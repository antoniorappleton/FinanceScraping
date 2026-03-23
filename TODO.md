# Price and Intervals Automation (yfinance Robust Fallback)
Status: In Progress

## Approved Plan Steps:

✅ 1. Update requirements.txt: Add 'yfinance==0.2.43'
✅ 2. Enhance scraper/yahoo.py: Add yfinance API fetch + compute priceChange_1w/1m/1y from history()
✅ 3. Update cron_scraper.py: Try yahoo yfinance first → use computed data in payload + priceChange_1m; fallback to HTML scrape
✅ 4. Update local_scheduler.py: Add --interval-minutes for 10-min fast syncs
✅ 5. Create .github/workflows/market-scrape.yml: GitHub cron every 10min (fast mode)
✅ 6. Install: pip install yfinance
✅ 7. Test: python cron_scraper.py --mode=fast → verify Firestore acoesDividendos has yf data/intervals
✅ 8. Update local_scheduler.py --interval-minutes=10 & run
9. ✅ attempt_completion
