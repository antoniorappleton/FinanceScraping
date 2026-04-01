#!/usr/bin/env python3
"""
Batch scrape justETF data for specific EU ETFs.
Retrieves all available profile metrics for each.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from scraper.registry import SCRAPER_REGISTRY
from scraper.intelligent_router_fixed import scrape_multi_source  # Fallback option

ETFS = ['G2X', 'QDVE', 'XDWF', 'QDVK', 'IU5C', '2B7D']
JUSTETF_SCRAPER = SCRAPER_REGISTRY['justetf']
OUTPUT_DIR = Path('data/raw')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def scrape_etf_data(scraper, ticker: str, market: str = 'EU') -> Dict[str, Any]:
    try:
        print(f'Scraping {ticker} from justETF...')
        result = scraper.scrape_quote(ticker=ticker, market=market)
        print(f'✓ {ticker}: Success, {len(result.get("metrics", {}))} metrics')
        return result
    except Exception as e:
        print(f'✗ {ticker}: justETF failed - {e}')
        # Fallback to multi-source
        try:
            print(f'  Trying multi-source fallback...')
            result = scrape_multi_source(ticker)
            print(f'✓ {ticker}: Multi-source fallback, sources: {result.get("sources_used")}')
            return result
        except Exception as e2:
            print(f'✗ {ticker}: All failed - {e2}')
            return {'ticker': ticker, 'error': str(e2), 'source': 'failed'}

if __name__ == '__main__':
    results = []
    for i, ticker in enumerate(ETFS):
        if i > 0:
            import time
            time.sleep(2.0)  # Rate limit
        result = scrape_etf_data(JUSTETF_SCRAPER, ticker)
        results.append(result)

    # Save batch
    batch = {
        'etfs': ETFS,
        'batch_timestamp': datetime.now().isoformat(),
        'results': results
    }
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = OUTPUT_DIR / f'justetf_etfs_batch_{timestamp}.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(batch, f, indent=2, ensure_ascii=False)
    print(f'\nBatch saved to: {output_file}')
    print(f'Success: {sum(1 for r in results if "error" not in r)} / {len(ETFS)}')
