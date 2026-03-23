import json
from scraper.registry import SCRAPER_REGISTRY

scraper = SCRAPER_REGISTRY['justetf']
result = scraper.scrape_quote('XDWF', 'EU')

with open('tmp/price_debug.txt', 'w', encoding='utf-8') as f:
    f.write(f"Title data: {result.get('title')}\n\n")
    metrics = result.get('metrics', {})
    f.write(f"Metrics count: {len(metrics)}\n")
    
    for k, v in metrics.items():
        if 'eur' in k.lower() or 'usd' in k.lower() or 'quote' in k.lower() or 'price' in k.lower() or 'nav' in k.lower():
            f.write(f"MATCH: {k} = {v}\n")
        
        try:
            val = float(str(v).replace('EUR', '').replace('USD', '').strip())
            if 30 < val < 50:
                f.write(f"POTENTIAL PRICE: {k} = {v}\n")
        except Exception:
            pass
