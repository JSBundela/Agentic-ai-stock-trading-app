import asyncio
import httpx
import json
import time

API_URL = "http://localhost:8000/agent/chat"

# Questions specifically targeting the NEWLY activated tools
TEST_CASES = [
    # Market Depth (MarketExplainer)
    "Show me the market depth for RELIANCE-EQ.",
    "What are the bids and asks for TCS?",
    
    # Portfolio/Funds (DataInterpreter)
    "How much cash do I have available?",
    "What is my margin used?",
    
    # Orders (DataInterpreter)
    "Show me my rejected orders.",
    "Do I have any open buy orders?",
    
    # Positions (DataInterpreter)
    "What is my total P&L?",
    "List my open positions.",
    
    # UI Navigation (UINavigation) - re-verify
    "Go to the dashboard."
]

async def run_verify():
    print(f"🚀 Verifying Full Tool Activation...\n")
    
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
            
            await asyncio.sleep(1.0)

if __name__ == "__main__":
    asyncio.run(run_verify())
