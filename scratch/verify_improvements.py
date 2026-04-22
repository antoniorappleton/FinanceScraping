import os
import sys
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.getcwd())

from scraper.yahoo import YahooFinanceScraper

def test_sma_fallback():
    load_dotenv()
    scraper = YahooFinanceScraper()
    
    # BCP.LS is a good candidate for possible missing SMAs in 'info'
    ticker = "BCP.LS"
    print(f"Testing scraper for {ticker}...")
    
    try:
        result = scraper.scrape_quote(ticker, "PT")
        metrics = result.get("metrics", {})
        
        print("\n--- RESULTS ---")
        print(f"Symbol: {result.get('ticker_used')}")
        print(f"Company: {result.get('title', {}).get('company')}")
        print(f"Price: {metrics.get('valorStock')}")
        print(f"SMA50: {metrics.get('sma50')}")
        print(f"SMA200: {metrics.get('sma200')}")
        print(f"RSI: {metrics.get('rsi')}")
        
        if metrics.get('sma50') and metrics.get('sma200'):
            print("\n✅ SUCCESS: SMAs are present.")
        else:
            print("\n❌ FAILURE: SMAs are missing.")
            
    except Exception as e:
        print(f"Error during test: {e}")

if __name__ == "__main__":
    test_sma_fallback()
