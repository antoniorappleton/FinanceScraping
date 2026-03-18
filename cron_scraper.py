import time
import os
import logging
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

def run_automated_scrape():
    """
    Main logic for daily automated scraping:
    1. Read tickers from Firestore
    2. Scrape data for each ticker
    3. Update Firestore marketData
    """
    load_dotenv()
    
    logger.info("🚀 Starting automated scraping session...")
    
    # 1. Get tickers from Firestore
    tickers = firebase_manager.get_all_tickers()
    if not tickers:
        logger.warning("⚠️ No tickers found in 'tickers' collection or Firebase not initialized.")
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
                
                # Transform to target schema
                # price, change, dividendYield
                price_val = 0
                change_val = 0
                yield_val = 0
                
                # Logic to extract values from different scraper outputs
                if source_name == "yahoo":
                    price_str = metrics.get("price", "0")
                    # Yahoo metrics are in a nested dict 'metrics'
                    # Actually scraper/yahoo.py returns them in 'metrics'
                    # Let's check yahoo scraper output structure
                    pass # will refine below

                # Universal extraction attempt
                price_str = result.get("title", {}).get("price") or metrics.get("price") or metrics.get("Price")
                change_str = metrics.get("change_pct") or metrics.get("Change") or metrics.get("Net Change")
                yield_str = metrics.get("Forward Dividend & Yield") or metrics.get("Dividend Yield") or metrics.get("Yield") or metrics.get("Dividend %")

                # Clean values (Convert to numbers)
                def clean_float(val):
                    if not val or not isinstance(val, (str, float, int)): return 0
                    if isinstance(val, (float, int)): return float(val)
                    # Remove currency symbols, commas, percent signs
                    cleaned = val.replace("$", "").replace("%", "").replace(",", "").replace("(", "").replace(")", "").strip()
                    try:
                        return float(cleaned)
                    except:
                        return 0

                payload = {
                    "price": clean_float(price_str),
                    "change": clean_float(change_str),
                    "dividendYield": clean_float(yield_str),
                    "source_used": source_name,
                    "company_name": result.get("title", {}).get("company", ticker)
                }
                
                # 3. Update Firestore
                if firebase_manager.update_market_data(ticker, payload):
                    logger.info(f"✅ {ticker} updated via {source_name}")
                    success = True
                    break # Success, move to next ticker
                
            except Exception as e:
                logger.error(f"❌ Error scraping {ticker} with {source_name}: {e}")
                continue # Try next scraper
        
        if not success:
            logger.error(f"🔴 Failed to update {ticker} after trying all sources.")
        
        # Delay to avoid blocking
        time.sleep(2)

    logger.info("🏁 Automated scraping session finished.")

if __name__ == "__main__":
    run_automated_scrape()
