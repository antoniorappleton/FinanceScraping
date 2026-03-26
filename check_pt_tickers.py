import os
from scraper.firebase_manager import firebase_manager
from dotenv import load_dotenv

load_dotenv()

def check_portugal_tickers():
    if not firebase_manager.db:
        print("Firebase not initialized")
        return

    docs = firebase_manager.db.collection("acoesDividendos").stream()
    pt_tickers = []
    others = []
    
    for doc in docs:
        data = doc.to_dict()
        ticker = data.get("ticker", doc.id)
        market = data.get("mercado", "Unknown")
        
        if market == "Portugal":
            pt_tickers.append((ticker, data))
        else:
            others.append((ticker, data))
            
    print(f"Found {len(pt_tickers)} Portugal tickers:")
    for ticker, data in pt_tickers:
        print(f"- {ticker}: ROIC={data.get('roic')}, RSI={data.get('rsi')}, PE={data.get('pe')}, EV/EBITDA={data.get('ev_ebitda')}")
        
    print(f"\nFound {len(others)} other tickers.")

if __name__ == "__main__":
    check_portugal_tickers()
