import yfinance as yf
tickers = ["EDP.LS", "GALP.LS", "JMT.LS"]
for t in tickers:
    try:
        stock = yf.Ticker(t)
        print(f"--- {t} ---")
        info = stock.info
        print(f"Price: {info.get('currentPrice')}")
        print(f"PE: {info.get('trailingPE')}")
        print(f"EV/EBITDA: {info.get('enterpriseToEbitda')}")
        print(f"ROE: {info.get('returnOnEquity')}")
        print("Keys available:", list(info.keys()))
    except Exception as e:
        print(f"Error for {t}: {e}")
