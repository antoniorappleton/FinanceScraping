from scraper.finviz import FinvizScraper
from scraper.google_finance import GoogleFinanceScraper
from scraper.yahoo import YahooFinanceScraper


SCRAPER_REGISTRY = {
    "finviz": FinvizScraper(),
    "yahoo": YahooFinanceScraper(),
    "google_finance": GoogleFinanceScraper(),
}

SUPPORTED_MARKETS = {
    "US": "Americano",
    "EU": "Europeu",
    "PT": "Português",
    "BR": "Brasileiro",
}