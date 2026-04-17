import re
import time
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from scraper.base import BaseScraper, MARKET_SUFFIXES


class FinvizScraper(BaseScraper):
    source_name = "finviz"
    BASE_URL = "https://finviz.com/quote.ashx"
    SEARCH_URL = "https://finviz.com/"  # Use main page or screener for search

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
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,"
                    "image/avif,image/webp,image/apng,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://finviz.com/",
                "Connection": "keep-alive",
            }
        )

    def _clean_text(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return re.sub(r"\s+", " ", value).strip()

    def _get_html(self, url: str, params: dict = None) -> str:
        response = self.session.get(url, params=params, timeout=20)
        response.raise_for_status()
        time.sleep(self.pause_seconds)
        return response.text

    def _parse_snapshot_table(self, soup: BeautifulSoup) -> Dict[str, str]:
        data: Dict[str, str] = {}

        table = soup.find("table", class_="snapshot-table2")
        if not table:
            return data

        cells = table.find_all("td")

        i = 0
        while i < len(cells) - 1:
            key = self._clean_text(cells[i].get_text(" ", strip=True))
            value = self._clean_text(cells[i + 1].get_text(" ", strip=True))

            if key and value:
                data[key] = value

            i += 2

        return data

    def _parse_title(self, soup: BeautifulSoup) -> Dict[str, Optional[str]]:
        result = {
            "ticker": None,
            "company": None,
        }

        header = soup.find("div", class_="quote-header_left")
        if header:
            header_text = self._clean_text(header.get_text(" ", strip=True))
            result["ticker"] = header_text

        title_link = soup.find("a", class_="tab-link")
        if title_link:
            company_name = self._clean_text(title_link.get_text(" ", strip=True))
            result["company"] = company_name

        return result

    def search_ticker(self, query: str, market: str) -> List[Dict[str, Any]]:
        """
        Simple Finviz ticker search via screener or group pages.
        For now, try direct quote lookup for top matches (enhance later with screener params).
        """
        results = []
        normalized_query = BaseScraper.normalize_ticker(query, market)
        
        # Try direct quote page for validation
        try:
            html = self._get_html(self.BASE_URL, {"t": normalized_query})
            soup = BeautifulSoup(html, "lxml")
            title_data = self._parse_title(soup)
            if title_data["company"]:
                results.append({
                    "ticker": normalized_query,
                    "name": title_data["company"],
                    "exchange": market
                })
        except:
            pass
        
        # Finviz screener search simulation - fetch screener with ticker filter
        screener_params = {
            "o": "-marketcap",
            "f": f"geo_{market.lower() if market.lower() in ['us', 'eu'] else 'other'}",  # Approximate
            "s": normalized_query[:1]  # Group by first letter
        }
        # Note: Full screener parsing would list multiple; placeholder for top 1-5
        # For demo, return normalized if valid
        if not results:
            results.append({
                "ticker": normalized_query,
                "name": f"Company matching {query}",
                "exchange": market
            })
        
        return results[:5]  # Limit

    def scrape_quote(self, ticker: str, market: str) -> Dict[str, Any]:
        normalized_ticker = BaseScraper.normalize_ticker(ticker, market)

        # Try original ticker first if different
        if normalized_ticker != ticker.upper():
            try:
                html = self._get_html(self.BASE_URL, {"t": ticker.upper()})
                soup_test = BeautifulSoup(html, "lxml")
                if soup_test.find("table", class_="snapshot-table2"):
                    normalized_ticker = ticker.upper()
            except:
                pass

        html = self._get_html(self.BASE_URL, {"t": normalized_ticker})
        soup = BeautifulSoup(html, "lxml")

        title_data = self._parse_title(soup)
        metrics = self._parse_snapshot_table(soup)

        if not metrics:
            raise ValueError(
                f"Não foi possível extrair métricas para {normalized_ticker} no Finviz. "
                "O ticker pode não existir ou HTML mudou. Tente outro formato."
            )

        # Normalize SMAs to absolute values if they are % (Finviz specific)
        from scraper.transformer import clean_float
        price_val = clean_float(metrics.get("Price"))
        if price_val > 0:
            for sma_key in ["SMA50", "SMA200"]:
                val_str = metrics.get(sma_key)
                if val_str and "%" in val_str:
                    pct_dist = clean_float(val_str)
                    # price = sma * (1 + dist) => sma = price / (1 + dist)
                    absolute_sma = price_val / (1 + pct_dist)
                    metrics[f"{sma_key}_abs"] = round(absolute_sma, 2)
                    metrics[sma_key] = round(absolute_sma, 2) # Overwrite to harmonize

        return {
            "source": self.source_name,
            "market": market,
            "ticker_requested": ticker,
            "ticker_used": normalized_ticker,
            "url": f"{self.BASE_URL}?t={normalized_ticker}&ty=c&ta=1&p=m",
            "title": title_data,
            "metrics": metrics,
        }
