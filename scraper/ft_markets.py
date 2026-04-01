import re
import time
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from scraper.base import BaseScraper


class FTMarketsScraper(BaseScraper):
    source_name = "ft_markets"
    BASE_URL = "https://markets.ft.com/data/etfs/tearsheet/summary?s="
    EQUITY_URL = "https://markets.ft.com/data/equities/tearsheet/summary?s="

    def __init__(self, pause_seconds: float = 1.5) -> None:
        self.pause_seconds = pause_seconds
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        })

    def _clean_text(self, value: Optional[str]) -> str:
        if value is None:
            return ""
        return re.sub(r"\s+", " ", value).strip()

    def search_ticker(self, query: str, market: str) -> List[Dict[str, Any]]:
        # FT search is complex, we mostly use direct tickers which FT handles well with colons
        # Return a possible match
        return [{"ticker": query, "name": f"FT Markets match for {query}", "exchange": market}]

    def scrape_quote(self, ticker: str, market: str) -> Dict[str, Any]:
        # FT uses TICKER:EXCH:CUR format often.
        # If it's an ETF, use BASE_URL, else EQUITY_URL
        # We can try both or assume based on market/ticker
        
        # Try ETF first if it's EU market and short ticker
        is_likely_etf = len(ticker.split(":")[0]) <= 6 and market in ["EU", "GLOBAL"]
        
        if is_likely_etf:
            url = f"{self.BASE_URL}{ticker}"
        else:
            url = f"{self.EQUITY_URL}{ticker}"
            
        try:
            response = self.session.get(url, timeout=20)
            
            # If EU market and not found or redirected to search, try GER:EUR suffix
            # Note: FT doesn't 302, it just renders a different page on 200 often
            if (response.status_code != 200 or "search" in response.url.lower()) and market == "EU" and ":" not in ticker:
                ticker_ger = f"{ticker}:GER:EUR"
                url = f"{self.BASE_URL if is_likely_etf else self.EQUITY_URL}{ticker_ger}"
                response = self.session.get(url, timeout=20)

            if response.status_code != 200 and is_likely_etf:
                # Try equity fallback
                url = f"{self.EQUITY_URL}{ticker}"
                response = self.session.get(url, timeout=20)
                
            response.raise_for_status()
            time.sleep(self.pause_seconds)
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # If the page still looks like a search result (no price), try one more time
            if not soup.find("span", class_="mod-ui-data-list__value") and \
               not soup.find("span", class_="mod-tearsheet-overview_header_price") and \
               market == "EU" and "GER:EUR" not in url:
                
                ticker_ger = f"{ticker}:GER:EUR"
                url = f"{self.BASE_URL if is_likely_etf else self.EQUITY_URL}{ticker_ger}"
                response = self.session.get(url, timeout=20)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "lxml")

            metrics = {}
            
            # 1. Company name
            name_tag = soup.find("h1", class_="mod-tearsheet-overview__header__name")
            company = self._clean_text(name_tag.get_text()) if name_tag else ticker
            
            # 2. Price and basic info
            # Usually in a list or specific classes
            price_tag = soup.find("span", class_="mod-ui-data-list__value")
            if not price_tag:
                 # Fallback for some tear sheets
                 price_tag = soup.find("span", class_="mod-tearsheet-overview_header_price")
                 
            if price_tag:
                metrics["price"] = self._clean_text(price_tag.get_text())
            else:
                # No price found, this source failed for this ticker
                raise ValueError(f"No price found for {ticker} on FT Markets")
            change_tags = soup.find_all("span", class_=re.compile(r"mod-ui-data-list__value--[positive|negative]"))
            if change_tags:
                 metrics["change"] = self._clean_text(change_tags[0].get_text())
            
            # 4. Summary data list (commonly performance/volume)
            data_items = soup.find_all("li", class_="mod-ui-data-list__item")
            for item in data_items:
                label = item.find("span", class_="mod-ui-data-list__label")
                value = item.find("span", class_="mod-ui-data-list__value")
                if label and value:
                    k = self._clean_text(label.get_text())
                    v = self._clean_text(value.get_text())
                    if k and v:
                        metrics[k] = v

            # 5. Profile / Key stats table
            tables = soup.find_all("table", class_="mod-ui-table")
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    tds = row.find_all(["td", "th"])
                    if len(tds) >= 2:
                        k = self._clean_text(tds[0].get_text())
                        v = self._clean_text(tds[1].get_text())
                        if k and v:
                            metrics[k] = v

            return {
                "source": self.source_name,
                "market": market,
                "ticker_requested": ticker,
                "ticker_used": ticker,
                "url": url,
                "title": {
                    "ticker": ticker,
                    "company": company
                },
                "metrics": metrics
            }

        except Exception as e:
            raise ValueError(f"FT Markets failed for {ticker}: {e}")
