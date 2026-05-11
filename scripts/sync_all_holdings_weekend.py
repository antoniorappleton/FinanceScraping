import os
import time
import random
from dotenv import load_dotenv
load_dotenv()

from scraper.yahoo import YahooFinanceScraper
from scraper.justetf import JustETFScraper
from scraper.firebase_manager import firebase_manager
from scraper.transformer import flatten_scrape_result, clean_row_for_firestore, normalize_ticker

def sync_all_holdings():
    print("Starting WEEKEND holdings sync for ALL assets in 'acoesDividendos'...")
    yahoo_scraper = YahooFinanceScraper(pause_seconds=5.0)
    justetf_scraper = JustETFScraper(pause_seconds=4.0)
    
    try:
        # 1. Get all documents from 'acoesDividendos'
        docs = firebase_manager.db.collection("acoesDividendos").stream()
        assets_found = []
        
        for d in docs:
            data = d.to_dict()
            ticker_id = data.get("ticker")
            isin = data.get("isin")
            name = data.get("company", "")
            
            if ticker_id:
                assets_found.append({
                    "id": ticker_id,
                    "isin": isin,
                    "name": name
                })
            
        print(f"Found {len(assets_found)} assets in 'acoesDividendos'. Processing...")
        
        # Shuffle to avoid hitting the same exchange/provider too rapidly
        random.shuffle(assets_found)
        
        for asset in assets_found:
            ticker_id = asset["id"]
            isin = asset["isin"]
            clean_ticker = normalize_ticker(ticker_id)
            market = "EU" if ".DE" in clean_ticker or ".LS" in clean_ticker or "XETR_" in ticker_id else "US"
            
            print(f"Checking holdings for {ticker_id}...")
            
            result = None
            
            # Step A: Try JustETF for ETFs or European assets
            is_etf = "ETF" in asset["name"].upper() or isin is not None
            if is_etf or market == "EU":
                try:
                    search_query = isin if isin else clean_ticker
                    result = justetf_scraper.scrape_quote(search_query, market)
                    if result and result.get("metrics", {}).get("holdings"):
                        print(f"  [JustETF] SUCCESS: Found {len(result['metrics']['holdings'])} holdings.")
                    else:
                        result = None
                except:
                    result = None

            # Step B: Fallback to Yahoo
            if not result:
                try:
                    result = yahoo_scraper.scrape_quote(clean_ticker, market)
                    if result and result.get("metrics", {}).get("holdings"):
                        print(f"  [Yahoo] SUCCESS: Found {len(result['metrics']['holdings'])} holdings.")
                    else:
                        print(f"  [INFO] No holdings found.")
                except Exception as e:
                    print(f"  [ERROR] Yahoo error: {e}")
            
            # Step C: Save
            if result:
                clean_data = clean_row_for_firestore(flatten_scrape_result(result))
                if result.get("isin"): clean_data["isin"] = result["isin"]
                firebase_manager.update_market_data(ticker_id, clean_data)
            
            # Additional random delay
            time.sleep(random.uniform(5, 8))
                
    except Exception as e:
        print(f"Error during bulk sync: {e}")

if __name__ == "__main__":
    sync_all_holdings()
