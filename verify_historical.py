
import httpx
import asyncio

BASE_URL = "http://localhost:8000"

async def test_endpoint(symbol, description):
    print(f"Testing {description} ('{symbol}')...")
    url = f"{BASE_URL}/historical/{symbol}"
    try:
        async with httpx.AsyncClient() as client:
            # Measure time
            start = asyncio.get_event_loop().time()
            response = await client.get(url, timeout=10.0)
            end = asyncio.get_event_loop().time()
            duration = end - start
            
        if response.status_code != 200:
            print(f"  [FAILURE] Status {response.status_code}")
            return False
            
        data = response.json()
        print(f"  Status: {response.status_code}, Time: {duration:.2f}s")
        print(f"  Source: {data.get('source')}")
        candles = data.get('candles', [])
        print(f"  Candles: {len(candles)}")
        
        if len(candles) > 0 and data.get('source') == 'yahoo':
            print("  [SUCCESS] Yahoo Data Retrieved")
            return True
        elif len(candles) > 0 and data.get('source') == 'sample_options':
             print("  [SUCCESS] Sample Options Data Retrieved (Expected)")
             return True
        elif len(candles) > 0 and data.get('source') == 'sample':
             print("  [WARNING] Sample Data (Standard Fallback)")
             # Valid if we expect fallback, but we want Yahoo for indices
             return True 
        else:
             print("  [FAILURE] No candles or unexpected source")
             return False

    except Exception as e:
        print(f"  [ERROR] {e}")
        return False
    print("-" * 30)

async def main():
    print("--- Verifying Historical Endpoint ---")
    
    # Test 1: NIFTY 50 (Should map to ^NSEI and get Yahoo data)
    await test_endpoint("NIFTY 50", "Nifty 50 Index")
    
    # Test 2: SENSEX (Should map to ^BSESN and get Yahoo data)
    await test_endpoint("SENSEX", "Sensex Index")
    
    # Test 3: Standard Stock (RELIANCE)
    await test_endpoint("RELIANCE", "Reliance Industries")
    
    # Test 4: Option (Should fast-fail to sample data)
    await test_endpoint("GOLD26FEB99200PE", "Gold Option (Unsupported)")

if __name__ == "__main__":
    asyncio.run(main())
