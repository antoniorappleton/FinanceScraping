import os
import sys
import time
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.getcwd())

from scraper.yahoo import YahooFinanceScraper

def test_single_ticker(ticker_id):
    load_dotenv()
    scraper = YahooFinanceScraper()
    
    print(f"\n--- Testing Ticker: {ticker_id} ---")
    
    # Try multiple times if 429
    for attempt in range(3):
        try:
            result = scraper.scrape_quote(ticker_id, "EU")
            metrics = result.get("metrics", {})
            
            if metrics.get('valorStock'):
                print(f"Success on attempt {attempt+1}")
                print(f"Company: {result.get('title', {}).get('company')}")
                print(f"Price: {metrics.get('valorStock')}")
                print(f"SMA50: {metrics.get('sma50')}")
                print(f"SMA200: {metrics.get('sma200')}")
                print(f"RSI: {metrics.get('rsi')}")
                return True
            else:
                print(f"Attempt {attempt+1}: No price found.")
        except Exception as e:
            print(f"Attempt {attempt+1} error: {e}")
        
        if attempt < 2:
            print("Waiting 15s to retry...")
            time.sleep(15)
    
    return False

if __name__ == "__main__":
    # Test QDVE as it's a popular one and often in the database
    test_single_ticker("QDVE")
