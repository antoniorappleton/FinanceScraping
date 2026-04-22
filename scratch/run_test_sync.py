import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.getcwd())

from scraper.registry import SCRAPER_REGISTRY
from scraper.firebase_manager import firebase_manager
from scraper.transformer import clean_float, clean_row_for_firestore, normalize_ticker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_specific_test(tickers_to_test):
    load_dotenv()
    logger.info(f"Starting test sync for tickers: {tickers_to_test}")
    
    # Sources to try (prioritizing JustETF for these ETFs)
    sources_to_try = ["justetf", "yahoo", "ft_markets", "google_finance", "finviz"]
    
    for ticker_id in tickers_to_test:
        ticker = normalize_ticker(ticker_id)
        market_code = "EU" # Mostly European ETFs/Stocks in the list
        
        # Add special handling for specific tickers if needed
        if ticker_id in ["VWCE", "QDVE", "EXSA", "GRID"]:
            # These are ETFs, Yahoo often needs .DE or .AS
            pass
            
        success = False
        for source_name in sources_to_try:
            if source_name not in SCRAPER_REGISTRY: continue
            
            scraper = SCRAPER_REGISTRY[source_name]
            try:
                logger.info(f"[{ticker_id}] Fetching from {source_name}...")
                result = scraper.scrape_quote(ticker=ticker, market=market_code)
                metrics = result.get("metrics", {})
                
                price_str = (
                    metrics.get("valorStock") or
                    metrics.get("price") or
                    metrics.get("Price") or
                    metrics.get("Latest quote") or
                    metrics.get("NAV")
                )
                price_val = clean_float(price_str)
                
                if price_val and price_val > 0:
                    payload = {
                        "valorStock": price_val,
                        "priceChange_1d": clean_float(metrics.get("change_pct") or metrics.get("Change")),
                        "priceChange_1w": clean_float(metrics.get("priceChange_1w") or metrics.get("Perf Week")),
                        "priceChange_1m": clean_float(metrics.get("priceChange_1m") or metrics.get("Perf Month")),
                        "priceChange_1y": clean_float(metrics.get("priceChange_1y") or metrics.get("Perf Year")),
                        "yield": clean_float(metrics.get("yield") or metrics.get("Dividend Yield") or metrics.get("Dividend %")),
                        "pe": clean_float(metrics.get("pe") or metrics.get("PE Ratio (TTM)") or metrics.get("P/E")),
                        "roa": clean_float(metrics.get("roa") or metrics.get("ROA") or metrics.get("Return on Assets")),
                        "roe": clean_float(metrics.get("roe") or metrics.get("ROE") or metrics.get("Return on Equity")),
                        "rsi": clean_float(metrics.get("rsi") or metrics.get("RSI (14)")),
                        "sma50": clean_float(metrics.get("sma50") or metrics.get("SMA50")),
                        "sma200": clean_float(metrics.get("sma200") or metrics.get("SMA200")),
                        "marketCap": clean_float(metrics.get("Market Cap") or metrics.get("marketCap") or metrics.get("Fund size")),
                        "source_used": f"{source_name} (test_sync)",
                        "nome": result.get("title", {}).get("company", ticker),
                        "lastFullSync": datetime.now().isoformat(),
                    }
                    
                    # Add extra metrics
                    cleaned_metrics = clean_row_for_firestore(metrics)
                    for k, v in cleaned_metrics.items():
                        if k not in payload: payload[k] = v

                    if firebase_manager.update_market_data(ticker_id, payload):
                        logger.info(f"[{ticker_id}] SUCCESS: Updated with price {price_val} and SMAs {payload.get('sma50')}/{payload.get('sma200')}")
                        success = True
                        break
            except Exception as e:
                logger.error(f"[{ticker_id}] Error with {source_name}: {e}")
        
        if not success:
            logger.error(f"[{ticker_id}] FAILED to update after trying all sources.")

if __name__ == "__main__":
    tickers = ["VWCE", "QDVE", "EXSA", "NUKL", "GRID", "VVMX"]
    run_specific_test(tickers)
