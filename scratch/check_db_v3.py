import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

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
    
    # List all collections
    colls = db.collections()
    coll_ids = [c.id for c in colls]
    print(f"Collections found: {coll_ids}")
    
    for coll_name in ["acoesDividendos", "ativos", "marketData"]:
        if coll_name in coll_ids:
            docs = list(db.collection(coll_name).limit(5).stream())
            print(f"Collection '{coll_name}' has {len(docs)} sample docs.")
            for d in docs:
                print(f"  - {d.id} (fields: {list(d.to_dict().keys())})")

if __name__ == "__main__":
    check_db_explicit()
