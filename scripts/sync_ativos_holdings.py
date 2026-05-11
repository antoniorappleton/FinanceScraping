import os
import time
from dotenv import load_dotenv
load_dotenv()

from scraper.yahoo import YahooFinanceScraper
from scraper.justetf import JustETFScraper
from scraper.firebase_manager import firebase_manager
from scraper.transformer import flatten_scrape_result, clean_row_for_firestore, normalize_ticker

def sync_holdings_for_ativos():
    print("Starting holdings sync for 'ativos' collection...")
    yahoo_scraper = YahooFinanceScraper(pause_seconds=6.0)
    justetf_scraper = JustETFScraper(pause_seconds=4.0)
    
    try:
        # 1. Get all documents from 'ativos'
        # Filter for things that might be ETFs or have ISINs
        docs = firebase_manager.db.collection("ativos").stream()
        
        assets_to_check = []
        for d in docs:
            data = d.to_dict()
            ticker_id = data.get("ticker")
            isin = data.get("isin")
            name = data.get("nome", data.get("name", ""))
            
            if not ticker_id:
                continue
                
            assets_to_check.append({
                "id": ticker_id,
                "isin": isin,
                "name": name,
                "type": "ETF" if "ETF" in name.upper() else "UNKNOWN"
            })
            
        print(f"Found {len(assets_to_check)} assets in 'ativos'. Starting sync...")
        
        for asset in assets_to_check:
            ticker_id = asset["id"]
            isin = asset["isin"]
            is_etf = asset["type"] == "ETF" or isin is not None
            
            # Normalize for search
            clean_ticker = normalize_ticker(ticker_id)
            market = "EU" if ".DE" in clean_ticker or ".LS" in clean_ticker or "XETR_" in ticker_id else "US"
            
            print(f"Processing {ticker_id} (ISIN: {isin or 'N/A'})...")
            
            result = None
            
            # Step A: If it's likely an ETF, try JustETF first
            if is_etf or market == "EU":
                try:
                    search_query = isin if isin else clean_ticker
                    print(f"  [JustETF] Trying to scrape {search_query}...")
                    result = justetf_scraper.scrape_quote(search_query, market)
                    
                    if result and result.get("metrics", {}).get("holdings"):
                        print(f"  [SUCCESS] Found {len(result['metrics']['holdings'])} holdings on JustETF.")
                    else:
                        print(f"  [INFO] JustETF returned no holdings or failed.")
                        result = None
                except Exception as e:
                    print(f"  [JustETF] Error: {e}")
                    result = None

            # Step B: Fallback to Yahoo if JustETF failed or wasn't used
            if not result:
                try:
                    print(f"  [Yahoo] Trying to scrape {clean_ticker}...")
                    result = yahoo_scraper.scrape_quote(clean_ticker, market)
                    if result and result.get("metrics", {}).get("holdings"):
                        print(f"  [SUCCESS] Found {len(result['metrics']['holdings'])} holdings on Yahoo.")
                    else:
                        print(f"  [INFO] Yahoo returned no holdings.")
                except Exception as e:
                    print(f"  [Yahoo] Error: {e}")
                    result = None

            # Step C: Save result if found
            if result:
                clean_data = clean_row_for_firestore(flatten_scrape_result(result))
                # Ensure ISIN is saved if found
                if result.get("isin"):
                    clean_data["isin"] = result["isin"]
                
                firebase_manager.update_market_data(ticker_id, clean_data)
                print(f"  [DONE] Updated {ticker_id}")
            else:
                print(f"  [SKIPPED] No holdings data found for {ticker_id}")

            # Politeness delay
            time.sleep(5.0)
                
    except Exception as e:
        print(f"Error during sync: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    sync_holdings_for_ativos()
