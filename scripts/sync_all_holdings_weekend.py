from dotenv import load_dotenv
load_dotenv()

import os
import time
import random
from scraper.yahoo import YahooFinanceScraper
from scraper.firebase_manager import firebase_manager
from scraper.transformer import flatten_scrape_result, clean_row_for_firestore, normalize_ticker

def sync_all_holdings():
    print("Starting WEEKEND holdings sync for ALL assets in 'acoesDividendos'...")
    scraper = YahooFinanceScraper(pause_seconds=5.0) # Longer pause for bulk sync
    
    try:
        # 1. Get all documents from 'acoesDividendos'
        docs = firebase_manager.db.collection("acoesDividendos").stream()
        tickers_found = []
        
        for d in docs:
            data = d.to_dict()
            ticker_id = data.get("ticker")
            if ticker_id:
                tickers_found.append(ticker_id)
            
        print(f"Found {len(tickers_found)} assets in 'acoesDividendos'. Processing...")
        
        # Shuffle to avoid hitting the same exchange/provider too rapidly
        random.shuffle(tickers_found)
        
        for ticker_id in tickers_found:
            ticker = normalize_ticker(ticker_id)
            # Detect market
            market = "EU" if ".DE" in ticker or ".LS" in ticker or "XETR_" in ticker_id else "US"
            
            print(f"Checking holdings for {ticker}...")
            try:
                result = scraper.scrape_quote(ticker, market)
                if result:
                    metrics = result.get("metrics", {})
                    if "holdings" in metrics:
                        print(f"  [SUCCESS] Found {len(metrics['holdings'])} holdings for {ticker}.")
                        clean_data = clean_row_for_firestore(flatten_scrape_result(result))
                        firebase_manager.update_market_data(ticker_id, clean_data)
                    else:
                        print(f"  [INFO] No holdings found for {ticker}.")
                else:
                    print(f"  [ERROR] Failed to scrape {ticker}.")
            except Exception as e:
                print(f"  [ERROR] Error processing {ticker}: {e}")
                if "429" in str(e):
                    print("  [429] Rate limit hit. Sleeping for 2 minutes...")
                    time.sleep(120)
            
            # Additional random delay between 5 and 10 seconds
            time.sleep(random.uniform(5, 10))
                
    except Exception as e:
        print(f"Error during bulk sync: {e}")

if __name__ == "__main__":
    sync_all_holdings()
