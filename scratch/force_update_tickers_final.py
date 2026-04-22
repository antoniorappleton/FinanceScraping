from dotenv import load_dotenv
import os
import sys
import time
import logging
from datetime import datetime

# Load dotenv at the very beginning
load_dotenv(os.path.join(os.getcwd(), ".env"))

# Add project root to sys.path
sys.path.append(os.getcwd())

from scraper.registry import SCRAPER_REGISTRY
from scraper.firebase_manager import firebase_manager
from scraper.transformer import clean_float, clean_row_for_firestore
from scraper.base import BaseScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def force_update(tickers_list):
    logger.info(f"Iniciando atualização forçada FINAL para: {tickers_list}")
    
    for ticker_id in tickers_list:
        logger.info(f"--- Processando: {ticker_id} ---")
        
        final_payload = {}
        
        # 1. Obter dados base (JustETF)
        try:
            logger.info(f"[{ticker_id}] Tentando JustETF...")
            jetf_result = SCRAPER_REGISTRY["justetf"].scrape_quote(ticker=ticker_id, market="EU")
            jetf_metrics = jetf_result.get("metrics", {})
            
            price_val = clean_float(jetf_metrics.get("valorStock") or jetf_metrics.get("price"))
            # Se vier preço irreal (como o '2' de antes), ignorar
            if price_val > 5: 
                final_payload.update({
                    "valorStock": price_val,
                    "marketCap": clean_float(jetf_metrics.get("Fund size") or jetf_metrics.get("marketCap")),
                    "yield": clean_float(jetf_metrics.get("Dividend Yield") or jetf_metrics.get("yield")),
                    "nome": jetf_result.get("title", {}).get("company", ticker_id),
                })
                logger.info(f"[{ticker_id}] JustETF: Preço {price_val} obtido.")
            else:
                logger.warning(f"[{ticker_id}] JustETF: Preço ignorado por parecer inválido: {price_val}")
        except Exception as e:
            logger.warning(f"[{ticker_id}] Erro JustETF: {e}")

        # Pausa para não sobrecarregar
        time.sleep(5)

        # 2. Obter SMA e RSI (Yahoo Finance)
        try:
            logger.info(f"[{ticker_id}] Tentando Yahoo Finance...")
            y_ticker = BaseScraper.normalize_ticker(ticker_id, "EU") 
            yf_result = SCRAPER_REGISTRY["yahoo"].scrape_quote(ticker=y_ticker, market="EU")
            yf_metrics = yf_result.get("metrics", {})
            
            yf_price = clean_float(yf_metrics.get("valorStock"))
            
            # Incorporar os SMAs e RSI calculados ou obtidos
            final_payload.update({
                "sma50": clean_float(yf_metrics.get("sma50")),
                "sma200": clean_float(yf_metrics.get("sma200")),
                "rsi": clean_float(yf_metrics.get("rsi")),
                "priceChange_1d": clean_float(yf_metrics.get("priceChange_1d")),
                "priceChange_1w": clean_float(yf_metrics.get("priceChange_1w")),
                "priceChange_1m": clean_float(yf_metrics.get("priceChange_1m")),
                "priceChange_1y": clean_float(yf_metrics.get("priceChange_1y")),
            })
            
            # Preferir o preço do Yahoo se disponível (mais preciso para ETFs em EUR)
            if yf_price > 0:
                final_payload["valorStock"] = yf_price
                final_payload["nome"] = yf_result.get("title", {}).get("company", ticker_id)
            
            logger.info(f"[{ticker_id}] Yahoo: Dados técnicos processados. SMA50={final_payload.get('sma50')}")
            
        except Exception as e:
            logger.warning(f"[{ticker_id}] Erro Yahoo: {e}")

        # 3. Guardar se tivermos pelo menos o preço
        if final_payload.get("valorStock"):
            final_payload["lastFullSync"] = datetime.now().isoformat()
            final_payload["source_used"] = "Mixed (Force)"
            
            if firebase_manager.update_market_data(ticker_id, final_payload):
                logger.info(f"[{ticker_id}] SUCESSO: Atualizado no Firestore.")
            else:
                logger.error(f"[{ticker_id}] ERRO: Falha no Firestore.")
        else:
            logger.error(f"[{ticker_id}] FALHA: Sem preço.")

        # Pausa LONGA entre tickers
        logger.info("Aguardando 30 segundos...")
        time.sleep(30)

if __name__ == "__main__":
    test_tickers = ["VWCE", "QDVE", "EXSA", "NUKL", "GRID", "VVMX"]
    force_update(test_tickers)
