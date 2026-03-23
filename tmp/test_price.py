import json
from scraper.registry import SCRAPER_REGISTRY

scraper = SCRAPER_REGISTRY['justetf']
result = scraper.scrape_quote('XDWF', 'EU')

print(f"Title data: {result.get('title')}")
metrics = result.get('metrics', {})
print("Metrics keys:", list(metrics.keys()))

for k, v in metrics.items():
    if 'eur' in k.lower() or 'usd' in k.lower() or 'quote' in k.lower() or 'price' in k.lower() or 'nav' in k.lower():
        print(f"  {k}: {v}")
    # Print potential values that could be exactly the price
    try:
        if 30 < float(str(v).replace('EUR', '').replace('USD', '').strip()) < 50:
            print(f"  [Potential Price] {k}: {v}")
    except:
        pass
