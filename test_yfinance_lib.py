
import yfinance as yf
import pandas as pd

def test_yfinance_lib(symbol="RELIANCE.NS"):
    print(f"Fetching {symbol} using yfinance lib...")
    try:
        ticker = yf.Ticker(symbol)
        # Fetch 1 month history
        hist = ticker.history(period="1mo")
        
        if hist.empty:
            print("❌ No data found (Empty DataFrame)")
        else:
            print(f"✅ Success! Fetched {len(hist)} rows.")
            print(hist.tail())
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_yfinance_lib()
