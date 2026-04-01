import os
import sys
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.getcwd())

from scraper.firebase_manager import firebase_manager
from scraper.registry import SCRAPER_REGISTRY
from scraper.transformer import clean_float, clean_row_for_firestore

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def repair_pt_tickers():
    docs = firebase_manager.db.collection("acoesDividendos").stream()
    pt_tickers = []
    for d in docs:
        data = d.to_dict()
        if data.get("mercado") == "Portugal":
            pt_tickers.append(data.get("ticker", d.id).upper())
            
    logger.info(f"Repairing {len(pt_tickers)} Portugal tickers...")
    scraper = SCRAPER_REGISTRY["yahoo"]
    
    for ticker in pt_tickers:
        logger.info(f"Targeting: {ticker}")
        try:
            # We use PT market
            result = scraper.scrape_quote(ticker=ticker, market="PT")
            metrics = result.get("metrics", {})
            
            payload = {
                "pe": clean_float(metrics.get("pe")),
                "ev_ebitda": clean_float(metrics.get("ev_ebitda")),
                "rsi": clean_float(metrics.get("rsi")),
                "roe": clean_float(metrics.get("roe")),
                "roa": clean_float(metrics.get("roa")),
                "roic": clean_float(metrics.get("roic")),
                "valorStock": clean_float(metrics.get("valorStock")),
                "lastFullSync": datetime.now().isoformat()
            }
            
            # Add other cleaned metrics
            cleaned = clean_row_for_firestore(metrics)
            for k, v in cleaned.items():
                if k not in payload and v is not None:
                    payload[k] = v
                    
            firebase_manager.update_market_data(ticker, payload)
            logger.info(f"SUCCESS: {ticker} updated.")
            
        except Exception as e:
            logger.error(f"FAILED: {ticker}: {e}")
            
        # Large delay to respect Yahoo
        time.sleep(15)

if __name__ == "__main__":
    repair_pt_tickers()
