
import httpx
import time
import asyncio

async def test_symbol(symbol, name, raw_symbol_in_app):
    print(f"Testing {name} (App sees: '{raw_symbol_in_app}', Mapped to: '{symbol}')...")
    
    # 30 days of data
    period1 = int(time.time()) - (30 * 24 * 60 * 60)
    period2 = int(time.time())
    
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {
        "period1": period1,
        "period2": period2,
        "interval": "1d"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=10.0)
            
        if response.status_code != 200:
            print(f"  [FAILURE] Status {response.status_code} for {symbol}")
            print(f"  Response: {response.text[:100]}...")
            return False
            
        data = response.json()
        result = data.get('chart', {}).get('result', [])
        
        if not result:
            print(f"  [FAILURE] No result in JSON for {symbol}")
            return False
            
        timestamps = result[0].get('timestamp', [])
        print(f"  [SUCCESS] Found {len(timestamps)} candles for {symbol}")
        return True
            
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False

async def main():
    print("--- Starting Yahoo Finance API Test (httpx) ---")

    # Test 1: Standard Stock
    # App logic: "RELIANCE" -> "RELIANCE.NS"
    await test_symbol("RELIANCE.NS", "Reliance (Standard)", "RELIANCE")

    # Test 2: Indices (Current Bad Logic)
    # App logic: "NIFTY 50" -> "NIFTY 50.NS"
    await test_symbol("NIFTY 50.NS", "Nifty 50 (Current App Logic)", "NIFTY 50")
    
    # App logic: "SENSEX" -> "SENSEX.NS"
    await test_symbol("SENSEX.NS", "Sensex (Current App Logic)", "SENSEX")

    # Test 3: Indices (Target Correct Logic)
    await test_symbol("^NSEI", "Nifty 50 (Target)", "NIFTY 50")
    await test_symbol("^BSESN", "Sensex (Target)", "SENSEX")

    # Test 4: Options?
    # App logic: "GOLD26FEB..." -> "GOLD26FEB....NS"
    await test_symbol("GOLD.NS", "Gold ETF? (Proxy check)", "GOLD") 

if __name__ == "__main__":
    asyncio.run(main())
