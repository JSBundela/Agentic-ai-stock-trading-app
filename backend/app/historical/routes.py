"""
Historical data proxy endpoint - fetches Yahoo Finance OHLC data server-side to bypass CORS
"""
from fastapi import APIRouter
import httpx
import time
import random
import re
from app.core.logger import logger

router = APIRouter()

import yfinance as yf
import pandas as pd

def generate_sample_candles(base_price: float = 2500.0, days: int = 30):
    """Generate sample OHLC candles when Yahoo Finance is unavailable"""
    candles = []
    current_time = int(time.time())
    day_seconds = 86400
    
    price = base_price
    for i in range(days, 0, -1):
        timestamp = current_time - (i * day_seconds)
        # Simulate price movement
        change = random.uniform(-0.03, 0.03) * price
        open_price = price
        close_price = price + change
        high_price = max(open_price, close_price) + random.uniform(0, 0.02) * price
        low_price = min(open_price, close_price) - random.uniform(0, 0.02) * price
        
        candles.append({
            "time": timestamp,
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2)
        })
        price = close_price
    
    return candles


# Map internal symbols to Yahoo Finance symbols
SYMBOL_MAP = {
    "NIFTY 50": "^NSEI",
    "NIFTY": "^NSEI",
    "SENSEX": "^BSESN",
    "BSE SENSEX": "^BSESN",
    "NIFTY BANK": "^NSEBANK",
    "BANKNIFTY": "^NSEBANK",
}

@router.get("/historical/{symbol}")
async def get_historical_data(symbol: str):
    """
    Proxy endpoint to fetch historical OHLC data using yfinance library.
    Falls back to sample data if Yahoo Finance is unavailable or not supported.
    """
    try:
        # 1. Check for Options (unsupported by Yahoo Finance public API generally)
        if re.search(r'\d{2}[A-Z]{3}\d+[CP]E$', symbol) or re.search(r'\d{2}[A-Z]{3}\d+(?:CE|PE)', symbol):
            logger.info(f"[Historical] Options contract detected: {symbol}. Skipping API call, returning sample data.")
            return {"candles": generate_sample_candles(), "source": "sample_options"}

        # 2. Map Symbol
        yahoo_symbol = SYMBOL_MAP.get(symbol.upper())

        if not yahoo_symbol:
            # Default fallback logic
            if '-' in symbol:
                # e.g. "RELIANCE-EQ" -> "RELIANCE.NS"
                yahoo_symbol = symbol.split('-')[0] + '.NS'
            elif not symbol.endswith('.NS') and not symbol.endswith('.BO') and not symbol.startswith('^'):
                # Append .NS for NSE stocks by default if no suffix
                yahoo_symbol = f"{symbol}.NS"
            else:
                yahoo_symbol = symbol

        logger.info(f"[Historical] Fetching data for {symbol} -> {yahoo_symbol} via yfinance lib")
        
        # 3. Use yfinance Library
        # Run in executor to avoid blocking async event loop
        def fetch_yf():
            # Create Ticker
            ticker = yf.Ticker(yahoo_symbol)
            # Fetch history
            return ticker.history(period="1mo", interval="1d")

        try:
           import asyncio
           loop = asyncio.get_event_loop()
           hist = await loop.run_in_executor(None, fetch_yf)
        except Exception as lib_err:
             logger.error(f"[Historical] yfinance lib error: {lib_err}")
             return {"candles": generate_sample_candles(), "source": "sample_lib_error"}

        if hist.empty:
            logger.warning(f"[Historical] No result found for {yahoo_symbol}")
            return {"candles": generate_sample_candles(), "source": "sample_empty"}
        
        # 4. Parse DataFrame to Candles
        candles = []
        # Reset index to get Date column if it's the index
        hist = hist.reset_index()
        
        for _, row in hist.iterrows():
            # Handle different Date column names or types
            # yfinance returns 'Date' (timestamp) or 'Datetime'
            date_val = row.get('Date')
            
            if pd.isna(date_val): 
                continue
                
            # Convert timestamp to unix seconds
            try:
                ts = int(date_val.timestamp())
            except:
                continue

            # Check for valid OHLC
            if pd.notna(row['Open']) and pd.notna(row['Close']):
                candles.append({
                    "time": ts,
                    "open": row['Open'],
                    "high": row['High'],
                    "low": row['Low'],
                    "close": row['Close']
                })
        
        if len(candles) == 0:
            return {"candles": generate_sample_candles(), "source": "sample_parsed_empty"}
            
        logger.info(f"[Historical] Success. Returning {len(candles)} candles.")
        return {"candles": candles, "source": "yahoo_lib"}
        
    except Exception as e:
        logger.error(f"[Historical] Error fetching {symbol}: {e}")
        # Return sample data on any error
        return {"candles": generate_sample_candles(), "source": "sample_error"}
