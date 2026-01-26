import asyncio
import httpx
import json

API_URL = "http://localhost:8000/agent/chat"

# Comprehensive test suite mapping queries to expected agents and tools
TEST_SCENARIOS = [
    {
        "agent": "MarketExplainer",
        "query": "What is the current price of RELIANCE?",
        "expected_tool": "getQuotes"
    },
    {
        "agent": "MarketExplainer",
        "query": "Show me the market depth for TCS.",
        "expected_tool": "getMarketDepth"
    },
    {
        "agent": "TrendNews",
        "query": "What is the latest news on HDFC Bank?",
        "expected_tool": "searchNews"
    },
    {
        "agent": "DataInterpreter",
        "query": "How much cash do I have available?",
        "expected_tool": "getLimits"
    },
    {
        "agent": "DataInterpreter",
        "query": "What are my current open positions?",
        "expected_tool": "getPositions"
    },
    {
        "agent": "UINavigation",
        "query": "Go to the order book.",
        "expected_tool": "navigateTo"
    },
    {
        "agent": "MarketExplainer",
        "query": "Show me a chart of NIFTY 50.",
        "expected_tool": "generateChart"
    }
]

async def run_robust_test():
    print(f"🚀 Starting Robust Agent & Tool Verification...\n")
    results = []
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for scenario in TEST_SCENARIOS:
            print(f"Testing Agent: {scenario['agent']} | Query: '{scenario['query']}'")
            try:
                response = await client.post(API_URL, json={"query": scenario["query"]})
                if response.status_code == 200:
                    data = response.json()
                    actual_agent = data.get("agent", "Unknown")
                    tool_calls = data.get("mcp_tool_calls", [])
                    actual_tools = [t["tool"] for t in tool_calls]
                    
                    status = "✅ PASS" if scenario["expected_tool"] in actual_tools else "❌ FAIL (Tool Mismatch)"
                    if actual_agent != scenario["agent"]:
                        status = "⚠️ PASS (Agent Mismatch / Tool OK)" if scenario["expected_tool"] in actual_tools else "❌ FAIL"
                    
                    results.append({
                        "query": scenario["query"],
                        "expected_agent": scenario["agent"],
                        "actual_agent": actual_agent,
                        "expected_tool": scenario["expected_tool"],
                        "actual_tools": actual_tools,
                        "status": status
                    })
                    print(f"   Result: {status} | Actual Tools: {actual_tools}")
                else:
                    print(f"   Error: HTTP {response.status_code}")
            except Exception as e:
                print(f"   Exception: {e}")
            
            print("-" * 50)

    # Generate Report File
    report = "# Agent Robustness Audit Report\n\n"
    report += "| Query | Target Agent | Actual Agent | Target Tool | Status |\n"
    report += "| :--- | :--- | :--- | :--- | :--- |\n"
    for r in results:
        tools_str = ", ".join(r["actual_tools"]) if r["actual_tools"] else "None"
        report += f"| {r['query']} | {r['expected_agent']} | {r['actual_agent']} | {r['expected_tool']} ({tools_str}) | {r['status']} |\n"
    
    with open("agent_audit_report.md", "w") as f:
        f.write(report)
    print("\n📝 Audit Report generated: agent_audit_report.md")

if __name__ == "__main__":
    asyncio.run(run_robust_test())
