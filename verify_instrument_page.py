
import httpx
import asyncio

BASE_URL = "http://localhost:8000"

async def test_instrument_flow(symbol):
    print(f"--- Testing Flow for: {symbol} ---")
    async with httpx.AsyncClient() as client:
        # 1. Search (as done in InstrumentPage)
        print(f"1. Search '/scripmaster/search?q={symbol}'")
        resp = await client.get(f"{BASE_URL}/scripmaster/search", params={"q": symbol})
        if resp.status_code == 200:
            data = resp.json().get('data', [])
            print(f"   Success. Found {len(data)} results.")
            match = next((s for s in data if s['tradingSymbol'] == symbol), None)
            if match:
                print(f"   [OK] Exact match found: {match['tradingSymbol']}")
                print(f"        Token: {match.get('instrumentToken')}, Segment: {match.get('exchangeSegment')}")
            else:
                print(f"   [FAIL] No exact match in results. Top result: {data[0]['tradingSymbol'] if data else 'None'}")
        else:
            print(f"   [FAIL] Status {resp.status_code}")

        # 2. Get Scrip Details (Alternative)
        print(f"2. Get Scrip '/scripmaster/scrip/{symbol}'")
        resp = await client.get(f"{BASE_URL}/scripmaster/scrip/{symbol}")
        if resp.status_code == 200:
            print(f"   [OK] Found scrip: {resp.json().get('data', {}).get('tradingSymbol')}")
        else:
             print(f"   [FAIL] Status {resp.status_code}")

        # 3. Historical Data
        print(f"3. Historical '/historical/{symbol}'")
        resp = await client.get(f"{BASE_URL}/historical/{symbol}", timeout=30.0)
        if resp.status_code == 200:
            hdata = resp.json()
            print(f"   [OK] Source: {hdata.get('source')}, Candles: {len(hdata.get('candles', []))}")
        else:
            print(f"   [FAIL] Status {resp.status_code}")

        # 4. Snapshot Quote (The Logic I Just Added)
        if match:
            token = f"{match['exchangeSegment']}|{match['instrumentToken']}"
            print(f"4. Snapshot Quote '/market/quotes' for {token}")
            payload = {"instrument_tokens": [token]}
            resp = await client.post(f"{BASE_URL}/market/quotes", json=payload)
            
            if resp.status_code == 200:
                qdata = resp.json()
                print(f"   [OK] Response: {qdata}")
                if qdata and isinstance(qdata, list) and len(qdata) > 0:
                    q = qdata[0]
                    print(f"   [SUCCESS] LTP: {q.get('ltp', 'N/A')}, Source: API")
                else:
                    print(f"   [FAIL] Empty data returned")
            else:
                print(f"   [FAIL] Status {resp.status_code}: {resp.text}")

if __name__ == "__main__":
    asyncio.run(test_instrument_flow("RELIANCE-EQ"))
