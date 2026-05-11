from dotenv import load_dotenv
load_dotenv()

import os
from scraper.yahoo import YahooFinanceScraper
from scraper.firebase_manager import firebase_manager
from scraper.transformer import flatten_scrape_result, clean_row_for_firestore, normalize_ticker

def sync_holdings_for_ativos():
    print("Starting holdings sync for 'ativos' collection...")
    scraper = YahooFinanceScraper(pause_seconds=6.0) # Increased pause to avoid 429
    
    try:
        # 1. Get all documents from 'ativos'
        docs = firebase_manager.db.collection("ativos").stream()
        etfs_found = []
        
        for d in docs:
            data = d.to_dict()
            ticker_id = data.get("ticker")
            if not ticker_id:
                continue
            
            # Simple heuristic: if it has 'ETF' in name or we check via yfinance
            # But let's just try to scrape everything in 'ativos' that might be an ETF
            etfs_found.append(ticker_id)
            
        print(f"Found {len(etfs_found)} assets in 'ativos'. Checking for holdings...")
        
        for ticker_id in etfs_found:
            ticker = normalize_ticker(ticker_id)
            # Detect market (rough estimation)
            market = "EU" if ".DE" in ticker or ".LS" in ticker or "XETR_" in ticker_id else "US"
            
            print(f"Checking holdings for {ticker}...")
            try:
                result = scraper.scrape_quote(ticker, market)
                if result:
                    metrics = result.get("metrics", {})
                    if "holdings" in metrics:
                        print(f"  [SUCCESS] Found {len(metrics['holdings'])} holdings for {ticker}.")
                        # update_market_data already handles saving holdings if they are in the data
                        # but we need to pass the holdings to the data dict
                        clean_data = clean_row_for_firestore(flatten_scrape_result(result))
                        firebase_manager.update_market_data(ticker_id, clean_data)
                    else:
                        print(f"  [INFO] No holdings found for {ticker} (likely not an ETF or no data).")
                else:
                    print(f"  [ERROR] Failed to scrape {ticker}.")
            except Exception as e:
                print(f"  [ERROR] Error processing {ticker}: {e}")
                
    except Exception as e:
        print(f"Error during sync: {e}")

if __name__ == "__main__":
    sync_holdings_for_ativos()
