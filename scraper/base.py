from abc import ABC, abstractmethod
from typing import Any, Dict, List

MARKET_SUFFIXES = {
    "US": "",
    "EU": ".DE",  # Common for Germany, adjust per exact EU ticker
    "PT": ".LS",  # Lisbon
    "BR": ".SA",  # B3 Brazil
}


class BaseScraper(ABC):
    source_name = "base"

    @classmethod
    def normalize_ticker(cls, ticker: str, market: str) -> str:
        """Normalize ticker with market-specific suffix if not present."""
        suffix = MARKET_SUFFIXES.get(market, "")
        ticker = ticker.strip().upper()
        if suffix and not ticker.endswith(suffix):
            ticker += suffix
        return ticker

    @abstractmethod
    def scrape_quote(self, ticker: str, market: str) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def search_ticker(self, query: str, market: str) -> List[Dict[str, Any]]:
        """
        Search for tickers matching query in market.
        Returns list of [{'ticker': str, 'name': str, 'exchange': str}, ...]
        """
        raise NotImplementedError
