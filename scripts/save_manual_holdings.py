from dotenv import load_dotenv
load_dotenv()

from scraper.firebase_manager import firebase_manager
from datetime import datetime

# Data extracted by the browser subagent
HOLDINGS_DATA = {
    "QDVE": [
      {"name": "NVIDIA Corp.", "symbol": "NVDA", "weight": 0.2301},
      {"name": "Apple", "symbol": "AAPL", "weight": 0.1853},
      {"name": "Microsoft", "symbol": "MSFT", "weight": 0.1536},
      {"name": "Broadcom Inc.", "symbol": "AVGO", "weight": 0.0820},
      {"name": "Micron Technology", "symbol": "MU", "weight": 0.0212},
      {"name": "Palantir Technologies, Inc.", "symbol": "PLTR", "weight": 0.0187},
      {"name": "AMD", "symbol": "AMD", "weight": 0.0185},
      {"name": "Cisco Systems, Inc.", "symbol": "CSCO", "weight": 0.0171},
      {"name": "Applied Materials, Inc.", "symbol": "AMAT", "weight": 0.0152},
      {"name": "Lam Research", "symbol": "LRCX", "weight": 0.0149}
    ],
    "IS3N": [
      {"name": "Taiwan Semiconductor Manufacturing Co., Ltd.", "symbol": "TSM", "weight": 0.1148},
      {"name": "Samsung Electronics Co., Ltd.", "symbol": "SMSN", "weight": 0.0437},
      {"name": "Tencent Holdings Ltd.", "symbol": "TCEHY", "weight": 0.0334},
      {"name": "SK hynix, Inc.", "symbol": "SKHYNIX", "weight": 0.0243},
      {"name": "Alibaba Group Holding Ltd.", "symbol": "BABA", "weight": 0.0221},
      {"name": "China Construction Bank Corp.", "symbol": "CCB", "weight": 0.0087},
      {"name": "HDFC Bank Ltd.", "symbol": "HDB", "weight": 0.0075},
      {"name": "Reliance Industries Ltd.", "symbol": "RELIANCE", "weight": 0.0072},
      {"name": "Delta Electronics, Inc.", "symbol": "DELTA", "weight": 0.0071},
      {"name": "Hon Hai Precision Industry Co., Ltd.", "symbol": "HONHAI", "weight": 0.0063}
    ],
    "2B76": [
      {"name": "Brookfield Corp.", "symbol": "BN", "weight": 0.0734},
      {"name": "Blackstone, Inc.", "symbol": "BX", "weight": 0.0725},
      {"name": "3i Group Plc", "symbol": "III.L", "weight": 0.0593},
      {"name": "KKR & Co., Inc.", "symbol": "KKR", "weight": 0.0535},
      {"name": "Partners Group Holding AG", "symbol": "PGHN.SW", "weight": 0.0500},
      {"name": "Apollo Global Management, Inc.", "symbol": "APO", "weight": 0.0436},
      {"name": "Washington H. Soul Pattinson & Co. Ltd.", "symbol": "SOL.AX", "weight": 0.0414},
      {"name": "EQT AB", "symbol": "EQT.ST", "weight": 0.0405},
      {"name": "Brookfield Asset Mgmt", "symbol": "BAM", "weight": 0.0399},
      {"name": "Ares Capital", "symbol": "ARCC", "weight": 0.0394}
    ],
    "QUTM": [
      {"name": "IonQ, Inc.", "symbol": "IONQ", "weight": 0.0729},
      {"name": "D-Wave Quantum", "symbol": "QBTS", "weight": 0.0454},
      {"name": "Wells Fargo & Co.", "symbol": "WFC", "weight": 0.0449},
      {"name": "Bank of America Corp.", "symbol": "BAC", "weight": 0.0435},
      {"name": "Nokia Oyj", "symbol": "NOKIA.HE", "weight": 0.0435},
      {"name": "Accenture Plc", "symbol": "ACN", "weight": 0.0427},
      {"name": "Amazon.com, Inc.", "symbol": "AMZN", "weight": 0.0424},
      {"name": "IBM", "symbol": "IBM", "weight": 0.0422},
      {"name": "Deutsche Telekom AG", "symbol": "DTE.DE", "weight": 0.0422},
      {"name": "Honeywell International, Inc.", "symbol": "HON", "weight": 0.0409}
    ],
    "JEDI": [
      {"name": "Taiwan Semiconductor Manufacturing Co., Ltd.", "symbol": "TSM", "weight": 0.1214},
      {"name": "Samsung Electronics Co., Ltd.", "symbol": "SMSN", "weight": 0.0461},
      {"name": "Tencent Holdings Ltd.", "symbol": "TCEHY", "weight": 0.0354},
      {"name": "SK hynix, Inc.", "symbol": "SKHYNIX", "weight": 0.0258},
      {"name": "Alibaba Group Holding Ltd.", "symbol": "BABA", "weight": 0.0234},
      {"name": "China Construction Bank Corp.", "symbol": "CCB", "weight": 0.0092},
      {"name": "HDFC Bank Ltd.", "symbol": "HDB", "weight": 0.0078},
      {"name": "Reliance Industries Ltd.", "symbol": "RELIANCE", "weight": 0.0078},
      {"name": "Delta Electronics, Inc.", "symbol": "DELTA", "weight": 0.0076},
      {"name": "Hon Hai Precision Industry Co., Ltd.", "symbol": "HONHAI", "weight": 0.0066}
    ],
    "XDWF": [
      {"name": "JPMorgan Chase & Co.", "symbol": "JPM", "weight": 0.0606},
      {"name": "Berkshire Hathaway, Inc.", "symbol": "BRK-B", "weight": 0.0512},
      {"name": "Visa, Inc.", "symbol": "V", "weight": 0.0396},
      {"name": "Mastercard, Inc.", "symbol": "MA", "weight": 0.0328},
      {"name": "Bank of America Corp.", "symbol": "BAC", "weight": 0.0254},
      {"name": "HSBC Holdings Plc", "symbol": "HSBA.L", "weight": 0.0216},
      {"name": "The Goldman Sachs Group, Inc.", "symbol": "GS", "weight": 0.0190},
      {"name": "Wells Fargo & Co.", "symbol": "WFC", "weight": 0.0189},
      {"name": "Royal Bank of Canada", "symbol": "RY", "weight": 0.0173},
      {"name": "Commonwealth Bank of Australia", "symbol": "CBA.AX", "weight": 0.0152}
    ],
    "NUKL": [
      {"name": "Cameco", "symbol": "CCJ", "weight": 0.1546},
      {"name": "NexGen Energy Ltd.", "symbol": "NXE", "weight": 0.0724},
      {"name": "Sprott Physical Uranium", "symbol": "U.U.TO", "weight": 0.0669},
      {"name": "Oklo", "symbol": "OKLO", "weight": 0.0594},
      {"name": "Jacobs Solutions", "symbol": "J", "weight": 0.0524},
      {"name": "Fuji Electric Co., Ltd.", "symbol": "6504.T", "weight": 0.0514},
      {"name": "Atkinsrealis Group", "symbol": "ATRL.TO", "weight": 0.0511},
      {"name": "Hitachi Ltd.", "symbol": "6501.T", "weight": 0.0502},
      {"name": "Mitsubishi Heavy Industries, Ltd.", "symbol": "7011.T", "weight": 0.0500},
      {"name": "Uranium Energy Corp.", "symbol": "UEC", "weight": 0.0472}
    ]
}

def save_manual_holdings():
    print("Saving manually extracted holdings to Firebase...")
    for ticker, holdings in HOLDINGS_DATA.items():
        print(f"Updating {ticker}...")
        try:
            # We use save_etf_holdings directly
            firebase_manager.save_etf_holdings(ticker, holdings)
            print(f"  [SUCCESS] {ticker} updated.")
        except Exception as e:
            print(f"  [ERROR] {ticker}: {e}")

if __name__ == "__main__":
    save_manual_holdings()
