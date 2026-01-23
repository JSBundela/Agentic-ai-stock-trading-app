
import asyncio
import websockets
import json

async def test_hsm_neo_fin_key():
    with open('session_cache.json', 'r') as f:
        cache = json.load(f)
    with open('.env', 'r') as f:
        env = dict(line.strip().split('=', 1) for line in f if '=' in line)
    
    token = cache['view_token']
    sid = cache['view_sid']
    access_token = env.get('KOTAK_ACCESS_TOKEN')
    
    url = "wss://mlhsm.kotaksecurities.com"
    
    headers = {
        "sid": sid,
        "Authorization": f"Bearer {token}",
        "neo-fin-key": access_token
    }
    
    print(f"Connecting to {url}...")
    try:
        async with websockets.connect(url, additional_headers=headers) as ws:
            print("Connected!")
            
            handshake = {
                "type": "cn",
                "token": token,
                "sid": sid,
                "un": "ZGSFS"
            }
            print(f"Sending handshake: {json.dumps(handshake)[:100]}...")
            await ws.send(json.dumps(handshake))
            
            print("Awaiting responses (5s)...")
            try:
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    print(f"RECEIVED: {msg}")
            except asyncio.TimeoutError:
                print("No more messages received (timeout).")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_hsm_neo_fin_key())
