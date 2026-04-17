import os
from dotenv import load_dotenv
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials

def check_db_explicit():
    load_dotenv()
    cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not cred_path:
        print("No cred path in .env")
        return

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    
    db = firestore.client()
    
    # List collections (standard way)
    collections = [c.id for c in db.collections()]
    print(f"Collections found: {collections}")
    
    for coll_name in ["acoesDividendos", "ativos"]:
        if coll_name in collections:
            docs = list(db.collection(coll_name).limit(5).stream())
            print(f"Collection '{coll_name}' has {len(docs)} sample docs.")
            for doc in docs:
                print(f"  - {doc.id}")

if __name__ == "__main__":
    check_db_explicit()
