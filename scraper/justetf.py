import re
import time
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from scraper.base import BaseScraper


# ---------------------------------------------------------------------------
# Known ticker → ISIN mapping for common EU ETFs.
# This avoids relying on the JavaScript-rendered JustETF search page.
# Add more entries here as needed.
# ---------------------------------------------------------------------------
TICKER_ISIN_MAP: Dict[str, str] = {
    # iShares sector ETFs (XETRA / gettex, EUR)
    "QDVE": "IE00B3WJKG14",   # S&P 500 IT
    "QDVK": "IE00B4MCHD36",   # S&P 500 Consumer Discretionary
    "QDVF": "IE00B3WJKN06",   # S&P 500 Financials
    "IUIT": "IE00B3WJKG14",   # iShares S&P 500 IT (USD, LSE)
    "IU5C": "IE00BDDRF478",   # iShares Core € Corp Bond
    "2B7D": "IE00BDBRDM35",   # iShares USD Corp Bond
    # Xtrackers
    "XDWF": "IE00BM67HL84",   # Xtrackers MSCI World Financials
    # Amundi / Lyxor
    "G2X":  "LU1681048804",   # Lyxor MSCI World
    "DAVV": "LU0392494992",   # Xtrackers MSCI World Swap
    # Vanguard
    "VUSA": "IE00B3XXRP09",   # Vanguard S&P 500
    "VUAA": "IE00B3XXRP09",   # Vanguard S&P 500 (Acc)
    "VUSD": "IE00B3XXRP09",   # Vanguard S&P 500 (USD)
    # Misc
    "EUNK": "IE00B3F81R35",   # iShares Core MSCI World
    "JEDI": "IE00BFNM3P36",   # JPMorgan Global Equity
    "VVMX": "IE00BKX55S42",   # Vanguard FTSE All-World
    "VZLC": "IE00B3RBWM25",   # Vanguard FTSE All-World High Div
    "VWCE": "IE00BK5BQT80",   # Vanguard FTSE All-World (Acc)
    # FT Nasdaq Smart Grid
    "GRID":     "IE000J80JTL1",
    "GRID:GER": "IE000J80JTL1",
    "GRID:FRA": "IE000J80JTL1",
    "GRID:IE":  "IE000J80JTL1",
    # Added
    "EXSA": "DE0002635307",   # iShares STOXX Europe 600
    "EUNN": "IE00B3VWMM18",   # iShares MSCI World Small Cap
    "NUKL": "IE000M7V94J1",   # VanEck Uranium and Nuclear
}


class JustETFScraper(BaseScraper):
    source_name = "justetf"
    # The JSON API endpoint resolves queries server-side (no JS needed)
    API_URL     = "https://www.justetf.com/api/etfs"
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
        """
        Resolve a ticker to an ISIN using:
          1. Local TICKER_ISIN_MAP  (instant, no network)
          2. JustETF JSON API       (server-side search, no JS needed)
        The old approach of scraping the HTML search page failed because
        justETF renders its search results via JavaScript.
        """
        q = query.upper().strip()

        # 1. Fast path: local map
        if q in TICKER_ISIN_MAP:
            isin = TICKER_ISIN_MAP[q]
            return [{"ticker": q, "name": q, "exchange": "JustETF", "isin": isin}]

        # 2. JustETF JSON API (requires Accept + Referer headers)
        api_headers = {
            **self.session.headers,
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.justetf.com/en/find-etf.html",
        }
        params = {
            "query": q,
            "search": "ALL",
            "locale": "en",
            "valutaId": "EUR",
        }
        try:
            r = self.session.get(self.API_URL, params=params,
                                 headers=api_headers, timeout=15)
            r.raise_for_status()
            time.sleep(self.pause_seconds)
            data = r.json()
            results = []
            for item in data.get("hits", data.get("results", []))[:5]:
                isin = item.get("isin", "")
                name = item.get("name", item.get("shortName", q))
                if isin:
                    # Cache for future calls
                    TICKER_ISIN_MAP[q] = isin
                    results.append({
                        "ticker": q,
                        "name": name,
                        "exchange": "JustETF",
                        "isin": isin,
                    })
            return results
        except Exception as e:
            # API failed – signal clearly so scrape_quote can raise a useful error
            raise ValueError(
                f"JustETF: could not resolve '{query}' via API ({e}). "
                f"Add it to TICKER_ISIN_MAP in scraper/justetf.py."
            ) from e

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
        
        # Price extraction (specific data-testid found via browser)
        price_tag = soup.find("div", class_="realtime-quotes")
        if not price_tag:
             price_tag = soup.find("span", {"data-testid": "realtime-quotes_price-value"})
        if not price_tag:
             price_tag = soup.find("div", class_="etf-data-row")
        if not price_tag:
             # Search for text "Latest quote" and get parent
             lq_label = soup.find(string=re.compile(r"Latest quote", re.I))
             if lq_label:
                 price_tag = lq_label.find_parent("div").find("span", class_="val") or lq_label.find_parent("div")
             
        if price_tag:
            # If we found the wrapper, search within it
            val = price_tag.find("span", {"data-testid": "realtime-quotes_price-value"}) or price_tag.find("span", class_="val") or price_tag
            metrics["valorStock"] = self._clean_text(val.get_text())
        
        # Fallback 5: Check meta tags or global regex in HTML
        if not metrics.get("valorStock"):
            meta_desc = soup.find("meta", property="og:description")
            if meta_desc and "EUR" in meta_desc.get("content", ""):
                 # Often contains "Price: 336.63 EUR"
                 match = re.search(r"([\d,.]+)\s*EUR", meta_desc["content"])
                 if match:
                     metrics["valorStock"] = match.group(1)
        
        if not metrics.get("valorStock"):
             # Last resort: search for a pattern like "336.63 EUR" in the whole text
             match = re.search(r"(\d{2,}\.\d{2})\s*EUR", soup.get_text())
             if match:
                 metrics["valorStock"] = match.group(1)
                 
        
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
            label_elem = panel.find(["strong", "label", "dt"])
            value_elem = panel.find(["span", "dd"]) or panel
            if label_elem:
                k = self._clean_text(label_elem.get_text())
                if k:
                    v_elem = value_elem.find_next_sibling() or value_elem
                    v = self._clean_text(v_elem.get_text())
                    if v and k not in metrics:
                        metrics[k] = v  # BUG FIX: was `metrics[key]` (outer-loop var)

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
