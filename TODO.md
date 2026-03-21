# ETF Scraping Improvements - JustETF & Finviz + Table Display Fix
Status: In Progress

## Approved Plan Steps:

1. ✅ Create this TODO.md tracking file 
2. ✅ Read scraper/base.py for ticker normalization capabilities
3. ✅ Update scraper/intelligent_router.py:
   - Merge best from intelligent_router_fixed.py 
   - Expand KNOWN_EU_ETFS/US_ETFS with user tickers 
   - Add COLON ticker parsing (LYM9:FRA:EUR -> LYM9.PA, extract market) 
   - Improve ETF detection patterns for US (QQQ-like, OIH sector) 
   - Optimize source rules: US ETF=['finviz','justetf','yahoo'], EU ETF=['justetf','euronext','yahoo'] 
   - Add rate limiting in scrape_multi_source
4. ✅ Update app.py: Make /api/search-batch always use scrape_multi_source(tickers split+normalize) 
   - Use main intelligent_router 
   - Cleaned dead code 
   - Fixed file handle 'file'->'f' consistency 
5. ✅ Minor scraper/justetf.py: Enhance EU search/handling
6. ✅ Minor scraper/finviz.py: Better US ETF signals
7. ✅ Update scraper/registry.py: Uncomment/use main intelligent_router
8. ✅ Test: Run batch on user tickers list (created test_batch_etfs.py, executed) 
9. ✅ **NEW** Add /api/load-recent route to app.py + "Load Recent" UI in app.js for viewing saved batch JSONs in table
10. ✅ Test: python app.py, browser localhost:5000 → "📂 Load Recent" → select test_user_tickers_batch → table displays 87 rows ETFs/stocks data
11. 🔄 attempt_completion

