import os
import sys
import logging
from dotenv import load_dotenv

# Load .env before any other imports that might use it
load_dotenv()

# Add current directory to sys.path
sys.path.append(os.getcwd())

from scraper.firebase_manager import firebase_manager
from scraper.registry import SCRAPER_REGISTRY
from scraper.transformer import clean_float, clean_row_for_firestore
import yfinance as yf

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_portugal_tickers():
    if not firebase_manager.db:
        logger.error("Firebase not initialized. Check your .env and service account JSON path.")
        return

    logger.info("Fetching tickers from 'acoesDividendos' collection...")
    docs = firebase_manager.db.collection("acoesDividendos").stream()
    
    pt_tickers = []
    for doc in docs:
        data = doc.to_dict()
        market = data.get("mercado", "")
        if market == "Portugal":
            pt_tickers.append((doc.id, data))
            
    if not pt_tickers:
        logger.warning("No Portugal tickers found.")
        return

    logger.info(f"Found {len(pt_tickers)} Portugal tickers to update.")

    scraper = SCRAPER_REGISTRY.get("yahoo")
    if not scraper:
        logger.error("Yahoo scraper not found in registry.")
        return

    for ticker, current_data in pt_tickers:
        logger.info(f"--- Processing {ticker} ---")
        
        try:
            # We know it's Portugal, so use "PT" market for normalization
            result = scraper.scrape_quote(ticker=ticker, market="PT")
            metrics = result.get("metrics", {})
            
            # Debug: what keys did we get?
            logger.info(f"Keys returned from scraper: {list(metrics.keys())}")
            
            # The user wants: ROIC, RSI, PE, EV/Ebithda
            # Let's see if we can find them or compute them
            
            # PE
            pe = metrics.get("info_trailingpe") or metrics.get("info_forwardpe") or metrics.get("pe")
            
            # EV/EBITDA
            ev_ebitda = metrics.get("info_enterprisetoebitda") or metrics.get("ev_ebitda")
            
            # ROIC (Return on Invested Capital) - often not in info
            # We might have ROA/ROE
            roa = metrics.get("info_returnonassets")
            roe = metrics.get("info_returnonequity")
            
            # RSI (needs calculation)
            rsi = calculate_rsi(ticker, market="PT")
            
            from datetime import datetime
            payload = {
                "pe": pe,
                "ev_ebitda": ev_ebitda,
                "roa": roa,
                "roe": roe,
                "rsi": rsi,
                "roic": metrics.get("info_returnoninvestedcapital"), # Try if it exists
                "valorStock": metrics.get("valorStock"),
                "source_used": f"special_pt_sync (yahoo)",
                "lastFullSync": f"{datetime.now().isoformat()}"
            }
            
            # Merge with other cleaned metrics
            cleaned = clean_row_for_firestore(metrics)
            for k, v in cleaned.items():
                if k not in payload and v is not None:
                    payload[k] = v
            
            logger.info(f"Updating {ticker} with payload: PE={pe}, EV/EBITDA={ev_ebitda}, RSI={rsi}")
            firebase_manager.update_market_data(ticker, payload)
            
        except Exception as e:
            logger.error(f"Error updating {ticker}: {e}")

def calculate_rsi(ticker, market="PT", period=14):
    """Simple RSI calculation using yfinance history."""
    try:
        from scraper.base import BaseScraper
        normalized = BaseScraper.normalize_ticker(ticker, market)
        stock = yf.Ticker(normalized)
        hist = stock.history(period="1mo")
        if len(hist) < period + 1:
            return None
        
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi.iloc[-1], 2)
    except Exception as e:
        logger.error(f"Error calculating RSI for {ticker}: {e}")
        return None

if __name__ == "__main__":
    update_portugal_tickers()
