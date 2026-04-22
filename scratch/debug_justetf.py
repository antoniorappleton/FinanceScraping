from dotenv import load_dotenv
import os
import sys
import json

# Load dotenv
load_dotenv(os.path.join(os.getcwd(), ".env"))
sys.path.append(os.getcwd())

from scraper.justetf import JustETFScraper

def debug_justetf():
    scraper = JustETFScraper()
    ticker = "VWCE"
    print(f"Debugging JustETF for {ticker}...")
    
    try:
        result = scraper.scrape_quote(ticker, "EU")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_justetf()
