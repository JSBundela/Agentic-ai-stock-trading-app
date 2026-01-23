
import asyncio
import websockets
import json

async def test_hsm_kitchen_sink():
    with open('session_cache.json', 'r') as f:
        cache = json.load(f)
    
    token = cache['view_token']
    sid = cache['view_sid']
    url = "wss://mlhsm.kotaksecurities.com"
    
    headers = {
        "sid": sid,
        "Authorization": f"Bearer {token}",
        "Sid": sid,
        "auth": token
    }
    
    print(f"Connecting to {url}...")
    try:
        async with websockets.connect(url, additional_headers=headers) as ws:
            print("Connected!")
            
            handshake = {
                "type": "cn",
                "token": token,
                "sid": sid,
                "un": "ZGSFS",
                "Authorization": token,
                "auth": token,
                "Sid": sid
            }
            print(f"Sending handshake: {json.dumps(handshake)[:100]}...")
            await ws.send(json.dumps(handshake))
            
            # Also try sending a subscription immediately
            # Crude check for an MCX scrip token
            # MCX GOLD 05FEB26 might be around. 
            sub = {"type": "mw", "scrip": "mcx_fo|251433"} # Example
            print(f"Sending dummy sub: {json.dumps(sub)}...")
            await ws.send(json.dumps(sub))

            print("Awaiting responses (10s)...")
            try:
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    print(f"RECEIVED: {msg}")
            except asyncio.TimeoutError:
                print("No more messages received (timeout).")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_hsm_kitchen_sink())
