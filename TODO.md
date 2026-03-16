o # Fix Market Scraper Errors (405, JSON, Dropdowns)

**Status:** ✅ Complete

## Steps:
- [x] **Step 1:** Stop VSCode Live Server (Ctrl+C in its terminal or VSCode: Ctrl+Shift+P > Live Server: Stop Live Server).
- [x] **Step 2:** Run Flask backend: `python app.py` (in project root).
- [x] **Step 3:** Open browser: http://127.0.0.1:5000
- [x] **Step 4:** Verify dropdowns:
  | Dropdown | Expected                      |
  | -------- | ----------------------------- |
  | Fonte    | Finviz, Yahoo, Google Finance | \n | Mercado | US (Americano), EU (Europeu), PT (Português), BR (Brasileiro) |
- [x] **Step 5:** Test search: AAPL + Yahoo + US → JSON result or suggestions (no 405).
- [x] Create this TODO (auto)

**Completed:** 6/6

**Notes:** Backend routes correct. Issue was Live Server (port 5500, no /api). Flask provides data/JSON. All tests passed: dropdowns fixed, no 405/JSON errors.

# Git Commands - Make `git add .`, `commit`, `push origin main` work

**Status:** ⏳ In Progress

## Steps:
- [ ] **Step 1:** `git add .` (stage TODO.md, templates/index.html changes)
- [ ] **Step 2:** `git commit -m "FinanceScraping | primeira etapa "`
- [ ] **Step 3:** `git branch -m main` (rename branch to main, safe as origin/main matches HEAD)
- [ ] **Step 4:** `git push -u origin main` (push with upstream)

**Completed:** 0/4

**Notes:** Current branch: blackboxai/universal-ticker-support. origin/main up to date.

