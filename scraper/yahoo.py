from typing import Any, Dict

from scraper.base import BaseScraper


class YahooFinanceScraper(BaseScraper):
    source_name = "yahoo"

    def scrape_quote(self, ticker: str, market: str) -> Dict[str, Any]:
        raise NotImplementedError(
            "Yahoo Finance ainda não foi implementado nesta versão."
        )