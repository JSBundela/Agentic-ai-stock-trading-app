"""
Historical data proxy endpoint - fetches Yahoo Finance OHLC data server-side to bypass CORS
"""
from fastapi import APIRouter
import httpx
import time
import random

router = APIRouter()

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

@router.get("/historical/{symbol}")
async def get_historical_data(symbol: str):
    """
    Proxy endpoint to fetch historical OHLC data from Yahoo Finance.
    Falls back to sample data if Yahoo Finance is unavailable.
    """
    try:
        # Convert to Yahoo Finance format (add .NS for NSE stocks)
        yahoo_symbol = symbol.split('-')[0] + '.NS' if '-' in symbol else symbol + '.NS'
        
        # 30 days of daily data
        period1 = int(time.time()) - (30 * 24 * 60 * 60)
        period2 = int(time.time())
        
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
        params = {
            "period1": period1,
            "period2": period2,
            "interval": "1d"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
        
        # If Yahoo Finance is rate limited (429) or returns error, use sample data
        if response.status_code != 200:
            return {"candles": generate_sample_candles(), "source": "sample"}
        
        data = response.json()
        result = data.get('chart', {}).get('result', [])
        
        if not result or len(result) == 0:
            return {"candles": generate_sample_candles(), "source": "sample"}
        
        chart_data = result[0]
        timestamps = chart_data.get('timestamp', [])
        quotes = chart_data.get('indicators', {}).get('quote', [{}])[0]
        
        candles = []
        for i in range(len(timestamps)):
            if (quotes.get('open', [])[i] and 
                quotes.get('high', [])[i] and 
                quotes.get('low', [])[i] and 
                quotes.get('close', [])[i]):
                
                candles.append({
                    "time": timestamps[i],
                    "open": quotes['open'][i],
                    "high": quotes['high'][i],
                    "low": quotes['low'][i],
                    "close": quotes['close'][i]
                })
        
        if len(candles) == 0:
            return {"candles": generate_sample_candles(), "source": "sample"}
            
        return {"candles": candles, "source": "yahoo"}
        
    except Exception as e:
        # Return sample data on any error
        return {"candles": generate_sample_candles(), "source": "sample"}
