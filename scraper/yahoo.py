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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://finance.yahoo.com",
            "Referer": "https://finance.yahoo.com",
        })
        # Try to establish a session by visiting the main page
        try:
            self.session.get("https://finance.yahoo.com", timeout=10)
        except:
            pass

    def _clean_text(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return re.sub(r"\s+", " ", value).strip()

    def _get_html(self, ticker: str) -> str:
        url = f"{self.BASE_URL}/{ticker}" # No trailing slash
        response = self.session.get(url, timeout=20)
        response.raise_for_status()
        time.sleep(self.pause_seconds)
        return response.text

    def _get_stats_from_html(self, ticker: str) -> Dict[str, Any]:
        """Scrape key-statistics page for SMAs when API fails."""
        stats = {}
        try:
            url = f"{self.BASE_URL}/{ticker}/key-statistics"
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return stats
            
            soup = BeautifulSoup(response.text, "lxml")
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                for row in rows:
                    tds = row.find_all("td")
                    if len(tds) >= 2:
                        key = self._clean_text(tds[0].get_text())
                        val = self._clean_text(tds[1].get_text())
                        if "50-Day Moving Average" in key:
                            stats["sma50"] = val
                        elif "200-Day Moving Average" in key:
                            stats["sma200"] = val
                        elif "Market Cap" in key:
                            stats["marketCap"] = val
        except Exception as e:
            print(f"Error scraping stats HTML for {ticker}: {e}")
        return stats

    def _parse_summary(self, soup: BeautifulSoup, ticker: str = "") -> Dict[str, str]:
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
            
            # Current data - split to be more resilient
            info = {}
            try:
                info = stock.info
            except Exception as e:
                print(f"yfinance info error for {ticker}: {e}")
            
            hist = None
            try:
                hist = stock.history(period="2y", interval="1d")
            except Exception as e:
                print(f"yfinance history error for {ticker}: {e}")
            
            if hist is None or hist.empty:
                # If both info and hist fail, and hist is really needed for price
                if not info or ('currentPrice' not in info and 'regularMarketPrice' not in info):
                    return None
                current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            else:
                current_price = info.get('currentPrice') or info.get('regularMarketPrice') or hist['Close'].iloc[-1]
            
            # 2. Compute SMAs from history (Source of Truth)
            sma20_calc = None
            sma50_calc = None
            sma100_calc = None
            sma200_calc = None
            
            if len(hist) >= 20:
                sma20_calc = float(hist['Close'].rolling(window=20).mean().iloc[-1])
            if len(hist) >= 50:
                sma50_calc = float(hist['Close'].rolling(window=50).mean().iloc[-1])
            if len(hist) >= 100:
                sma100_calc = float(hist['Close'].rolling(window=100).mean().iloc[-1])
            if len(hist) >= 200:
                sma200_calc = float(hist['Close'].rolling(window=200).mean().iloc[-1])

            # 2b. Compute Volume SMA
            sma_vol20 = None
            if 'Volume' in hist.columns and len(hist) >= 20:
                sma_vol20 = float(hist['Volume'].rolling(window=20).mean().iloc[-1])

            # 2c. Trend Signals
            above_sma50 = current_price > sma50_calc if sma50_calc else None
            above_sma200 = current_price > sma200_calc if sma200_calc else None
            golden_cross = sma50_calc > sma200_calc if (sma50_calc and sma200_calc) else None

            # 3. Compute intervals (trading days approx)
            changes = {}
            periods = {
                '1w': 5,   # 1 week ~5 trading days
                '1m': 21,  # 1 month ~21
                '1y': 252  # 1 year ~252
            }
            
            if hist is not None and not hist.empty:
                for interval, days_back in periods.items():
                    if len(hist) >= days_back + 1:
                        past_close = hist['Close'].iloc[-(days_back + 1)]
                        change_pct = ((current_price - past_close) / past_close) * 100
                        changes[f'priceChange_{interval}'] = round(change_pct, 2)
            
            # 4. Compute RSI from history
            rsi = None
            try:
                if hist is not None and len(hist) >= 15:
                    delta = hist['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi_series = 100 - (100 / (1 + rs))
                    rsi = round(float(rsi_series.iloc[-1]), 2)
            except:
                pass

            # --- Technical Indicators: SMA fallback ---
            sma50 = info.get('fiftyDayAverage')
            sma200 = info.get('twoHundredDayAverage')
            try:
                if (sma50 is None or sma50 == 0) and hist is not None and len(hist) >= 50:
                    sma50 = round(hist['Close'].tail(50).mean(), 4)
                if (sma200 is None or sma200 == 0) and hist is not None and len(hist) >= 200:
                    sma200 = round(hist['Close'].tail(200).mean(), 4)
            except:
                pass

            # Fallback if no info fields
            ticker_used = normalized_ticker
            company_name = info.get('longName') or info.get('shortName') or normalized_ticker
            
            # Map common metrics with fallbacks
            pe = info.get('trailingPE') or info.get('forwardPE')
            ev_ebitda = info.get('enterpriseToEbitda')
            dividend_yield = info.get('dividendYield') or info.get('trailingAnnualDividendYield')
            
            data = {
                'yf_success': True,
                'valorStock': current_price,
                **changes,
                'marketCap': info.get('marketCap'),
                'pe': pe,
                'ev_ebitda': ev_ebitda,
                'yield': dividend_yield,
                'rsi': rsi,
                'company': company_name,
                'ticker': normalized_ticker,
                'roe': info.get('returnOnEquity'),
                'roa': info.get('returnOnAssets'),
                'roic': info.get('returnOnCapital'), # Some tickets have this
                'sma50': sma50,
                'sma200': sma200,
            }
            
            # Add all info keys cleaned
            for k, v in info.items():
                if isinstance(v, (int, float)):
                    key = k.lower().replace(" ", "_")
                    if f'info_{key}' not in data:
                        data[f'info_{key}'] = v
            
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
                summary = self._parse_summary(soup, normalized)
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
        # Normalize specifically for Yahoo
        norm_ticker = ticker.strip().upper()
        if ":" in norm_ticker:
            # Handle ELI:BCP -> BCP.LS, EPA:CS -> CS.PA, etc.
            parts = norm_ticker.split(":")
            prefix = parts[0]
            symbol = parts[1]
            if prefix == "ELI":
                norm_ticker = f"{symbol}.LS"
            elif prefix == "EPA":
                norm_ticker = f"{symbol}.PA"
            elif prefix in ["FRA", "GER", "XETR"]:
                norm_ticker = f"{symbol}.DE"
            elif prefix == "IE":
                norm_ticker = f"{symbol}.IR"
            elif prefix == "LON":
                norm_ticker = f"{symbol}.L"
            elif prefix == "AMS":
                norm_ticker = f"{symbol}.AS"
            elif prefix == "MIL":
                norm_ticker = f"{symbol}.MI"
            elif prefix == "MAD":
                norm_ticker = f"{symbol}.MC"
            elif prefix == "SWI":
                norm_ticker = f"{symbol}.SW"
                
        # Primary: yfinance
        yf_data = self._get_yfinance_data(norm_ticker, market)
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
        ticker_to_try = norm_ticker if ":" not in norm_ticker else normalized_ticker
        
        try:
            html = self._get_html(ticker_to_try)
            soup = BeautifulSoup(html, "lxml")
            summary = self._parse_summary(soup, ticker_to_try)
            
            # Try to get SMAs from statistics page HTML as fallback
            html_stats = self._get_stats_from_html(ticker_to_try)
            if html_stats:
                if "metrics" not in summary: summary["metrics"] = {}
                summary["metrics"].update(html_stats)
                
            if summary.get("metrics"):
                ticker_used = ticker_to_try
            else:
                raise ValueError("No metrics")
        except:
            html = self._get_html(normalized_ticker)
            soup = BeautifulSoup(html, "lxml")
            summary = self._parse_summary(soup, normalized_ticker)
            
            html_stats = self._get_stats_from_html(normalized_ticker)
            if html_stats:
                if "metrics" not in summary: summary["metrics"] = {}
                summary["metrics"].update(html_stats)

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
