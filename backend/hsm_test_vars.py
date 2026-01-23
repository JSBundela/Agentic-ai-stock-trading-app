
import asyncio
import websockets
import json

async def test_hsm_variations():
    with open('session_cache.json', 'r') as f:
        cache = json.load(f)
    with open('.env', 'r') as f:
        env = dict(line.strip().split('=', 1) for line in f if '=' in line)
    
    token = cache['view_token']
    sid = cache['view_sid']
    ucc = env.get('UCC')
    mobile = env.get('MOBILE_NUMBER')
    
    url = "wss://mlhsm.kotaksecurities.com"
    
    variations = [
        {"type": "cn", "token": token, "sid": sid, "un": ucc},
        {"type": "cn", "access_token": token, "sid": sid, "un": ucc},
        {"type": "cn", "token": token, "sid": sid, "un": mobile},
        {"type": "cn", "access_token": token, "sid": sid, "un": mobile},
    ]
    
    for i, payload in enumerate(variations):
        print(f"\n--- Testing Variation {i+1}: {list(payload.keys())} ---")
        try:
            async with websockets.connect(url, additional_headers={"sid": sid, "Authorization": f"Bearer {token}"}) as ws:
                print(f"Sending: {json.dumps(payload)[:100]}...")
                await ws.send(json.dumps(payload))
                
                # Try to subscribe to something current (MCX CRUDEOIL symbol is usually active)
                # We need a token. I'll just wait for the ACK first.
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    print(f"SUCCESS! RECEIVED: {msg}")
                    return # Stop if one works
                except asyncio.TimeoutError:
                    print("Timeout - no response.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_hsm_variations())
