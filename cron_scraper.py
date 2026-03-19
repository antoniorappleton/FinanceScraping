import time
import os
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Import scrapers and manager
from scraper.registry import SCRAPER_REGISTRY
from scraper.firebase_manager import firebase_manager

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
    load_dotenv()
    
    logger.info(f"🚀 Starting automated scraping ({mode.upper()} sync)...")
    
    # 1. Get tickers from Firestore
    tickers = firebase_manager.get_all_tickers()
    if not tickers:
        logger.warning("⚠️ No tickers found in 'acoesDividendos' collection or Firebase not initialized.")
        return

    logger.info(f"📋 Found {len(tickers)} tickers to process: {tickers}")
    
    # 2. Iterate and Scrape
    # Pre-select scrapers (Preference order)
    # Defaulting to yahoo for US/General, or euronext for EU/PT if needed.
    # For simplicity, we'll try Yahoo first, then Google Finance.
    
    for ticker in tickers:
        logger.info(f"🔍 Processing: {ticker}")
        
        success = False
        # Try multiple scrapers if one fails
        for source_name in ["yahoo", "google_finance", "finviz"]:
            if source_name not in SCRAPER_REGISTRY:
                continue
                
            scraper = SCRAPER_REGISTRY[source_name]
            try:
                # Attempt to scrape (assuming Americano/US as default, or detecting market from ticker)
                # For this automation, we assume US or generic market for simplicity, 
                # or we could extend the 'tickers' collection to include market.
                market = "US" 
                if "." in ticker: # e.g. EDP.LS or similar
                    market = "PT"
                
                result = scraper.scrape_quote(ticker=ticker, market=market)
                metrics = result.get("metrics", {})
                
                # Universal extraction attempt
                price_str = result.get("title", {}).get("price") or metrics.get("price") or metrics.get("Price")
                change_str = metrics.get("change_pct") or metrics.get("Change") or metrics.get("Net Change")
                market_cap_str = metrics.get("Market Cap") or metrics.get("Market Cap (intraday)") or metrics.get("MarketCap")

                # Clean values (Convert to numbers)
                def clean_float(val):
                    if not val or not isinstance(val, (str, float, int)): return 0
                    if isinstance(val, (float, int)): return float(val)
                    cleaned = val.replace("$", "").replace("%", "").replace(",", "").replace("(", "").replace(")", "").strip()
                    multiplier = 1
                    if cleaned.endswith("B"):
                        multiplier = 1_000_000_000
                        cleaned = cleaned[:-1]
                    elif cleaned.endswith("M"):
                        multiplier = 1_000_000
                        cleaned = cleaned[:-1]
                    elif cleaned.endswith("T"):
                        multiplier = 1_000_000_000_000
                        cleaned = cleaned[:-1]
                    try:
                        return float(cleaned) * multiplier
                    except:
                        return 0

                # Build Payload based on mode
                if mode == "fast":
                    payload = {
                        "valorStock": clean_float(price_str),
                        "priceChange_1d": clean_float(change_str) / 100 if "%" in str(change_str) else clean_float(change_str),
                        "marketCap": clean_float(market_cap_str),
                        "source_used": source_name,
                        "nome": result.get("title", {}).get("company", ticker)
                    }
                else:
                    # Full Sync Indicators
                    yield_str = metrics.get("Forward Dividend & Yield") or metrics.get("Dividend Yield") or metrics.get("Yield") or metrics.get("Dividend %")
                    pe_str = metrics.get("PE Ratio (TTM)") or metrics.get("P/E Ratio") or metrics.get("PE") or metrics.get("pe")
                    ebitda_str = metrics.get("EBITDA") or metrics.get("ebitda")
                    perf_1w_str = metrics.get("Perf Week")
                    perf_1y_str = metrics.get("Perf Year")
                    roa_str = metrics.get("ROA")
                    roe_str = metrics.get("ROE")
                    roi_str = metrics.get("ROI")
                    dividend_val_str = metrics.get("Dividend")

                    # Initialize payload with fixed/cleaned fields
                    payload = {
                        "valorStock": clean_float(price_str),
                        "priceChange_1d": clean_float(change_str) / 100 if "%" in str(change_str) else clean_float(change_str),
                        "priceChange_1w": clean_float(perf_1w_str) / 100 if "%" in str(perf_1w_str) else clean_float(perf_1w_str),
                        "priceChange_1y": clean_float(perf_1y_str) / 100 if "%" in str(perf_1y_str) else clean_float(perf_1y_str),
                        "yield": clean_float(yield_str) / 100 if "%" in str(yield_str) else clean_float(yield_str),
                        "dividendValue": clean_float(dividend_val_str),
                        "pe": clean_float(pe_str),
                        "roa": clean_float(roa_str) / 100 if "%" in str(roa_str) else clean_float(roa_str),
                        "roe": clean_float(roe_str) / 100 if "%" in str(roe_str) else clean_float(roe_str),
                        "roi": clean_float(roi_str) / 100 if "%" in str(roi_str) else clean_float(roi_str),
                        "marketCap": clean_float(market_cap_str),
                        "ebitda": clean_float(ebitda_str),
                        "source_used": source_name,
                        "nome": result.get("title", {}).get("company", ticker),
                        "lastFullSync": datetime.now().isoformat()
                    }

                    # Add ALL other metrics from the scraper
                    # We map them to Firestore-friendly keys if they contain spaces or special chars
                    for k, v in metrics.items():
                        # Create a clean key (replace spaces with _, remove special chars)
                        clean_key = k.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "").replace("%", "pct").replace("-", "_")
                        
                        # Avoid overwriting already processed specialized fields
                        if clean_key not in payload:
                            # Try to clean if it looks like a number/percentage
                            if isinstance(v, str) and (re.search(r'\d', v) or v == "-"):
                                if "%" in v:
                                    payload[clean_key] = clean_float(v) / 100
                                else:
                                    payload[clean_key] = clean_float(v)
                            else:
                                payload[clean_key] = v
                
                # 3. Update Firestore
                logger.info(f"📤 Sending {len(payload)} fields to Firestore for {ticker}: {list(payload.keys())}")
                if firebase_manager.update_market_data(ticker, payload):
                    logger.info(f"✅ {ticker} updated ({mode}) via {source_name}")
                    success = True
                    break # Success, move to next ticker
                
            except Exception as e:
                logger.error(f"❌ Error scraping {ticker} with {source_name}: {e}")
                continue # Try next scraper
        
        if not success:
            logger.error(f"🔴 Failed to update {ticker} after trying all sources.")
        
        # Delay to avoid blocking
        time.sleep(2)

    logger.info(f"🏁 Automated {mode} scraping session finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Scraper for Firestore")
    parser.add_argument("--mode", choices=["fast", "full"], default="full", help="Sync mode: 'fast' for price/cap, 'full' for all metrics.")
    args = parser.parse_args()
    
    run_automated_scrape(mode=args.mode)
