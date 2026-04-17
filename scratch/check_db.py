from scraper.firebase_manager import firebase_manager

def check_collections():
    if not firebase_manager.db:
        print("Firebase not initialized.")
        return
    
    collections = ["acoesDividendos", "ativos", "marketData"]
    for coll_name in collections:
        try:
            docs = firebase_manager.db.collection(coll_name).limit(5).get()
            print(f"Collection '{coll_name}': {len(docs)} docs found.")
            if docs:
                print(f"  Example ID: {docs[0].id}")
        except Exception as e:
            print(f"Error checking '{coll_name}': {e}")

if __name__ == "__main__":
    check_collections()
