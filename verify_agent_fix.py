import asyncio
import httpx
import json
import time

API_URL = "http://localhost:8000/agent/chat"

TEST_CASES = [
    "What is the current price of RELIANCE-EQ?",
    "Show me the market depth for TCS.",
    "Get me the quote for HDFCBANK.",
    "How is NIFTY 50 performing right now?",
    "Check the price of INFIBEAM.",
    "What is the volume for TATAMOTORS?",
    "Is SENSEX up or down today?",
    "Get detailed quote for SBIN."
]

async def run_verify():
    print(f"🚀 Verifying Agent Fix (Market Data Routing)...\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, query in enumerate(TEST_CASES, 1):
            print(f"[{i}/{len(TEST_CASES)}] Asking: {query}")
            try:
                response = await client.post(API_URL, json={"query": query})
                if response.status_code == 200:
                    data = response.json()
                    agent = data.get("agent", "Unknown")
                    tools = data.get("mcp_tool_calls", [])
                    tool_names = [t.get("tool") for t in tools] if tools else ["None"]
                    print(f"   Agent: {agent} | Tools: {tool_names}")
                else:
                    print(f"   Error: {response.status_code}")
            except Exception as e:
                print(f"   Exception: {e}")
            
            await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(run_verify())
