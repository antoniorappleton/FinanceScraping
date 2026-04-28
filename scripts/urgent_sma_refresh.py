import os
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# Carregar variaveis de ambiente
load_dotenv()

from scraper.yahoo import YahooFinanceScraper
from scraper.firebase_manager import firebase_manager
from scraper.transformer import clean_float

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PRIORITY_TICKERS = ['VWCE', 'GRID', 'NUKL', 'QDVE', 'IS3N', 'VVMX']

def process_ticker(ticker_id, yahoo_scraper, finviz_scraper):
    # Obter dados basicos do ticker em acoesDividendos para saber o mercado
    doc_ref = firebase_manager.db.collection("acoesDividendos").document(ticker_id).get()
    market = "US"
    if doc_ref.exists:
        market = doc_ref.to_dict().get("mercado", "US")
    
    # Mapeamento simples de mercado para o scraper
    market_code = "US"
    m_lower = (market or "US").lower()
    if "portugal" in m_lower or ".ls" in ticker_id.lower():
        market_code = "PT"
    elif any(x in m_lower for x in ["euronext", "germany", "xetra", "europe", "eu"]):
        market_code = "EU"
    elif "brazil" in m_lower or "brasil" in m_lower or ".sa" in ticker_id.lower():
        market_code = "BR"

    # Detetar se parece ser um ETF europeu mal classificado
    etf_prefixes = ["QD", "EX", "IS", "VVM", "EUN", "2B", "VW", "IW", "EM", "MEU", "LYX", "AMU", "NU", "IU", "IE", "GRID"]
    if market_code == "US" and any(ticker_id.startswith(p) for p in etf_prefixes):
        logger.info(f"  ETF Ticker {ticker_id} parece ser um ETF Europeu. Tentando mercado EU...")
        market_code = "EU"

    logger.info(f"Atualizando {ticker_id} (Mercado: {market_code})...")
    
    try:
        # 1. Tentar Yahoo
        result = yahoo_scraper.scrape_quote(ticker_id, market_code)
        metrics = result.get("metrics", {})
        
        # 2. Se Yahoo falhar nos SMAs e for US, tentar Finviz
        if market_code == "US" and not metrics.get("sma50") and finviz_scraper:
            logger.info(f"  Yahoo falhou nos SMAs. Tentando Finviz para {ticker_id}...")
            try:
                fv_result = finviz_scraper.scrape_quote(ticker_id, market_code)
                metrics.update(fv_result.get("metrics", {}))
            except:
                pass

        if metrics.get("sma50") or metrics.get("valorStock"):
            payload = {
                "sma20": clean_float(metrics.get("sma20")),
                "sma50": clean_float(metrics.get("sma50")),
                "sma100": clean_float(metrics.get("sma100")),
                "sma200": clean_float(metrics.get("sma200")),
                "sma_vol20": clean_float(metrics.get("sma_vol20")),
                "above_sma50": metrics.get("above_sma50"),
                "above_sma200": metrics.get("above_sma200"),
                "golden_cross": metrics.get("golden_cross"),
                "rsi": clean_float(metrics.get("rsi")),
                "valorStock": clean_float(metrics.get("valorStock")),
                "lastSmaUpdate": datetime.now().isoformat()
            }
            
            # Calculo manual se necessario
            price = payload["valorStock"]
            if price and payload["sma50"] and payload["above_sma50"] is None:
                payload["above_sma50"] = price > payload["sma50"]
            if price and payload["sma200"] and payload["above_sma200"] is None:
                payload["above_sma200"] = price > payload["sma200"]
            if payload["sma50"] and payload["sma200"] and payload["golden_cross"] is None:
                payload["golden_cross"] = payload["sma50"] > payload["sma200"]

            # Remover None
            payload = {k: v for k, v in payload.items() if v is not None}
            
            if firebase_manager.update_market_data(ticker_id, payload):
                logger.info(f"  Success {ticker_id} atualizado (SMA50: {payload.get('sma50')}).")
                return True
            else:
                return False
        else:
            logger.warning(f"  Warning Sem dados suficientes para {ticker_id}")
            return False
            
    except Exception as e:
        logger.error(f"  Error Erro ao processar {ticker_id}: {e}")
        return False

def refresh_smas_prioritized():
    logger.info("Iniciando atualizacao PRIORITRIA de SMAs e Indicadores...")
    
    try:
        ativos_docs = firebase_manager.db.collection("ativos").stream()
        ticker_list = []
        seen = set()
        for d in ativos_docs:
            t = d.to_dict().get("ticker")
            if t and t not in seen:
                ticker_list.append(t.upper())
                seen.add(t.upper())
        
        logger.info(f"Encontrados {len(ticker_list)} tickers unicos na colecao 'ativos'.")
    except Exception as e:
        logger.error(f"Erro ao aceder ao Firebase: {e}")
        return

    from scraper.registry import SCRAPER_REGISTRY
    yahoo_scraper = YahooFinanceScraper(pause_seconds=1.5)
    finviz_scraper = SCRAPER_REGISTRY.get("finviz")
    
    # Separar prioritarios
    priority_list = []
    others_list = []
    
    for t in ticker_list:
        is_priority = False
        for p in PRIORITY_TICKERS:
            if p in t: # Matches VWCE or VWCE.DE
                is_priority = True
                break
        
        if is_priority:
            priority_list.append(t)
        else:
            others_list.append(t)
    
    logger.info(f"Prioritarios ({len(priority_list)}): {priority_list}")
    logger.info(f"Restantes: {len(others_list)}")

    updated_count = 0
    failed_count = 0

    # 1. Processar prioritarios
    logger.info(">>> Processando tickers prioritarios...")
    for ticker_id in priority_list:
        if process_ticker(ticker_id, yahoo_scraper, finviz_scraper):
            updated_count += 1
        else:
            failed_count += 1
        time.sleep(1.5)

    # 2. Processar restantes
    logger.info(">>> Processando restantes tickers...")
    for ticker_id in others_list:
        if process_ticker(ticker_id, yahoo_scraper, finviz_scraper):
            updated_count += 1
        else:
            failed_count += 1
        time.sleep(1.0)

    logger.info("-" * 30)
    logger.info(f"Atualizacao concluida!")
    logger.info(f"Sucesso: {updated_count}")
    logger.info(f"Falhas: {failed_count}")
    logger.info("-" * 30)

if __name__ == "__main__":
    refresh_smas_prioritized()
