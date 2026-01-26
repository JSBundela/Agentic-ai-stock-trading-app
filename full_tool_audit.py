import asyncio
import httpx
import json

API_URL = "http://localhost:8000/agent/chat"

# Audit ALL 11 tools across all agents
AUDIT_SCENARIOS = [
    {
        "tool": "getQuotes",
        "query": "What is the current price of RELIANCE?",
        "target_agent": "MarketExplainer"
    },
    {
        "tool": "getIndexQuotes",
        "query": "What is the value of NIFTY 50?",
        "target_agent": "MarketExplainer"
    },
    {
        "tool": "getMarketDepth",
        "query": "Show me the market depth for TCS.",
        "target_agent": "MarketExplainer"
    },
    {
        "tool": "searchNews",
        "query": "What is the latest news on Tata Motors?",
        "target_agent": "TrendNews"
    },
    {
        "tool": "getLimits",
        "query": "How much margin do I have?",
        "target_agent": "DataInterpreter"
    },
    {
        "tool": "getOrders",
        "query": "Show me my rejected orders.",
        "target_agent": "DataInterpreter"
    },
    {
        "tool": "getPositions",
        "query": "What are my current open positions?",
        "target_agent": "DataInterpreter"
    },
    {
        "tool": "navigateTo",
        "query": "Take me to the funds page.",
        "target_agent": "UINavigation"
    },
    {
        "tool": "generateChart",
        "query": "Show me a chart of NIFTY 50.",
        "target_agent": "MarketExplainer"
    },
    {
        "tool": "getWebSocketStatus",
        "query": "Is the real-time market feed working?",
        "target_agent": "DataInterpreter"
    },
    {
        "tool": "applyFilter",
        "query": "Show me only my MIS rejected orders.",
        "target_agent": "DataInterpreter"
    }
]

async def run_full_audit():
    print(f"🕵️ Starting Full 11-Tool Audit...\n")
    results = []
    
    async with httpx.AsyncClient(timeout=40.0) as client:
        for scenario in AUDIT_SCENARIOS:
            print(f"Checking Tool: {scenario['tool']} | Query: '{scenario['query']}'")
            try:
                response = await client.post(API_URL, json={"query": scenario["query"]})
                if response.status_code == 200:
                    data = response.json()
                    agent_resp = data.get("response", {}).get("content", "")
                    tool_calls = data.get("mcp_tool_calls", [])
                    actual_tools = [t["tool"] for t in tool_calls]
                    
                    status = "✅ USED" if scenario["tool"] in actual_tools else "❌ NOT USED"
                    
                    results.append({
                        "question": scenario["query"],
                        "tool": scenario["tool"],
                        "agent": data.get("agent", "Unknown"),
                        "response_preview": agent_resp[:100] + "...",
                        "status": status,
                        "actual_tools": actual_tools
                    })
                    print(f"   Result: {status} via {data.get('agent')}")
                else:
                    print(f"   Error: HTTP {response.status_code}")
            except Exception as e:
                print(f"   Exception: {e}")
            
            print("-" * 60)

    # Output detailed report
    print("\n" + "="*80)
    print("FINAL 11-TOOL AUDIT REPORT")
    print("="*80)
    print(f"{'QUESTION':<40} | {'TOOL':<20} | {'STATUS'}")
    print("-" * 80)
    for r in results:
        print(f"{r['question']:<40} | {r['tool']:<20} | {r['status']}")
    
    # Save to file
    with open("full_audit_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    asyncio.run(run_full_audit())
