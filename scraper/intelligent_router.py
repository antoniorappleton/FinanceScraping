from typing import Dict, List, Tuple, Any
import re
import time
from scraper.registry import SCRAPER_REGISTRY
from scraper.base import BaseScraper, MARKET_SUFFIXES

DETECT_PATTERNS = {
    'crypto': r'^[A-Z]+-[A-Z]+$',
    'etf': r'\.(E[ST]|A[CT])\b|QQQ|IXC|VGK|OIH|VU|IWDA|AGG',
}

# Expanded from user list and tests
KNOWN_EU_ETFS = {
    'G2X', 'QDVE', 'XDWF', 'QDVK', 'IU5C', '2B7D', 'VUSA', 'VUAA', 'VUSD', 'DAVV', 'QDVF', 'IUIT', 'IYM', 'GRID'
}
KNOWN_US_ETFS = {
    'QQQ', 'IXC', 'VGK', 'OIH', 'EUNK', 'XDWF', 'QDVF', 'IUIT', 'IYM'
}

MARKET_MAP = {
    'FRA': 'EU', 'PA': 'EU', 'DE': 'EU', 'LON': 'UK', 'LSE': 'UK', 'ELI': 'PT', 'BIT': 'IT', 'ETR': 'EU',
    'EPA': 'EU', 'XETR': 'EU', 'GER': 'EU', 'IE': 'EU'
}

def parse_ticker_market(ticker: str) -> Tuple[str, str]:
    """Parse ticker:market[:cur] -> normalized_ticker, market."""
    parts = re.split(r'[:]', ticker, maxsplit=2)
    clean_ticker = parts[0].strip().upper()
    detected_market = 'US'
    
    if len(parts) > 1:
        exch = parts[1].strip().upper()
        detected_market = MARKET_MAP.get(exch, 'EU' if exch in ['FRA','PA','DE'] else 'GLOBAL')
    
    # Normalize suffix if needed
    norm_ticker = BaseScraper.normalize_ticker(clean_ticker, detected_market)
    
    return norm_ticker, detected_market

def detect_asset_type_and_market(ticker: str) -> Tuple[str, str]:
    """Enhanced detection with COLON parsing."""
    ticker_upper = ticker.strip().upper()
    
    # Parse complex formats first
    parsed_ticker, market = parse_ticker_market(ticker_upper)
    
    # Known ETFs
    if parsed_ticker in KNOWN_EU_ETFS:
        print(f"DETECT [EU_ETF]: {ticker_upper} -> etf/{market}")
        return 'etf', 'EU'
    if parsed_ticker in KNOWN_US_ETFS:
        print(f"DETECT [US_ETF]: {ticker_upper} -> etf/US")
        return 'etf', 'US'
    
    # Crypto
    if re.match(DETECT_PATTERNS['crypto'], parsed_ticker):
        print(f"DETECT [CRYPTO]: {ticker_upper} -> crypto/GLOBAL")
        return 'crypto', 'GLOBAL'
    
    # ETF heuristics improved
    is_etf = bool(re.search(DETECT_PATTERNS['etf'], parsed_ticker))
    is_short_eu = len(parsed_ticker) <= 6 and market in ['EU', 'PT', 'UK']
    
    asset_type = 'etf' if (is_etf or is_short_eu) else 'stock'
    
    print(f"DETECT: {ticker_upper} -> {asset_type}/{market} (parsed={parsed_ticker})")
    return asset_type, market

def select_sources(asset_type: str, market: str) -> List[str]:
    """Optimized rules: finviz first US ETF/stock, justetf first EU ETF."""
    rules = {
        ('stock', 'US'): ['finviz', 'yahoo', 'google_finance'],
        ('stock', 'PT'): ['euronext', 'yahoo', 'google_finance'],
        ('stock', 'EU'): ['euronext', 'yahoo', 'ft_markets', 'justetf'],
        ('stock', 'BR'): ['yahoo', 'google_finance'],
        ('stock', 'UK'): ['yahoo', 'euronext', 'ft_markets', 'justetf'],
        ('etf', 'EU'): ['justetf', 'ft_markets', 'euronext', 'yahoo', 'google_finance'],
        ('etf', 'US'): ['finviz', 'justetf', 'yahoo', 'ft_markets'],
        ('etf', 'GLOBAL'): ['justetf', 'ft_markets', 'yahoo'],
        ('crypto', 'GLOBAL'): ['yahoo', 'google_finance'],
    }
    key = (asset_type, market)
    sources = rules.get(key, ['yahoo'])
    available = [s for s in sources if s in SCRAPER_REGISTRY]
    print(f"SOURCES for {asset_type}/{market}: {available}")
    return available

def consolidate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge multi-source data."""
    if not results:
        return {}
    
    consolidated = {
        'sources_used': [r.get('source', 'unknown') for r in results],
        'markets': list(set(r.get('market', []) for r in results)),
        'ticker_used': results[0].get('ticker_used') or results[0].get('ticker_requested'),
        'title': results[0].get('title', {}),
        'metrics': {},
        'urls': [r.get('url') for r in results if r.get('url')],
    }
    
    all_metrics = {}
    for r in results:
        for k, v in r.get('metrics', {}).items():
            if k not in all_metrics or (all_metrics[k] is None or all_metrics[k] == ''):
                all_metrics[k] = v
    
    consolidated['metrics'] = all_metrics
    return consolidated

def scrape_multi_source(ticker: str, market: str = None, sources: List[str] = None) -> Dict[str, Any]:
    """Intelligent scraping with rate limiting."""
    if market is None:
        asset_type, market = detect_asset_type_and_market(ticker)
    else:
        asset_type = 'stock'
    
    if sources is None:
        sources = select_sources(asset_type, market)
    
    results = []
    for i, source_name in enumerate(sources):
        if source_name not in SCRAPER_REGISTRY:
            continue
        scraper = SCRAPER_REGISTRY[source_name]
        try:
            result = scraper.scrape_quote(ticker=ticker, market=market)
            result['source'] = source_name
            results.append(result)
            print(f"✓ {source_name} succeeded for {ticker}")
            if i < len(sources) - 1:  # Delay between sources
                time.sleep(1.0)
        except Exception as e:
            print(f"✗ {source_name} failed for {ticker}: {e}")
            continue
    
    print(f"Scraping {ticker}: {asset_type}/{market}, tried {sources}, got {len(results)} results")
    return {
        **consolidate_results(results),
        'asset_type': asset_type,
        'detected_market': market,
        'selected_sources': sources,
        'results_count': len(results),
    }

