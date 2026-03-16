from typing import Any, Dict

from scraper.base import BaseScraper


class GoogleFinanceScraper(BaseScraper):
    source_name = "google_finance"

    def scrape_quote(self, ticker: str, market: str) -> Dict[str, Any]:
        raise NotImplementedError(
            "Google Finance ainda não foi implementado nesta versão."
        )