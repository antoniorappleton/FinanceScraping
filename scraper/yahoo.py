import re
import time
from typing import Any, Dict, List, Optional

import requests
import yfinance as yf
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

    def _get_yfinance_data(self, ticker: str, market: str) -> Optional[Dict[str, Any]]:
        """Robust yfinance API fetch + computed intervals."""
        try:
            normalized_ticker = BaseScraper.normalize_ticker(ticker, market)
            stock = yf.Ticker(normalized_ticker)
            
            # Current data
            info = stock.info
            hist = stock.history(period="2y", interval="1d")  # Daily for changes
            
            if hist.empty or len(hist) < 5:
                return None
            
            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or hist['Close'].iloc[-1]
            
            # Compute intervals (trading days approx)
            changes = {}
            periods = {
                '1w': 5,   # 1 week ~5 trading days
                '1m': 21,  # 1 month ~21
                '1y': 252  # 1 year ~252
            }
            
            for interval, days_back in periods.items():
                if len(hist) >= days_back + 1:
                    past_close = hist['Close'].iloc[-(days_back + 1)]
                    change_pct = ((current_price - past_close) / past_close) * 100
                    changes[f'priceChange_{interval}'] = round(change_pct, 2)
            
            # Fallback if no info fields
            ticker_used = normalized_ticker
            company_name = info.get('longName') or info.get('shortName') or normalized_ticker
            
            data = {
                'yf_success': True,
                'valorStock': float(current_price),
                **changes,
                'marketCap': info.get('marketCap'),
                'pe': info.get('trailingPE') or info.get('forwardPE'),
                'yield': info.get('dividendYield'),
                'company': company_name,
                'ticker': ticker_used
            }
            
            # Add all info keys cleaned
            for k, v in info.items():
                if isinstance(v, (int, float)):
                    data[f'info_{k.lower().replace(" ", "_")}'] = v
            
            return data
            
        except Exception as e:
            print(f"yfinance error for {ticker}: {e}")
            return None

    def search_ticker(self, query: str, market: str) -> List[Dict[str, Any]]:
        results = []
        normalized = BaseScraper.normalize_ticker(query, market)
        
        # Use yfinance for search too
        yf_data = self._get_yfinance_data(normalized, market)
        if yf_data:
            results.append({
                "ticker": yf_data['ticker'],
                "name": yf_data['company'],
                "exchange": market
            })
        
        if not results:
            # Fallback to HTML search
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
        
        return results[:5]

    def scrape_quote(self, ticker: str, market: str) -> Dict[str, Any]:
        """Try yfinance first (robust), fallback to HTML scrape."""
        # Primary: yfinance
        yf_data = self._get_yfinance_data(ticker, market)
        if yf_data:
            return {
                "source": self.source_name,
                "method": "yfinance",
                "market": market,
                "ticker_requested": ticker,
                "ticker_used": yf_data['ticker'],
                "url": f"{self.BASE_URL}/{yf_data['ticker']}",
                "title": {
                    "ticker": yf_data['ticker'],
                    "company": yf_data['company']
                },
                "metrics": yf_data
            }
        
        # Fallback: HTML scrape (existing logic)
        normalized_ticker = BaseScraper.normalize_ticker(ticker, market)
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
            html = self._get_html(normalized_ticker)
            soup = BeautifulSoup(html, "lxml")
            summary = self._parse_summary(soup)
            if not summary.get("metrics"):
                raise ValueError("No data found for ticker in Yahoo Finance")
            ticker_used = normalized_ticker

        return {
            "source": self.source_name,
            "method": "html_scrape",
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
