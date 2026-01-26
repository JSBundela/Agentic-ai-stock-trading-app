import asyncio
import httpx
import json

API_URL = "http://0.0.0.0:8000/agent/chat"

TEST_QUERIES = [
    "Show me a chart of RELIANCE.",
    "Plot the trend for Infosys.",
    "Give me a 1 year chart for TATAMOTORS."
]

async def verify_charts():
    print(f"🚀 Verifying Visual Agent Capabilities...\n")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for query in TEST_QUERIES:
            print(f"Asking: '{query}'")
            try:
                response = await client.post(API_URL, json={"query": query})
                data = response.json()
                
                # Check for tool usage
                tools = data.get("mcp_tool_calls", [])
                chart_tool = next((t for t in tools if t["tool"] == "generateChart"), None)
                
                if chart_tool:
                    print(f"✅ Success! Generated Chart for: {chart_tool['args']}")
                    print(f"   Data Points: {len(chart_tool['result'].get('data', []))}")
                    print(f"   Period: {chart_tool['result'].get('period')}")
                else:
                    print(f"❌ Failed. Tools used: {[t['tool'] for t in tools]}")
                    print(f"   Agent Response: {data.get('response', {}).get('content')}")
            
            except Exception as e:
                print(f"Exception: {e}")
            
            print("-" * 40)

if __name__ == "__main__":
    asyncio.run(verify_charts())
