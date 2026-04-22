import pandas as pd
import numpy as np
from types import SimpleNamespace

# Mock of the YahooFinanceScraper logic
def mock_sma_calculation(hist_prices, info_input):
    info = info_input.copy()
    hist = pd.DataFrame({'Close': hist_prices})
    
    # Logic extracted from scraper/yahoo.py
    sma50 = info.get('fiftyDayAverage')
    sma200 = info.get('twoHundredDayAverage')
    
    try:
        if (sma50 is None or sma50 == 0) and len(hist) >= 50:
            sma50 = round(hist['Close'].tail(50).mean(), 4)
        if (sma200 is None or sma200 == 0) and len(hist) >= 200:
            sma200 = round(hist['Close'].tail(200).mean(), 4)
    except Exception as e:
        print(f"Error: {e}")
        
    return sma50, sma200

def run_mock_test():
    print("--- Running Mock SMA Calculation Test ---")
    
    # 1. Simulate historical prices (250 days)
    # Start at 100 and slowly grow
    prices = np.linspace(100, 150, 250) + np.random.normal(0, 2, 250)
    
    # 2. Case: Info has NO SMAs
    info_no_smas = {'currentPrice': 150.0}
    
    s50, s200 = mock_sma_calculation(prices, info_no_smas)
    
    print("\n[Scenario 1: Missing SMAs in 'info']")
    print(f"Calculated SMA50: {s50} (Expected ~{np.mean(prices[-50:]):.2f})")
    print(f"Calculated SMA200: {s200} (Expected ~{np.mean(prices[-200:]):.2f})")
    
    # 3. Case: Info HAS SMAs (should not overwrite if present and non-zero)
    info_with_smas = {'fiftyDayAverage': 999.0, 'twoHundredDayAverage': 888.0}
    s50_2, s200_2 = mock_sma_calculation(prices, info_with_smas)
    
    print("\n[Scenario 2: SMAs present in 'info']")
    print(f"SMA50: {s50_2} (Should be 999.0)")
    print(f"SMA200: {s200_2} (Should be 888.0)")

if __name__ == "__main__":
    run_mock_test()
