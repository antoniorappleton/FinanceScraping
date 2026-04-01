import re
import time
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from scraper.base import BaseScraper


class GoogleFinanceScraper(BaseScraper):
    source_name = "google_finance"
    BASE_URL = "https://www.google.com/finance/quote"

    EXCHANGE_MAP = {
        "US": "NYSE,NASDAQ",
        "EU": "FRA,XETR",
        "PT": "ELI",
        "BR": "BVMF",
        "LON": "LON",
    }

    def __init__(self, pause_seconds: float = 2.0) -> None:
        self.pause_seconds = pause_seconds
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })

    def _clean_text(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return re.sub(r"\s+", " ", value).strip()

    def _get_html(self, ticker: str, market: str) -> str:
        # If ticker already has an exchange (TICKER:EXCHANGE), use it directly
        if ":" in ticker:
            ticker_param = ticker
            url = f"{self.BASE_URL}/{ticker_param}"
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            return response.text
        else:
            # Try multiple exchanges in order
            exchanges = self.EXCHANGE_MAP.get(market, "NASDAQ").split(",")
            last_error = None
            
            for ex in exchanges:
                ticker_param = f"{ticker}:{ex}"
                url = f"{self.BASE_URL}/{ticker_param}"
                try:
                    response = self.session.get(url, timeout=20)
                    response.raise_for_status()
                    
                    # Verify if the page found actually has a price
                    soup = BeautifulSoup(response.text, "lxml")
                    price = soup.find("div", class_="YMlKec fxKbKc")
                    if price:
                        time.sleep(self.pause_seconds)
                        return response.text
                    else:
                         continue # Try next exchange
                except Exception as e:
                    last_error = e
                    continue
            
            if last_error:
                raise last_error
            raise ValueError(f"No results for {ticker} on any exchange for market {market}")

    def _parse_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        data: Dict[str, str] = {}
        
        # Company name and ticker
        title = soup.find("h1", class_="lVhDvP")
        if title:
            company_info = self._clean_text(title.get_text())
            data["company"] = company_info.split(" - ")[0] if " - " in company_info else company_info
            data["ticker"] = company_info.split(" - ")[-1] if " - " in company_info else ticker
        
        # Price and key stats
        price = soup.find("div", class_="YMlKec fxKbKc")
        if price:
            data["price"] = self._clean_text(price.get_text())
        
        # Info table
        infos = soup.find_all("div", class_="P6K39b")
        for info in infos:
            label = info.find("div", class_="MUFPAe")
            value = info.find("div", class_="v7xafc")
            if label and value:
                data[self._clean_text(label.get_text())] = self._clean_text(value.get_text())
        
        return data

    def search_ticker(self, query: str, market: str) -> List[Dict[str, Any]]:
        results = []
        normalized = BaseScraper.normalize_ticker(query, market)
        
        try:
            html = self._get_html(normalized, market)
            soup = BeautifulSoup(html, "lxml")
            info = self._parse_info(soup)
            if info.get("company"):
                results.append({
                    "ticker": normalized,
                    "name": info["company"],
                    "exchange": market
                })
        except:
            pass
        
        if not results:
            results = [{"ticker": normalized, "name": f"Possible match for '{query}'", "exchange": market}]
        
        return results[:5]

    def scrape_quote(self, ticker: str, market: str) -> Dict[str, Any]:
        normalized_ticker = BaseScraper.normalize_ticker(ticker, market)
        
        # Try original first
        orig_ticker = ticker.strip().upper()
        ticker_used = orig_ticker
        try:
            html = self._get_html(orig_ticker, market)
            soup = BeautifulSoup(html, "lxml")
            info = self._parse_info(soup)
            if info.get("price") or len(info) > 1:
                pass  # Good
            else:
                raise ValueError("No data")
        except:
            # Fallback normalized
            html = self._get_html(normalized_ticker, market)
            soup = BeautifulSoup(html, "lxml")
            info = self._parse_info(soup)
            if not info.get("price"):
                raise ValueError("No quote data found in Google Finance")
            ticker_used = normalized_ticker

        return {
            "source": self.source_name,
            "market": market,
            "ticker_requested": ticker,
            "ticker_used": ticker_used,
            "url": f"{self.BASE_URL}/{ticker_used}:{self.EXCHANGE_MAP.get(market, 'NASDAQ')}",
            "title": {
                "ticker": info.get("ticker"),
                "company": info.get("company")
            },
            "metrics": info
        }
