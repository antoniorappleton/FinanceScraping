import time
import os
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Import scrapers and manager
from scraper.registry import SCRAPER_REGISTRY
from scraper.firebase_manager import firebase_manager
from scraper.transformer import clean_float, clean_row_for_firestore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_automated_scrape(mode="full"):
    """
    Main logic for automated scraping:
    - Fast Mode: Updates only high-frequency data (Price, Change, Cap).
    - Full Mode: Updates all financial indicators.
    """
    # load_dotenv() # Already loaded at top Level
    
    logger.info(f"Starting automated scraping ({mode.upper()} sync)...")
    
    # 1. Get tickers from Firestore
    try:
        docs = firebase_manager.db.collection("acoesDividendos").stream()
        ticker_data = []
        for d in docs:
            data = d.to_dict()
            ticker = data.get("ticker", d.id).upper()
            market = data.get("mercado", "")
            ticker_data.append({"ticker": ticker, "market_name": market})
    except Exception as e:
        logger.error(f"Error fetching tickers: {e}")
        return

    if not ticker_data:
        logger.warning("No tickers found in 'acoesDividendos' collection or Firebase not initialized.")
        return

    # Sort: Portugal first
    ticker_data.sort(key=lambda x: x.get("market_name") != "Portugal")

    logger.info(f"Found {len(ticker_data)} tickers to process.")
    
    for item in ticker_data:
        ticker = item["ticker"]
        market_name = item["market_name"]
        # Detect market code
        market_code = "US" 
        if market_name == "Portugal" or "." in ticker:
            market_code = "PT"
            
        success = False
        # Try multiple scrapers in order
        sources_to_try = ["yahoo", "google_finance", "finviz"]
        
        # Avoid Finviz for PT/EU stocks to prevent US ticker data pollution
        if market_code != "US":
            sources_to_try = ["yahoo", "google_finance"]

        for source_name in sources_to_try:
            if source_name not in SCRAPER_REGISTRY:
                continue
                
            scraper = SCRAPER_REGISTRY[source_name]
            try:
                result = scraper.scrape_quote(ticker=ticker, market=market_code)
                metrics = result.get("metrics", {})
                method_used = result.get("method", "scrape")
                
                # Universal extraction attempt
                price_str = metrics.get("valorStock") or result.get("title", {}).get("price") or metrics.get("price")
                change_str = metrics.get("change_pct") or metrics.get("Change")
                market_cap_str = metrics.get("Market Cap") or metrics.get("marketCap")

                # Build Payload
                if mode == "fast":
                    payload = {
                        "valorStock": clean_float(price_str),
                        "priceChange_1d": clean_float(change_str),
                        "marketCap": clean_float(market_cap_str),
                        "source_used": f"{source_name} ({method_used})",
                        "method_used": method_used,
                        "nome": result.get("title", {}).get("company", ticker)
                    }
                else:
                    # Full Sync Indicators
                    payload = {
                        "valorStock": clean_float(price_str),
                        "priceChange_1d": clean_float(change_str),
                        "priceChange_1w": clean_float(metrics.get("priceChange_1w") or metrics.get("Perf Week")),
                        "priceChange_1y": clean_float(metrics.get("priceChange_1y") or metrics.get("Perf Year")),
                        "priceChange_1m": clean_float(metrics.get("priceChange_1m")),
                        "yield": clean_float(metrics.get("yield") or metrics.get("Dividend Yield")),
                        "pe": clean_float(metrics.get("pe") or metrics.get("PE Ratio (TTM)")),
                        "roa": clean_float(metrics.get("roa") or metrics.get("ROA")),
                        "roe": clean_float(metrics.get("roe") or metrics.get("ROE")),
                        "roi": clean_float(metrics.get("roi") or metrics.get("ROI")),
                        "rsi": clean_float(metrics.get("rsi")),
                        "roic": clean_float(metrics.get("roic")),
                        "ev_ebitda": clean_float(metrics.get("ev_ebitda") or metrics.get("EV/EBITDA")),
                        "marketCap": clean_float(market_cap_str),
                        "ebitda": clean_float(metrics.get("ebitda") or metrics.get("EBITDA")),
                        
                        "source_used": f"{source_name} ({method_used})",
                        "method_used": method_used,
                        "nome": result.get("title", {}).get("company", ticker),
                        "lastFullSync": datetime.now().isoformat()
                    }

                    # Add other cleaned metrics
                    cleaned_metrics = clean_row_for_firestore(metrics)
                    for k, v in cleaned_metrics.items():
                        if k not in payload:
                            payload[k] = v
                
                # 3. Update Firestore
                if firebase_manager.update_market_data(ticker, payload):
                    logger.info(f"{ticker} updated ({mode}) via {source_name}")
                    success = True
                    break # Success, move to next ticker
                
            except Exception as e:
                logger.error(f"Error scraping {ticker} with {source_name}: {e}")
                if "429" in str(e):
                    logger.warning("Rate limit hit. Sleeping longer...")
                    time.sleep(10)
                continue 
        
        if not success:
            logger.error(f"Failed to update {ticker} after trying all sources.")
        
        time.sleep(2)

    logger.info(f"Automated {mode} scraping session finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Scraper for Firestore")
    parser.add_argument("--mode", choices=["fast", "full"], default="full", help="Sync mode: 'fast' for price/cap, 'full' for all metrics.")
    args = parser.parse_args()
    
    run_automated_scrape(mode=args.mode)
