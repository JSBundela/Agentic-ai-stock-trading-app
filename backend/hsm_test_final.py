
import asyncio
import websockets
import json

async def test_hsm_final_hope():
    with open('session_cache.json', 'r') as f:
        cache = json.load(f)
    with open('.env', 'r') as f:
        env = dict(line.strip().split('=', 1) for line in f if '=' in line)
    
    # HSM often uses the Trade Token (session token) for actual market data
    token = cache['trade_token']
    sid = cache['trade_sid']
    dc = cache.get('data_center', 'E21')
    ucc = env.get('UCC')
    access_token = env.get('KOTAK_ACCESS_TOKEN')
    
    url = "wss://mlhsm.kotaksecurities.com"
    
    # Try with plain Authorization (NO BEARER)
    headers = {
        "sid": sid,
        "Authorization": access_token, # NO BEARER per doc Q1
        "Auth": token,
        "neo-fin-key": "neotradeapi"
    }
    
    print(f"Connecting to {url}...")
    try:
        async with websockets.connect(url, additional_headers=headers) as ws:
            print("Connected!")
            
            # Try a handshake with ALL possible param names including data center
            handshake = {
                "type": "cn",
                "token": token,
                "sid": sid,
                "un": ucc,
                "dc": dc,
                "dataCenter": dc
            }
            print(f"Sending handshake: {json.dumps(handshake)[:150]}...")
            await ws.send(json.dumps(handshake))
            
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
    asyncio.run(test_hsm_final_hope())
