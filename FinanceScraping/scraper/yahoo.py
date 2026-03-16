import re
import time
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from scraper.base import BaseScraper


class YahooFinanceScraper(BaseScraper):
    source_name = "yahoo"
    BASE_URL = "https://finance.yahoo.com/quote"

    def __init__(self, pause_seconds: float = 2.0) -> None:
        self.pause_seconds = pause_seconds
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })

    def _clean_text(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return re.sub(r"\s+", " ", value).strip()

    def _get_html(self, ticker: str) -> str:
        url = f"{self.BASE_URL}/{ticker}"
        response = self.session.get(url, timeout=20)
        response.raise_for_status()
        time.sleep(self.pause_seconds)
        return response.text

    def _parse_summary(self, soup: BeautifulSoup) -> Dict[str, str]:
        data: Dict[str, str] = {}
        
        # Main quote header
        header = soup.find("h1", class_="D(ib) Fz(18px)")
        if header:
            company_info = self._clean_text(header.get_text())
            data["company"] = company_info.split(" (")[0]
            data["ticker"] = company_info.split(" (")[1].rstrip(")") if " (" in company_info else ticker
            
        # Key stats table
        stats = {}
        table = soup.find("table", class_="W(100%) M(0) Bdcl(c)")
        if table:
            rows = table.find_all("tr")
            for row in rows:
                tds = row.find_all("td")
                if len(tds) >= 2:
                    key = self._clean_text(tds[0].get_text())
                    value = self._clean_text(tds[1].get_text())
                    if key and value:
                        stats[key] = value
        
        data["metrics"] = stats
        
        return data

    def search_ticker(self, query: str, market: str) -> List[Dict[str, Any]]:
        results = []
        normalized = BaseScraper.normalize_ticker(query, market)
        
        # Simple validation by trying quote page
        try:
            html = self._get_html(normalized)
            soup = BeautifulSoup(html, "lxml")
            summary = self._parse_summary(soup)
            if summary.get("company"):
                results.append({
                    "ticker": normalized,
                    "name": summary["company"],
                    "exchange": market
                })
        except:
            pass
        
        # Yahoo search simulation: https://finance.yahoo.com/quote?q=QUERY but parsing list
        # Placeholder: return normalized if valid-like
        if not results:
            results = [{"ticker": normalized, "name": f"Search '{query}'", "exchange": market}]
        
        return results[:5]

    def scrape_quote(self, ticker: str, market: str) -> Dict[str, Any]:
        normalized_ticker = BaseScraper.normalize_ticker(ticker, market)
        
        # Try original first
        orig_ticker = ticker.strip().upper()
        try:
            html = self._get_html(orig_ticker)
            soup = BeautifulSoup(html, "lxml")
            summary = self._parse_summary(soup)
            if summary.get("metrics"):
                ticker_used = orig_ticker
            else:
                raise ValueError("No metrics")
        except:
            # Fallback to normalized
            html = self._get_html(normalized_ticker)
            soup = BeautifulSoup(html, "lxml")
            summary = self._parse_summary(soup)
            if not summary.get("metrics"):
                raise ValueError("No data found for ticker in Yahoo Finance")
            ticker_used = normalized_ticker

        return {
            "source": self.source_name,
            "market": market,
            "ticker_requested": ticker,
            "ticker_used": ticker_used,
            "url": f"{self.BASE_URL}/{ticker_used}",
            "title": {
                "ticker": summary.get("ticker"),
                "company": summary.get("company")
            },
            "metrics": summary.get("metrics", {})
        }
