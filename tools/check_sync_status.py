import os
from datetime import datetime, timezone
import sys
from dotenv import load_dotenv

# Add the parent directory to sys.path to allow importing from 'scraper'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from scraper.firebase_manager import firebase_manager

def check_status():
    print(f"Checking status at {datetime.now(timezone.utc)}")
    docs = firebase_manager.db.collection("acoesDividendos").stream()
    
    total = 0
    updated = 0
    failed = []
    
    now = datetime.now(timezone.utc)
    
    for d in docs:
        total += 1
        data = d.to_dict()
        ticker = d.id
        updated_at = data.get("updatedAt")
        
        if updated_at:
            # Firestore timestamp to datetime
            if isinstance(updated_at, datetime):
                dt = updated_at
            else:
                # If it's a string or other, though usually it's a datetime object from SDK
                dt = datetime.fromisoformat(str(updated_at).replace('Z', '+00:00'))
            
            # Check if updated in the last 1 hour
            diff = now - dt
            if diff.total_seconds() < 3600:
                updated += 1
            else:
                failed.append(f"{ticker} (Last update: {updated_at})")
        else:
            failed.append(f"{ticker} (Never updated)")
            
    print(f"\nSummary:")
    print(f"Total Tickers: {total}")
    print(f"Recently Updated: {updated}")
    print(f"Pending/Failed: {len(failed)}")
    
    if failed:
        print("\nFailed Tickers:")
        for f in failed:
            print(f"- {f}")

if __name__ == "__main__":
    check_status()
