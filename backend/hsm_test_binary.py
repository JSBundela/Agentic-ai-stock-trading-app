
import asyncio
import websockets
import json
import struct

def build_binary_handshake(token, sid):
    src = "JS_API"
    
    # Payload elements (Tag + Length + Value)
    # Field 1: JWT
    f1 = b"\x01" + struct.pack(">H", len(token)) + token.encode()
    # Field 2: SID
    f2 = b"\x02" + struct.pack(">H", len(sid)) + sid.encode()
    # Field 3: SRC
    f3 = b"\x03" + struct.pack(">H", len(src)) + src.encode()
    
    packet = b"\x01" + b"\x03" + f1 + f2 + f3
    header = struct.pack(">H", len(packet))
    return header + packet

async def test_binary_hsm():
    with open('session_cache.json', 'r') as f:
        cache = json.load(f)
    with open('.env', 'r') as f:
        env = dict(line.strip().split('=', 1) for line in f if '=' in line)
    
    # The doc says "Final token(session token) which user gets after running login api"
    # That is the Trade Token.
    token = cache['trade_token']
    sid = cache['trade_sid']
    
    url = "wss://mlhsm.kotaksecurities.com"
    
    print(f"Connecting to {url}...")
    try:
        async with websockets.connect(url) as ws:
            print("Connected!")
            
            handshake = build_binary_handshake(token, sid)
            print(f"Sending Binary Handshake ({len(handshake)} bytes)...")
            await ws.send(handshake)
            
            print("Awaiting responses (10s)...")
            try:
                while True:
                    msg = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    print(f"RECEIVED ({len(msg)} bytes): {msg.hex() if isinstance(msg, bytes) else msg}")
                    
                    # Connection success packet structure:
                    # Length (2), Type (1), Field Count (1), Field ID (1), Length (2), Status (1 character 'K')
                    # 'K' is 4b
                    if isinstance(msg, bytes) and len(msg) >= 6:
                        # Skip header
                        body = msg[2:]
                        if body[0] == 1: # CONNECTION_TYPE
                            print("💎💎💎 BINARY HSM Handshake SUCCESS - ACK RECEIVED!")
                            # Now try to subscribe
                            return
            except asyncio.TimeoutError:
                print("No more messages received (timeout).")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_binary_hsm())
