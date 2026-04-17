import yfinance as yf
import json

def test_yf():
    ticker = "AAPL"
    stock = yf.Ticker(ticker)
    info = stock.info
    print(f"SMA50: {info.get('fiftyDayAverage')}")
    print(f"SMA200: {info.get('twoHundredDayAverage')}")
    print(f"Price: {info.get('currentPrice')}")

if __name__ == "__main__":
    test_yf()
