import os
from dotenv import load_dotenv
load_dotenv()
from scraper.firebase_manager import firebase_manager

def get_doc():
    doc = firebase_manager.db.collection('acoesDividendos').document('XETR_VVMX').get()
    if doc.exists:
        print(doc.to_dict())
    else:
        print("Document not found")

if __name__ == "__main__":
    get_doc()
