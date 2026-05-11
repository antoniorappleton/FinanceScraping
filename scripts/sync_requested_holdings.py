from dotenv import load_dotenv
load_dotenv()

import os
from scraper.justetf import JustETFScraper
from scraper.firebase_manager import firebase_manager
from scraper.transformer import flatten_scrape_result, clean_row_for_firestore

def sync_specific_etfs(tickers):
    print(f"Syncing holdings for specific ETFs: {tickers}")
    scraper = JustETFScraper()
    
    for ticker in tickers:
        print(f"Processing {ticker}...")
        try:
            result = scraper.scrape_quote(ticker, "EU")
            if result:
                metrics = result.get("metrics", {})
                if "holdings" in metrics:
                    print(f"  [SUCCESS] Found {len(metrics['holdings'])} holdings for {ticker}.")
                    # Use update_market_data which now handles holdings saving
                    clean_data = clean_row_for_firestore(flatten_scrape_result(result))
                    firebase_manager.update_market_data(ticker, clean_data)
                else:
                    print(f"  [INFO] No holdings found for {ticker} on JustETF.")
            else:
                print(f"  [ERROR] Failed to scrape {ticker}.")
        except Exception as e:
            print(f"  [ERROR] Error processing {ticker}: {e}")

if __name__ == "__main__":
    target_tickers = ["IS3N", "2B76", "QUTM", "JEDI", "XDWF", "QDVE", "NUKL"]
    sync_specific_etfs(target_tickers)
