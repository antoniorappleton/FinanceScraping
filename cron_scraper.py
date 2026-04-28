import time
import os
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Import scrapers and manager
from scraper.registry import SCRAPER_REGISTRY
from scraper.firebase_manager import firebase_manager
from scraper.transformer import clean_float, clean_row_for_firestore, normalize_ticker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _is_valid_valor_stock(val) -> bool:
    """
    Returns True if val is a valid numeric price (not None, not '#N/A',
    not any other non-numeric string, and greater than zero).
    """
    if val is None:
        return False
    if isinstance(val, (int, float)):
        return val > 0
    if isinstance(val, str):
        stripped = val.strip()
        if not stripped or stripped.startswith("#"):
            return False
        try:
            return float(stripped.replace(",", ".")) > 0
        except ValueError:
            return False
    return False


def _scrape_price_for_ticker(ticker_id: str, ticker: str, market_code: str, sources_to_try: list) -> tuple:
    """
    Tries each source until a valid price is found.
    Returns (price_val, payload_partial, source_name) or (None, None, None) on failure.
    """
    for source_name in sources_to_try:
        if source_name not in SCRAPER_REGISTRY:
            continue
        scraper = SCRAPER_REGISTRY[source_name]
        try:
            result = scraper.scrape_quote(ticker=ticker, market=market_code)
            metrics = result.get("metrics", {})
            method_used = result.get("method", "scrape")

            price_str = (
                metrics.get("valorStock") or
                result.get("title", {}).get("price") or
                metrics.get("price") or
                metrics.get("Latest quote") or
                metrics.get("NAV") or
                metrics.get("Quote") or
                metrics.get("Price")
            )

            price_val = clean_float(price_str)
            if price_val and price_val > 0:
                return price_val, result, source_name, method_used

            logger.warning(
                f"[{ticker_id}] Source '{source_name}' returned invalid price: {price_str!r}"
            )
        except Exception as e:
            logger.error(f"[{ticker_id}] Error with source '{source_name}': {e}")
            if "429" in str(e):
                logger.warning("Rate limit hit. Sleeping longer...")
                time.sleep(10)

    return None, None, None, None


def run_automated_scrape(mode="full"):
    """
    Main logic for automated scraping.

    Per-ticker decision flow:
    ─────────────────────────────────────────────────────────────────────
    1. Read current valorStock from Firestore.
    2. If valorStock is MISSING / '#N/A' / any non-numeric value:
         → Force-scrape the price NOW and persist just valorStock.
         → Skip the normal fast/full update for this cycle.
    3. If valorStock is a valid number:
         → Run the normal fast or full sync as configured.
    ─────────────────────────────────────────────────────────────────────
    """
    logger.info(f"Starting automated scraping ({mode.upper()} sync)...")

    # 1. Get tickers from Firestore
    try:
        docs = firebase_manager.db.collection("acoesDividendos").stream()
        ticker_data = []
        for d in docs:
            data = d.to_dict()
            ticker = data.get("ticker", d.id).upper()
            market = data.get("mercado", "")
            valor_stock_raw = data.get("valorStock")  # may be str "#N/A", float, or None
            ticker_data.append({
                "ticker": ticker,
                "market_name": market,
                "valorStock_current": valor_stock_raw,
            })
    except Exception as e:
        logger.error(f"Error fetching tickers: {e}")
        return

    if not ticker_data:
        logger.warning("No tickers found in 'acoesDividendos' collection or Firebase not initialized.")
        return

    # Sort: Portugal first
    ticker_data.sort(key=lambda x: x.get("market_name") != "Portugal")

    logger.info(f"Found {len(ticker_data)} tickers to process.")

    for item in ticker_data:
        ticker_id = item["ticker"]
        market_name = item["market_name"]
        valor_stock_current = item["valorStock_current"]

        # Normalize ticker for scraping (e.g. XETR_ABC -> ABC)
        ticker = normalize_ticker(ticker_id)

        # Detect market code
        market_code = "US"
        m_name_lower = (market_name or "").lower()

        if m_name_lower == "portugal" or ".ls" in ticker.lower() or ".ls" in ticker_id.lower():
            market_code = "PT"
        elif "xetra" in m_name_lower or "frankfurt" in m_name_lower or ticker_id.startswith("XETR_"):
            market_code = "EU"
        elif any(x in m_name_lower for x in ["euronext", "milan", "madrid", "paris", "europe", "eu", "justetf", "asia", "emerging", "global"]):
            market_code = "EU"
        elif any(x in m_name_lower for x in ["brasil", "brazil", "b3", "bvmf"]) or ".sa" in ticker.lower() or ticker_id.startswith("BVMF_"):
            market_code = "BR"
        elif "." in ticker:
            market_code = "PT" if ticker.endswith(".LS") else "US"

        # Determine sources to try based on market
        if market_code == "EU":
            sources_to_try = ["ft_markets", "justetf", "yahoo", "google_finance"]
        elif market_code == "PT":
            sources_to_try = ["yahoo", "google_finance", "ft_markets"]
        elif market_code == "BR":
            sources_to_try = ["yahoo"]
        else:  # US or Global
            sources_to_try = ["yahoo", "ft_markets", "google_finance", "finviz"]

        # ── DECISION POINT ────────────────────────────────────────────
        # If valorStock is missing or invalid, scrape price first.
        if not _is_valid_valor_stock(valor_stock_current):
            logger.info(
                f"[{ticker_id}] valorStock is invalid/missing (current={valor_stock_current!r}). "
                f"Performing FULL bootstrap for all indicators..."
            )
            # Find first source that works and do a full sync payload
            bootstrapped = False
            for source_name in sources_to_try:
                if source_name not in SCRAPER_REGISTRY: continue
                try:
                    scraper = SCRAPER_REGISTRY[source_name]
                    result = scraper.scrape_quote(ticker=ticker, market=market_code)
                    metrics = result.get("metrics", {})
                    price_val = clean_float(
                        metrics.get("valorStock") or metrics.get("price") or metrics.get("Price") or 
                        metrics.get("Latest quote") or metrics.get("NAV")
                    )
                    
                    if price_val and price_val > 0:
                        # Success! Build full payload immediately
                        payload = {
                            "valorStock": price_val,
                            "priceChange_1d": clean_float(metrics.get("change_pct") or metrics.get("Change")),
                            "priceChange_1w": clean_float(metrics.get("priceChange_1w") or metrics.get("Perf Week")),
                            "priceChange_1m": clean_float(metrics.get("priceChange_1m") or metrics.get("Perf Month")),
                            "priceChange_1y": clean_float(metrics.get("priceChange_1y") or metrics.get("Perf Year")),
                            "yield": clean_float(metrics.get("yield") or metrics.get("Dividend Yield") or metrics.get("Dividend %")),
                            "pe": clean_float(metrics.get("pe") or metrics.get("PE Ratio (TTM)") or metrics.get("P/E")),
                            "rsi": clean_float(metrics.get("rsi") or metrics.get("RSI (14)")),
                            "sma50": clean_float(metrics.get("sma50") or metrics.get("SMA50")),
                            "sma200": clean_float(metrics.get("sma200") or metrics.get("SMA200")),
                            "marketCap": clean_float(metrics.get("Market Cap") or metrics.get("marketCap") or metrics.get("Fund size")),
                            "source_used": f"{source_name} (bootstrap)",
                            "nome": result.get("title", {}).get("company", ticker),
                            "lastFullSync": datetime.now().isoformat(),
                        }
                        # Add extra metrics
                        cleaned_metrics = clean_row_for_firestore(metrics)
                        for k, v in cleaned_metrics.items():
                            if k not in payload: payload[k] = v

                        if firebase_manager.update_market_data(ticker_id, payload):
                            logger.info(f"[{ticker_id}] FULL bootstrap success via {source_name}")
                            bootstrapped = True
                            break
                except Exception as e:
                    logger.error(f"[{ticker_id}] Bootstrap error with {source_name}: {e}")
            
            if not bootstrapped:
                logger.error(f"[{ticker_id}] Could not bootstrap even a price. Skipping.")
            
            time.sleep(2)
            continue
        # ── END DECISION POINT ────────────────────────────────────────

        # Normal fast / full sync
        success = False

        for source_name in sources_to_try:
            if source_name not in SCRAPER_REGISTRY:
                continue

            scraper = SCRAPER_REGISTRY[source_name]
            try:
                result = scraper.scrape_quote(ticker=ticker, market=market_code)
                metrics = result.get("metrics", {})
                method_used = result.get("method", "scrape")

                # Universal price extraction
                price_str = (
                    metrics.get("valorStock") or
                    result.get("title", {}).get("price") or
                    metrics.get("price") or
                    metrics.get("Latest quote") or
                    metrics.get("NAV") or
                    metrics.get("Quote") or
                    metrics.get("Price")
                )

                change_str = metrics.get("change_pct") or metrics.get("Change") or metrics.get("Change (pct)")
                market_cap_str = metrics.get("Market Cap") or metrics.get("marketCap") or metrics.get("Fund size")

                price_val = clean_float(price_str)
                is_valid_price = price_val and price_val > 0

                if not price_str:
                    logger.warning(
                        f"[{ticker_id}] Source '{source_name}' returned no price string."
                    )

                if mode == "fast":
                    payload = {
                        "valorStock": price_val,
                        "priceChange_1d": clean_float(change_str),
                        "marketCap": clean_float(market_cap_str),
                        "source_used": f"{source_name} ({method_used})",
                        "method_used": method_used,
                        "nome": result.get("title", {}).get("company", ticker),
                    }
                else:
                    # Full Sync — all indicators
                    payload = {
                        "valorStock": price_val,
                        "priceChange_1d": clean_float(change_str),
                        "priceChange_1w": clean_float(metrics.get("priceChange_1w") or metrics.get("Perf Week")),
                        "priceChange_1y": clean_float(metrics.get("priceChange_1y") or metrics.get("Perf Year")),
                        "priceChange_1m": clean_float(metrics.get("priceChange_1m") or metrics.get("Perf Month")),
                        "yield": clean_float(metrics.get("yield") or metrics.get("Dividend Yield") or metrics.get("Dividend %")),
                        "pe": clean_float(metrics.get("pe") or metrics.get("PE Ratio (TTM)") or metrics.get("P/E")),
                        "roa": clean_float(metrics.get("roa") or metrics.get("ROA") or metrics.get("Return on Assets")),
                        "roe": clean_float(metrics.get("roe") or metrics.get("ROE") or metrics.get("Return on Equity")),
                        "roi": clean_float(metrics.get("roi") or metrics.get("ROI")),
                        "rsi": clean_float(metrics.get("rsi") or metrics.get("RSI (14)")),
                        "roic": clean_float(metrics.get("roic")),
                        "ev_ebitda": clean_float(metrics.get("ev_ebitda") or metrics.get("EV/EBITDA")),
                        "marketCap": clean_float(market_cap_str),
                        "ebitda": clean_float(metrics.get("ebitda") or metrics.get("EBITDA")),
                        "sma20": clean_float(metrics.get("sma20")),
                        "sma50": clean_float(metrics.get("sma50") or metrics.get("SMA50")),
                        "sma100": clean_float(metrics.get("sma100")),
                        "sma200": clean_float(metrics.get("sma200") or metrics.get("SMA200")),
                        "sma_vol20": clean_float(metrics.get("sma_vol20")),
                        "above_sma50": metrics.get("above_sma50"),
                        "above_sma200": metrics.get("above_sma200"),
                        "golden_cross": metrics.get("golden_cross"),
                        "source_used": f"{source_name} ({method_used})",
                        "method_used": method_used,
                        "nome": result.get("title", {}).get("company", ticker),
                        "lastFullSync": datetime.now().isoformat(),
                    }

                    # Persist any extra scraped metrics not already in the payload
                    cleaned_metrics = clean_row_for_firestore(metrics)
                    for k, v in cleaned_metrics.items():
                        if k not in payload:
                            payload[k] = v

                # Update Firestore only if price is valid
                if is_valid_price:
                    if firebase_manager.update_market_data(ticker_id, payload):
                        logger.info(
                            f"[{ticker_id}] updated ({mode}) via {source_name} "
                            f"(ticker used: {ticker}) → valorStock={price_val}"
                        )
                        success = True
                        break  # Move to next ticker
                else:
                    logger.warning(
                        f"[{ticker_id}] Price from '{source_name}' is zero/invalid. Trying next source..."
                    )

            except Exception as e:
                logger.error(f"[{ticker_id}] Error scraping with '{source_name}': {e}")
                if "429" in str(e):
                    logger.warning("Rate limit hit. Sleeping longer...")
                    time.sleep(10)
                continue

        if not success:
            logger.error(f"[{ticker_id}] Failed to update after trying all sources.")

        time.sleep(2)

    logger.info(f"Automated {mode} scraping session finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated Scraper for Firestore")
    parser.add_argument(
        "--mode",
        choices=["fast", "full"],
        default="full",
        help="Sync mode: 'fast' for price/cap, 'full' for all metrics.",
    )
    args = parser.parse_args()
    run_automated_scrape(mode=args.mode)
