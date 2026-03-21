import re
import time
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from scraper.base import BaseScraper


class JustETFScraper(BaseScraper):
    source_name = "justetf"
    SEARCH_URL = "https://www.justetf.com/en/search.html"
    PROFILE_URL = "https://www.justetf.com/en/etf-profile.html"

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

    def _clean_text(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return re.sub(r"\s+", " ", value).strip()

    def search_ticker(self, query: str, market: str = "EU") -> List[Dict[str, Any]]:
        params = {"query": query, "search": "ALL"}
        response = self.session.get(self.SEARCH_URL, params=params, timeout=20)
        response.raise_for_status()
        time.sleep(self.pause_seconds)
        
        soup = BeautifulSoup(response.text, "lxml")
        results = []
        
        # Look for the results table
        table = soup.find("table")
        if table:
            rows = table.find_all("tr")[1:] # Skip header
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    name_link = cols[1].find("a")
                    if name_link:
                        name = self._clean_text(name_link.get_text())
                        isin = ""
                        # Try to find ISIN in the columns (usually the last or second to last)
                        for col in cols:
                            text = col.get_text().strip()
                            if re.match(r"^[A-Z]{2}[0-9A-Z]{10}$", text):
                                isin = text
                                break
                        
                        results.append({
                            "ticker": isin or query,
                            "name": name,
                            "exchange": "JustETF",
                            "isin": isin
                        })
        
        return results[:5]

    def scrape_quote(self, ticker: str, market: str = "EU") -> Dict[str, Any]:
        # Ticker on JustETF is often an ISIN or we search for it
        # If it looks like an ISIN, go direct to profile
        if re.match(r"^[A-Z]{2}[0-9A-Z]{10}$", ticker.upper()):
            url = f"{self.PROFILE_URL}?isin={ticker.upper()}"
        else:
            # Search first to get ISIN
            suggestions = self.search_ticker(ticker, market)
            if not suggestions:
                raise ValueError(f"No ETF found for '{ticker}' on JustETF")
            isin = suggestions[0].get("isin")
            if not isin:
                raise ValueError(f"Could not find ISIN for '{ticker}' on JustETF")
            url = f"{self.PROFILE_URL}?isin={isin}"

        response = self.session.get(url, timeout=20)
        response.raise_for_status()
        time.sleep(self.pause_seconds)
        
        soup = BeautifulSoup(response.text, "lxml")
        metrics = {}
        
        # Fund name
        title_tag = soup.find("h1")
        company = self._clean_text(title_tag.get_text()) if title_tag else ticker
        
        # Robust extraction: multiple selectors for JustETF profile data
        # 1. h1 title already done
        # 2. Info tables
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                tds = row.find_all(["td", "th"])
                if len(tds) >= 2:
                    key_elem = tds[0]
                    val_elem = tds[1]
                    key = self._clean_text(key_elem.get_text())
                    val = self._clean_text(val_elem.get_text())
                    if key and val and key not in metrics:
                        metrics[key] = val

        # 3. Key facts panels (common JustETF classes)
        panels = soup.find_all(["div", "span"], class_=re.compile(r"(fact|key|info|val|metric|data)"))
        for panel in panels:
            label_elem = panel.find(["strong", "label", "dt", ".label", "[class*='label']"])
            value_elem = panel.find(["span", "dd", ".value", "[class*='value']"]) or panel
            if label_elem:
                k = self._clean_text(label_elem.get_text())
                if k:
                    v_elem = value_elem.find_next_sibling() or value_elem
                    v = self._clean_text(v_elem.get_text())
                    if v and k not in metrics:
                        metrics[key] = v

        # 4. Specific JustETF structures
        fact_rows = soup.find_all("div", class_=re.compile(r"fact-row|key-fact"))
        for row in fact_rows:
            label = row.find(class_=re.compile(r"label|key"))
            value = row.find(class_=re.compile(r"value|data"))
            if label and value:
                metrics[self._clean_text(label.get_text())] = self._clean_text(value.get_text())

        # 5. Meta/og:title fallback for company
        if not company:
            og_title = soup.find("meta", property="og:title")
            if og_title:
                company = self._clean_text(og_title.get("content"))


        return {
            "source": self.source_name,
            "market": market,
            "ticker_requested": ticker,
            "ticker_used": ticker, # or ISIN
            "url": url,
            "title": {
                "ticker": ticker,
                "company": company
            },
            "metrics": metrics
        }
