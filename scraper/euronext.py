import re
import time
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from scraper.base import BaseScraper


class EuronextScraper(BaseScraper):
    source_name = "euronext"
    SEARCH_API_URL = "https://live.euronext.com/pt/instrumentSearch/searchJSON"
    QUOTE_AJAX_URL = "https://live.euronext.com/pt/ajax/getDetailedQuote/{id}"
    METRICS_AJAX_URL = "https://live.euronext.com/pt/intraday_chart/getDetailedQuoteAjax/{id}/full"

    def __init__(self, pause_seconds: float = 1.0) -> None:
        self.pause_seconds = pause_seconds
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "X-Requested-With": "XMLHttpRequest"
            }
        )

    def _clean_text(self, value: Optional[str]) -> str:
        if value is None:
            return ""
        return re.sub(r"\s+", " ", value).strip()

    def search_ticker(self, query: str, market: str) -> List[Dict[str, Any]]:
        """
        Search for ticker on Euronext using their searchJSON endpoint.
        """
        params = {"q": query}
        try:
            response = self.session.get(self.SEARCH_API_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data:
                link = item.get("link", "")
                if "/product/equities/" in link:
                    # Extract ISIN-MIC from link (e.g., /pt/product/equities/PTEDP0AM0009-XLIS)
                    parts = link.split("/")
                    instr_id = parts[-1] if parts else ""
                    
                    results.append({
                        "ticker": item.get("value", ""),
                        "isin": item.get("isin", ""),
                        "name": item.get("name", ""),
                        "instr_id": instr_id,
                        "exchange": "Euronext"
                    })
            return results
        except Exception as e:
            print(f"Error searching Euronext: {e}")
            return []

    def scrape_quote(self, ticker: str, market: str) -> Dict[str, Any]:
        """
        Scrape quote data for a ticker on Euronext.
        """
        # 1. Search for ID
        search_results = self.search_ticker(ticker, market)
        if not search_results:
            raise ValueError(f"Ticker {ticker} não encontrado na Euronext.")

        # Pick the best match
        match = next((r for r in search_results if r["ticker"] == ticker.upper()), search_results[0])
        instr_id = match["instr_id"]
        
        metrics = {}
        
        # 2. Fetch Price AJAX
        try:
            price_url = self.QUOTE_AJAX_URL.format(id=instr_id)
            res_price = self.session.get(price_url, timeout=15)
            if res_price.status_code == 200:
                soup_price = BeautifulSoup(res_price.text, "lxml")
                price_el = soup_price.find("span", id="header-instrument-price")
                if price_el:
                    metrics["price"] = self._clean_text(price_el.text)
                
                # Change
                change_container = soup_price.find("div", class_="bg-euronext-blue")
                if not change_container:
                     change_container = soup_price.find("div", class_="bg-euronext-red") # Red for negative
                
                if change_container:
                    spans = change_container.find_all("span")
                    if len(spans) >= 2:
                        metrics["change_abs"] = self._clean_text(spans[0].text)
                        metrics["change_pct"] = self._clean_text(spans[1].text).strip("()")
        except Exception as e:
            print(f"Error fetching price for {ticker}: {e}")

        # 3. Fetch Metrics AJAX (Table)
        try:
            metrics_url = self.METRICS_AJAX_URL.format(id=instr_id)
            res_metrics = self.session.get(metrics_url, timeout=15)
            if res_metrics.status_code == 200:
                soup_tab = BeautifulSoup(res_metrics.text, "lxml")
                tables = soup_tab.find_all("table")
                for table in tables:
                    for row in table.find_all("tr"):
                        cols = row.find_all(["td", "th"])
                        if len(cols) >= 2:
                            key = self._clean_text(cols[0].text).lower()
                            val = self._clean_text(cols[1].text)
                            
                            if "capitalização" in key:
                                metrics["Market Cap"] = val
                            elif "volume" in key and "médio" not in key:
                                metrics["Volume"] = val
                            elif "receita" in key or "turnover" in key:
                                metrics["Turnover"] = val
                            elif "transações" in key or "trades" in key:
                                metrics["Trades"] = val
                            elif "vwap" in key:
                                metrics["VWAP"] = val
                            elif "abertura" in key or "abrir" in key:
                                metrics["Open"] = val
                            elif "fecho anterior" in key:
                                metrics["Prev Close"] = val
                            elif "máximo" in key and "dia" in key:
                                metrics["Day High"] = val
                            elif "mínimo" in key and "dia" in key:
                                metrics["Day Low"] = val
                            elif "alta" in key: # AJAX "Alta"
                                metrics["Day High"] = val
                            elif "baixa" in key: # AJAX "Baixa"
                                metrics["Day Low"] = val
                            elif "52 semanas" in key:
                                metrics["52w Range"] = val
                            elif "limite" in key:
                                metrics["Limits"] = val
        except Exception as e:
            print(f"Error fetching metrics for {ticker}: {e}")

        title_data = {
            "ticker": ticker.upper(),
            "company": match["name"],
        }

        return {
            "source": self.source_name,
            "market": market,
            "ticker_requested": ticker,
            "ticker_used": match["ticker"],
            "url": f"https://live.euronext.com/pt/product/equities/{instr_id}",
            "title": title_data,
            "metrics": metrics,
        }
