import os
import sys
from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.getcwd())
from scraper.registry import SCRAPER_REGISTRY
scraper = SCRAPER_REGISTRY["yahoo"]
ticker = "ELI:JMT"
result = scraper.scrape_quote(ticker=ticker, market="PT")
print(f"Ticker: {ticker}")
print(f"Ticker Used: {result['ticker_used']}")
print(f"PE: {result['metrics'].get('pe')}")
print(f"RSI: {result['metrics'].get('rsi')}")
print(f"EV/EBITDA: {result['metrics'].get('ev_ebitda')}")
