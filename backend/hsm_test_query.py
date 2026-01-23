
import asyncio
import websockets
import json

async def test_hsm_query_param():
    with open('session_cache.json', 'r') as f:
        cache = json.load(f)
    
    token = cache['view_token']
    sid = cache['view_sid']
    # Try with query param
    url = f"wss://mlhsm.kotaksecurities.com/?un=ZGSFS&sid={sid}&token={token}"
    
    print(f"Connecting to {url}...")
    try:
        async with websockets.connect(url) as ws:
            print("Connected!")
            
            # Try NO handshake first, just wait
            print("Awaiting responses (5s)...")
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"RECEIVED: {msg}")
            except asyncio.TimeoutError:
                print("No initial message. Sending 'cn'...")
                await ws.send(json.dumps({"type": "cn", "token": token, "sid": sid, "un": "ZGSFS"}))
                msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"RECEIVED AFTER CN: {msg}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_hsm_query_param())
