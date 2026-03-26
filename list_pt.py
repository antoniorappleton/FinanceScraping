import os
import sys
from dotenv import load_dotenv

# Load .env first
load_dotenv()

# Add current directory to sys.path
sys.path.append(os.getcwd())

from scraper.firebase_manager import firebase_manager

def list_pt_data():
    if not firebase_manager.db:
        print("Firebase not initialized")
        return

    docs = firebase_manager.db.collection("acoesDividendos").stream()
    print("Listing Portugal tickers in Firestore:")
    for doc in docs:
        data = doc.to_dict()
        if data.get("mercado") == "Portugal":
            ticker = data.get("ticker", doc.id)
            print(f"- {ticker}")
            print(f"  PE: {data.get('pe')}")
            print(f"  EV/EBITDA: {data.get('ev_ebitda')}")
            print(f"  RSI: {data.get('rsi')}")
            print(f"  ROIC: {data.get('roic')}")

if __name__ == "__main__":
    list_pt_data()
