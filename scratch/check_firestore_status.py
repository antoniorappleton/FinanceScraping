from dotenv import load_dotenv
import os
import sys

# Load dotenv at the very beginning
load_dotenv(os.path.join(os.getcwd(), ".env"))

# Add project root to sys.path
sys.path.append(os.getcwd())

from scraper.firebase_manager import firebase_manager

def check_tickers(tickers_list):
    db = firebase_manager.db
    if not db:
        print("Firebase not initialized.")
        return

    print(f"{'Ticker':<10} | {'Price':<10} | {'SMA50':<10} | {'SMA200':<10} | {'Last Sync':<20}")
    print("-" * 65)

    for ticker in tickers_list:
        doc = db.collection("acoesDividendos").document(ticker).get()
        if doc.exists:
            data = doc.to_dict()
            price = data.get("valorStock", "N/A")
            sma50 = data.get("sma50", "N/A")
            sma200 = data.get("sma200", "N/A")
            last_sync = data.get("lastFullSync", "Never")
            if isinstance(last_sync, str) and "T" in last_sync:
                last_sync = last_sync.split("T")[0] + " " + last_sync.split("T")[1][:5]
            
            print(f"{ticker:<10} | {price:<10} | {sma50:<10} | {sma200:<10} | {last_sync:<20}")
        else:
            print(f"{ticker:<10} | NOT FOUND")

if __name__ == "__main__":
    test_tickers = ["VWCE", "QDVE", "EXSA", "NUKL", "GRID", "VVMX"]
    check_tickers(test_tickers)
