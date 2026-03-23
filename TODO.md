# ETF Portfolio + Profit Maximization Algorithm
Status: In Progress

## Approved Plan Implementation Steps:

✅ 1. Create this TODO.md file

**2. Edit app.py**  
   - Add `/api/analyze-etf?ticker=` endpoint: intelligent scrape → compute enhanced algo (annualized returns, weighted score [25% ann3y +25% ann5y +20% rpr3y +15% mom6m +15%(1-vol)], risk_score=0.5*vol1y+0.5*|dd3y|, signals: >0.75 STRONG BUY / 0.6-0.75 BUY / 0.45-0.6 HOLD / <0.45 AVOID; downgrade if 6m<0; trend if 3m/6m<0; alloc_pct=score*(1-risk)*20 cap; div warnings sector>25%/geo>30%)  
   - Add `/portfolio?ticker=` route rendering portfolio.html w/ data  

**3. Create templates/portfolio.html**  
   - Sections: Perf Table (periods annualized*), Risk Metrics cards, BIG Signal Badge, Alloc Suggestion, Holdings Pie Chart (Chart.js, top: telecom/meta/alphabet/netflix...), Fund Facts grid, Trend indicator  

**4. Create static/portfolio.js**  
   - JS to fetch `/api/analyze-etf`, render tables/charts (perf bar/line, holdings pie), badges w/ colors  

**5. Edit static/app.js**  
   - Add "Portfolio" button/nav linking to `/portfolio?ticker=IU5C`  

**6. Edit static/style.css**  
   - Styles: .portfolio-grid, .signal-badge (green=#10b981/red=#ef4444/amber=#f59e0b), .risk-card, .pie-chart-container  

**7. Test**  
   - `python app.py`  
   - Visit http://localhost:5000/portfolio?ticker=IU5C  
   - Verify: Scrapes IU5C data, shows ~"BUY" signal (rpr1y=0.95, 3y=1.54, low recent dip), holdings pie (Meta~20%), alloc~12%, etc.  
   - ✅ attempt_completion w/ demo command  

## Expected Output for IU5C Sample Data:  
- Score ~0.70 (ann3y~0.37, ann5y~0.25, good rpr/vol)  
- Signal: BUY  
- Risk: Medium  
- Trend: Neutral (6m=-1.16% dip but long strong)  
- Alloc: 12-15%  
- Holdings: Telecom 98%, Meta 20%, Alphabet 18%  

Next: Edit app.py
