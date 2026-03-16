import re
import time
from typing import Any, Dict, Optional

import requests
from bs4 import BeautifulSoup

from scraper.base import BaseScraper


class FinvizScraper(BaseScraper):
    source_name = "finviz"
    BASE_URL = "https://finviz.com/quote.ashx"

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

    def _normalize_ticker(self, ticker: str, market: str) -> str:
        return ticker.strip().upper()

    def _get_html(self, ticker: str) -> str:
        params = {
            "t": ticker,
            "ty": "c",
            "ta": "1",
            "p": "m",
        }

        response = self.session.get(self.BASE_URL, params=params, timeout=20)
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

    def scrape_quote(self, ticker: str, market: str) -> Dict[str, Any]:
        normalized_ticker = self._normalize_ticker(ticker, market)

        html = self._get_html(normalized_ticker)
        soup = BeautifulSoup(html, "lxml")

        title_data = self._parse_title(soup)
        metrics = self._parse_snapshot_table(soup)

        if not metrics:
            raise ValueError(
                "Não foi possível extrair métricas desta página no Finviz. "
                "O ticker pode não existir nesta fonte ou o HTML pode ter mudado."
            )

        return {
            "source": self.source_name,
            "market": market,
            "ticker_requested": ticker.upper(),
            "ticker_used": normalized_ticker,
            "url": f"{self.BASE_URL}?t={normalized_ticker}&ty=c&ta=1&p=m",
            "title": title_data,
            "metrics": metrics,
        }