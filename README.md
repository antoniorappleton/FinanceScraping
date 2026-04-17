# FinanceScraping 📈

Automated scraping pipeline for global ticker data (Stocks & ETFs), with a focus on European markets. The system synchronizes real-time financial metrics directly to Firestore.

## 🚀 Features
- **Multi-Source Scraping**: Reliable data extraction from Yahoo Finance, FT Markets, JustETF, Google Finance, and Finviz.
- **Smart Fallback System**: Automatically switches providers if one fails or returns invalid data.
- **European Asset Focus**: Specialized logic for Euronext, XETRA, and Portuguese markets.
- **Intelligent Bootstrap Logic**: Automatically detects tickers with missing or invalid prices (`#N/A`) and force-updates them before following regular sync schedules.
- **Dynamic Frequency**: High-frequency price updates vs. weekly full financial health checks.

## ⚙️ Automation & Scheduling

The project includes a robust local scheduler (`local_scheduler.py`) designed to maintain the database updated without manual intervention:

| Mode | Frequency | Scope |
| :--- | :--- | :--- |
| **Priority Bootstrap** | Every Run | Tickers with `#N/A` or missing `valorStock` get price updates immediately. |
| **Fast Sync** | Every 4 Hours* | Updates `valorStock`, `priceChange_1d`, and `marketCap`. |
| **Full Sync** | Weekly (Sundays) | Updates all indicators (P/E, ROE, RSI, Yield, Performance 1m/1y, etc.). |

*\*Default interval, configurable via command line.*

## 🛠️ Setup

### Prerequisites
- Python 3.8+
- [Firebase project](https://console.firebase.google.com/) with a Service Account JSON.

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
4. Configure `.env`:
   ```env
   FIREBASE_SERVICE_ACCOUNT_JSON=C:\path\to\your\firebase-key.json
   ```

## 📖 Usage

### Automated Execution (Recommended)
Run the local scheduler in the background. It will manage the frequencies and modes automatically.
```bash
python local_scheduler.py --interval-4h
```

### Manual Execution
You can manually trigger specific sync modes using `cron_scraper.py`:
```bash
# Update only price and basic info for all tickers
python cron_scraper.py --mode fast

# Update all financial metrics (intended for weekly runs)
python cron_scraper.py --mode full
```

## 📂 Project Structure
- `local_scheduler.py`: Background service that orchestrates sync timing.
- `cron_scraper.py`: Core logic for fetching ticker data and updating Firestore.
- `scraper/`: Specialized modules for each data provider (Yahoo, FT, etc.).
- `tools/`: Utility scripts for database maintenance and diagnostic checks.
- `app.py`: (Optional) Web interface for portfolio analysis and visualization.

## 📝 Data Model & Ticker Management
The system reads from the `acoesDividendos` collection in Firestore.

**To add a new ticker:**
1. Create a document with the Ticker as ID (e.g. `AAPL` or `XETR_VVMX`).
2. Set `mercado` field (e.g., `Portugal`, `US`, `Xetra`).
3. (Optional) Set `valorStock` to `#N/A` if you want the scraper to prioritize it immediately.

**To trigger an immediate full update for a ticker:**
The scheduler handles this based on the `lastFullSync` timestamp, but you can always run `--mode full` manually.
