#!/usr/bin/env python3
"""
Test batch scraping for user tickers using improved intelligent router.
Handles mixed stocks/ETFs/EU/US/crypto with JustETF/Finviz optimizations.
"""

import json
from pathlib import Path
from datetime import datetime
from scraper.intelligent_router import scrape_multi_source
from scraper.transformer import normalize_tickers_from_text, flatten_scrape_result, build_ordered_columns

USER_TICKERS = """
AMD GOOGL MO AXP AMT LYM9:FRA:EUR AAPL ASML AVAX EPA:CS AXON ELI:BCP SAN BAC BMW BTC BNP ADA CVX C KO CORT ELI:CTT DOGE EDPR EDP BIT:ENEL ETH XOM F GALP GFS IBE IBS QQQ IXC EUNK:GER:EUR LON:XDWF QDVF IUIT IYM ELI:JMT LMT ETR:MBG META MSFT MSTR ELI:EGL NDAQ NESN NEM NOC NOS NVO NVDA PEP PFE PLD RENE RHM SOL ELI:SON BIT:STLAM TSLA TTE URI DAVV:FRA:EUR LON:G2X OIH XETR:VVMX LON:JEDI VGK VUAA VZ V LON:VOD VOW3 WBD LSE:VZLC XRP DRH G2X QDVE XDWF QDVK IU5C 2B7D
""".strip()

if __name__ == "__main__":
    print("Testing improved ETF scraping (JustETF/Finviz) on user tickers...")
    
    tickers = normalize_tickers_from_text(USER_TICKERS)
    print(f"Normalized {len(tickers)} unique tickers: {tickers[:10]}...")
    
    rows = []
    errors = []
    
    for i, ticker in enumerate(tickers):
        print(f"\n[{i+1}/{len(tickers)}] Scraping {ticker}...")
        if i > 0:
            import time
            time.sleep(1.5)
        try:
            result = scrape_multi_source(ticker)
            flat_row = flatten_scrape_result(result)
            rows.append(flat_row)
            print(f"✓ Success: {result.get('asset_type')}/{result.get('detected_market')} from {result.get('sources_used')}")
        except Exception as exc:
            errors.append({"ticker": ticker, "error": str(exc)})
            print(f"✗ Error: {exc}")
    
    print(f"\nSummary: {len(rows)} success, {len(errors)} errors")
    
    columns = build_ordered_columns(rows)
    
    batch_result = {
        "test_batch": True,
        "tickers": tickers,
        "success": len(rows),
        "errors": len(errors),
        "rows": rows,
        "columns": columns,
        "timestamp": datetime.now().isoformat()
    }
    
    # Save results
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outfile = output_dir / f"test_user_tickers_batch_{timestamp}.json"
    
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(batch_result, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {outfile}")
    if errors:
        print("Errors:", [e['ticker'] for e in errors])
    
    print("Test complete! Check data/raw/ for JSON output.")

