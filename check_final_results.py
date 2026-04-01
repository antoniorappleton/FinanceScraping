
import os
from dotenv import load_dotenv
load_dotenv()
from scraper.firebase_manager import firebase_manager

def check_results():
    tickers = ["EXSA", "EUNN"]
    for t in tickers:
        doc = firebase_manager.db.collection("acoesDividendos").document(t).get()
        if doc.exists:
            d = doc.to_dict()
            print(f"Ticker: {t}")
            print(f"  Price (valorStock): {d.get('valorStock')}")
            print(f"  Source Used: {d.get('source_used')}")
            print(f"  Last Update: {d.get('ultimaAtu')}")
            print(f"  Market: {d.get('mercado')}")
        else:
            print(f"Ticker {t} NOT FOUND in Firestore.")

if __name__ == "__main__":
    check_results()
