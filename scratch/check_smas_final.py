import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

def check_smas_state():
    load_dotenv()
    cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not cred_path:
        print("No cred path")
        return

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    
    # Check a few popular tickers
    tickers = ["AAPL", "MSFT", "VWCE", "VUSA", "COR.LS", "EDP.LS"]
    print(f"{'Ticker':<10} | {'SMA50':<10} | {'SMA200':<10} | {'Last Full Sync'}")
    print("-" * 60)
    
    for t in tickers:
        doc = db.collection("acoesDividendos").document(t).get()
        if doc.exists:
            data = doc.to_dict()
            s50 = data.get("sma50", "N/A")
            s200 = data.get("sma200", "N/A")
            last = data.get("lastFullSync", "Never")
            print(f"{t:<10} | {str(s50):<10} | {str(s200):<10} | {last}")
        else:
            print(f"{t:<10} | Not found")

if __name__ == "__main__":
    check_smas_state()
