from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseScraper(ABC):
    source_name = "base"

    @abstractmethod
    def scrape_quote(self, ticker: str, market: str) -> Dict[str, Any]:
        raise NotImplementedError