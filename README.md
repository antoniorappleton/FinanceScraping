# FinanceScraping 📈

Automated scraping pipeline for global ticker data (Stocks & ETFs), with a focus on European markets. The system synchronizes real-time financial metrics directly to Firestore.

## 🚀 Features
- **Multi-Source Scraping**: Reliable data extraction from Yahoo Finance, FT Markets, JustETF, Google Finance, and Finviz.
- **Smart Fallback System**: Automatically switches providers if one fails or returns invalid data.
- **European ETF Optimization**: Specialized handling for XETRA and Euronext listed assets.
- **Firestore Integration**: Periodically updates a central database with price, performance, and key financial indicators.
- **Automatic Ticker Normalization**: Handles custom database IDs (e.g., `XETR_VVMX`) by normalizing them for providers.

## 🛠️ Setup

### Prerequisites
- Python 3.8+
- [Firebase account](https://console.firebase.google.com/) with a Service Account JSON file.

### Installation
1. Clone the repository.
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables in `.env`:
   ```env
   FIREBASE_SERVICE_ACCOUNT_JSON=path/to/your/serviceAccountKey.json
   FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
   ```

## 📖 Usage

### Running the Scraper
You can run a full sync or a fast sync (only price and cap):
```bash
python cron_scraper.py --mode full  # Standard full sync
python cron_scraper.py --mode fast  # High-frequency price update
```

### Utility Tools
All helper scripts are located in the `tools/` directory:
- **Check Sync Status**: Verify which tickers are updated or stale.
  ```bash
  python tools/check_sync_status.py
  ```
- **Debug Ticker**: Inspect a specific document in Firestore.
  ```bash
  python tools/get_ticker_doc.py
  ```
- **Verify Tickers**: Run a diagnostic on the ticker list.
  ```bash
  python tools/verify_tickers.py
  ```

## 📂 Project Structure
- `cron_scraper.py`: Main orchestration script.
- `scraper/`: Core scraping logic per provider.
- `tools/`: Diagnostic and utility scripts.
- `requirements.txt`: Project dependencies.

## 📝 How to Add New Tickers
Simply add a new document to the `acoesDividendos` collection in Firestore with:
- `ticker`: The symbol (e.g., `AAPL`, `VWCE`, or `XETR_VVMX`).
- `market_name`: e.g., `US`, `Portugal`, `Xetra`.
The scraper will automatically pick it up on the next run.
