from typing import Dict, List, Tuple, Any
import re
from scraper.registry import SCRAPER_REGISTRY
from scraper.base import BaseScraper

DETECT_PATTERNS = {
    'crypto': r'^[A-Z]+-[A-Z]+$',
'etf': r'.*(E[ST]|A[CT]).*',
}

MARKET_FROM_SUFFIX = {
    '.LS': 'PT',
    '.SA': 'BR',
    '.DE': 'EU',
    '.PA': 'EU',
    # Add more
}

def detect_asset_type_and_market(ticker: str) -> Tuple[str, str]:
    """Detect asset_type ('stock', 'etf', 'crypto') and market ('US','EU','PT','BR','GLOBAL')."""
    ticker_upper = ticker.strip().upper()
    
    # Crypto first (Yahoo format)
    if re.match(DETECT_PATTERNS['crypto'], ticker_upper):
        return 'crypto', 'GLOBAL'
    
    # Market from suffix
    market = 'US'  # default
    for suffix, m in MARKET_FROM_SUFFIX.items():
        if ticker_upper.endswith(suffix):
            market = m
            break
    
    # ETF heuristic: Add known UCITS ETFs like VUSA, improve detection
    KNOWN_EU_ETFS = {'G2X', 'QDVE', 'XDWF', 'QDVK', 'IU5C', '2B7D', 'VUSA', 'VUAA', 'VUSD', 'GRID'}
    if ticker_upper in KNOWN_EU_ETFS:
        return 'etf', 'EU'
    if re.search(r'^(VU|IWDA|AGG)', ticker_upper):
        return 'etf', 'EU'
    if market != 'US' or re.search(r'\.(L|DE|PA|FP|AS)', ticker_upper):
        return 'etf', market
    
    return 'stock', market

def select_sources(asset_type: str, market: str) -> List[str]:
    """Select best sources per rules."""
    rules = {
        ('stock', 'US'): ['finviz', 'yahoo', 'google_finance'],
        ('stock', 'PT'): ['euronext', 'yahoo', 'google_finance'],
        ('stock', 'EU'): ['euronext', 'yahoo', 'justetf'],
        ('stock', 'BR'): ['yahoo', 'google_finance'],
        ('etf', 'EU'): ['justetf', 'yahoo', 'euronext', 'google_finance'],
        ('etf', 'US'): ['justetf', 'yahoo', 'finviz'],
        ('etf', 'GLOBAL'): ['justetf', 'yahoo'],
        ('crypto', 'GLOBAL'): ['yahoo', 'google_finance'],
    }
    key = (asset_type, market)
    available_sources = [s for s in rules.get(key, ['yahoo']) if s in SCRAPER_REGISTRY]
    if len(available_sources) == 0:
        print(f"Warning: No available sources for {asset_type}/{market}, falling back to ['yahoo']")
        return ['yahoo']
    print(f"Selected sources for {asset_type}/{market}: {available_sources}")
    return available_sources

def consolidate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Consolidate multi-source results: union metrics, first non-empty."""
    if not results:
        return {}
    
    consolidated = {
        'sources_used': [r.get('source') for r in results if r.get('source')],
        'markets': list(set(r.get('market', []) for r in results)),
        'ticker_used': results[0].get('ticker_used', results[0].get('ticker_requested')),
        'title': results[0].get('title', {}),
        'metrics': {},
        'urls': [r.get('url') for r in results if r.get('url')],
    }
    
    # Union all metrics, take first non-empty value per key
    all_metrics = {}
    for r in results:
        for k, v in r.get('metrics', {}).items():
            if k not in all_metrics or not all_metrics[k]:
                all_metrics[k] = v
    
    consolidated['metrics'] = all_metrics
    return consolidated

def scrape_multi_source(ticker: str, market: str = None, sources: List[str] = None) -> Dict[str, Any]:
    """Auto-detect or use provided, scrape multi-source, consolidate."""
    if market is None:
        asset_type, market = detect_asset_type_and_market(ticker)
    else:
        asset_type = 'stock'  # default if not auto
    
    if sources is None:
        sources = select_sources(asset_type, market)
    
    results = []
    for source_name in sources:
        if source_name not in SCRAPER_REGISTRY:
            continue
        scraper = SCRAPER_REGISTRY[source_name]
        try:
            result = scraper.scrape_quote(ticker=ticker, market=market)
            result['source'] = source_name  # Ensure source key
            results.append(result)
        except Exception as e:
            print(f"Failed {source_name}: {e}")
            continue
    
    print(f"Scraping {ticker}: type={asset_type}, market={market}, sources={sources}, results from {len(results)} sources")
    return {
        **consolidate_results(results),
        'asset_type': asset_type,
        'detected_market': market,
        'selected_sources': sources,
    }

