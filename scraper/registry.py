from scraper.euronext import EuronextScraper
from scraper.finviz import FinvizScraper
from scraper.google_finance import GoogleFinanceScraper
from scraper.yahoo import YahooFinanceScraper
from scraper.justetf import JustETFScraper
# from scraper.intelligent_router import detect_asset_type_and_market, select_sources, scrape_multi_source

SCRAPER_REGISTRY = {
    "finviz": FinvizScraper(),
    "yahoo": YahooFinanceScraper(),
    "google_finance": GoogleFinanceScraper(),
    "euronext": EuronextScraper(),
    "justetf": JustETFScraper(),
}

SUPPORTED_MARKETS = {
    "US": "Americano",
    "EU": "Europeu",
    "PT": "Português",
    "BR": "Brasileiro",
    "GLOBAL": "Global/Crypto",
}
