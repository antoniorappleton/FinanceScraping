
import os
from dotenv import load_dotenv
load_dotenv()
from scraper.registry import SCRAPER_REGISTRY

def debug_eunn():
    s = SCRAPER_REGISTRY['ft_markets']
    ticker = "EUNN"
    market = "EU"
    
    print(f"Scraping {ticker} ({market}) with FT Markets...")
    try:
        r = s.scrape_quote(ticker, market)
        print(f"URL Used: {r.get('url')}")
        print(f"Price found: {r['metrics'].get('price')}")
        print(f"Metrics: {r['metrics']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_eunn()
