import requests
import json
import re
import time
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
from scraper.base import BaseScraper

class JustETFScraper(BaseScraper):
    source_name = "justetf"
    BASE_URL = "https://www.justetf.com"

    def __init__(self, pause_seconds: float = 2.0) -> None:
        self.pause_seconds = pause_seconds
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def scrape_quote(self, ticker: str, market: str) -> Dict[str, Any]:
        """
        Scrape JustETF. If ticker looks like an ISIN, use it directly.
        Otherwise, search for it first.
        """
        isin = ticker if re.match(r"^[A-Z]{2}[A-Z0-9]{9}\d$", ticker.upper()) else None
        
        if not isin:
            search_results = self.search_ticker(ticker, market)
            if search_results:
                isin = search_results[0].get("isin")
                ticker_to_use = search_results[0].get("ticker")
            else:
                raise ValueError(f"Could not find ISIN for ticker {ticker} on JustETF")
        else:
            ticker_to_use = isin

        url = f"{self.BASE_URL}/en/etf-profile.html?isin={isin}#holdings"
        response = self.session.get(url, timeout=20)
        response.raise_for_status()
        time.sleep(self.pause_seconds)

        soup = BeautifulSoup(response.text, "lxml")
        
        metrics = {}
        holdings_list = []

        # 1. Extract other metrics from all tables first
        val_tables = soup.find_all("table", class_="table")
        for table in val_tables:
            for row in table.find_all("tr"):
                tds = row.find_all("td")
                if len(tds) >= 2:
                    key = tds[0].get_text(strip=True).lower().replace(" ", "_").replace(".", "")
                    val = tds[1].get_text(strip=True)
                    if key and val:
                        metrics[key] = val

        # 2. Specifically extract holdings
        # They can be in 'chart-data-table' or in a regular table if it's the Top 10 section
        
        # Method A: chart-data-table (Modern JustETF)
        table_containers = soup.find_all("div", class_="chart-data-table")
        for container in table_containers:
            # Check if this container is likely holdings (has links to stock profiles)
            rows = container.find_all("div", class_="chart-data-row")
            for row in rows:
                name_link = row.find("a")
                weight_div = row.find("div", class_="value")
                
                if name_link and weight_div:
                    name = name_link.get_text(strip=True)
                    weight_str = weight_div.get_text(strip=True).replace("%", "")
                    try:
                        weight = float(weight_str)
                        if name and "Weight" not in name:
                            holdings_list.append({
                                "name": name,
                                "symbol": "", 
                                "weight": weight
                            })
                    except:
                        pass

        # Method B: If holdings_list is still empty, look for keys in metrics that look like holdings
        # (This happens if Method A fails but the table parser caught them)
        if not holdings_list:
            for k, v in metrics.items():
                # Heuristic: if value ends with % and key doesn't look like a standard metric
                if isinstance(v, str) and v.endswith("%"):
                    try:
                        weight = float(v.replace("%", ""))
                        # Standard metrics we want to exclude
                        excluded_keywords = [
                            "ter", "yield", "volatility", "drawdown", "return", "risk", 
                            "ratio", "sharpe", "alpha", "beta", "standard_deviation",
                            "inception", "fund_size", "currency", "distribution", "policy",
                            "replication", "method", "domicile", "category", "listing"
                        ]
                        if not any(kw in k for kw in excluded_keywords):
                            # If it's a company name (usually has multiple words or is recognized)
                            if len(k) > 3 and ("_" in k or any(c.isupper() for c in k)):
                                holdings_list.append({
                                    "name": k.replace("_", " ").title(),
                                    "symbol": "",
                                    "weight": weight
                                })
                    except:
                        pass

        # 3. Get ETF Name from H1
        h1 = soup.find("h1")
        if h1:
            metrics["etfName"] = h1.get_text(strip=True).split("|")[0].strip()

        result = {
            "source": self.source_name,
            "market": market,
            "ticker_requested": ticker,
            "ticker_used": ticker_to_use,
            "isin": isin,
            "url": url,
            "title": {
                "ticker": ticker_to_use,
                "company": metrics.get("etfName", "")
            },
            "metrics": {
                "holdings": holdings_list,
                **metrics
            }
        }
        return result

    def search_ticker(self, query: str, market: str) -> List[Dict[str, Any]]:
        """Search JustETF for a ticker and return matches with ISIN."""
        # Use the find-etf endpoint which is what the web UI uses
        search_url = f"{self.BASE_URL}/en/find-etf.html?groupField=none&sortField=name&sortOrder=asc&search={query}"
        response = self.session.get(search_url, timeout=15)
        
        # If redirected to a profile page (sometimes happens if unique ISIN)
        if "isin=" in response.url:
            isin_match = re.search(r"isin=([A-Z0-9]+)", response.url)
            if isin_match:
                isin = isin_match.group(1)
                return [{"ticker": query, "isin": isin, "name": query, "exchange": market}]

        # Otherwise parse results page
        soup = BeautifulSoup(response.text, "lxml")
        results = []
        
        # In the results table, ISIN is often in a data attribute or in the link
        links = soup.find_all("a", href=re.compile(r"isin=[A-Z0-9]+"))
        for link in links:
            href = link.get("href")
            isin_match = re.search(r"isin=([A-Z0-9]+)", href)
            if isin_match:
                isin = isin_match.group(1)
                name = link.get_text(strip=True)
                if isin and isin not in [r["isin"] for r in results]:
                    results.append({
                        "ticker": query,
                        "isin": isin,
                        "name": name,
                        "exchange": market
                    })
        
        return results
