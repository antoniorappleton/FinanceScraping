from scraper.registry import SCRAPER_REGISTRY
import json

def test_smas():
    ticker = "AAPL"
    market = "US"
    
    # Try Yahoo
    print("--- YAHOO ---")
    yahoo = SCRAPER_REGISTRY["yahoo"]
    res_y = yahoo.scrape_quote(ticker=ticker, market=market)
    metrics_y = res_y.get("metrics", {})
    print(f"Price: {res_y.get('metrics', {}).get('valorStock')}")
    print(f"SMA50: {metrics_y.get('sma50')}")
    print(f"SMA200: {metrics_y.get('sma200')}")

    # Try Finviz
    print("\n--- FINVIZ ---")
    finviz = SCRAPER_REGISTRY["finviz"]
    res_f = finviz.scrape_quote(ticker=ticker, market=market)
    metrics_f = res_f.get("metrics", {})
    print(f"SMA50: {metrics_f.get('SMA50')}")
    print(f"SMA200: {metrics_f.get('SMA200')}")

if __name__ == "__main__":
    test_smas()
