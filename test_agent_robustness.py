import asyncio
import httpx
import json
import time
from typing import List, Dict

# Configuration
API_URL = "http://localhost:8000/agent/chat"
REPORT_FILE = "agent_robustness_report.md"

# Test Questions
TEST_CASES = [
    # --- Market Data (MARKET_EXPLAINER) ---
    "What is the current price of RELIANCE-EQ?",
    "Show me the market depth for TCS.",
    "Get me the quote for HDFCBANK.",
    "How is NIFTY 50 performing right now?",
    "Check the price of INFIBEAM.",
    "What is the volume for TATAMOTORS?",
    "Is SENSEX up or down today?",
    "Get detailed quote for SBIN.",

    # --- News & Trends (TREND_NEWS) ---
    "What is the latest news on Adani Enterprises?",
    "Find recent news about the IT sector.",
    "Any updates on RBI monetary policy?",
    "Search for news regarding electric vehicles in India.",
    "What is the news sentiment for Banking stocks?",
    "Latest announcements for Infosys.",
    "What is happening with Gold prices?",
    
    # --- UI Navigation (UI_NAVIGATION) ---
    "Take me to the dashboard.",
    "Go to the order book.",
    "I want to see my open positions.",
    "Show me my funds and limits.",
    "Navigate to the option chain.",
    "Open the profile settings.",
    "I want to place a new order.",
    "Go back to the home page.",

    # --- Data & Concepts (DATA_INTERPRETER) ---
    "What is the difference between CNC and MIS?",
    "Explain what a limit order is.",
    "How is margin calculated?",
    "What does market depth mean?",
    "Why would an order be rejected?",
    "What is a stop-loss order?",

    # --- Portfolio & Account (General/Portfolio context) ---
    "How much cash do I have available?",
    "Show me my rejected orders.",
    "What is my total P&L for today?",
    "List all my executed orders.",
    "Do I have any open buy orders?"
]

async def run_test():
    results = []
    print(f"🚀 Starting Robustness Test with {len(TEST_CASES)} questions...\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, query in enumerate(TEST_CASES, 1):
            print(f"[{i}/{len(TEST_CASES)}] Asking: {query}")
            start_time = time.time()
            
            try:
                response = await client.post(API_URL, json={"query": query})
                elapsed = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    success = data.get("success", False)
                    agent = data.get("agent", "Unknown")
                    tools = data.get("mcp_tool_calls", [])
                    tool_names = [t.get("tool") for t in tools] if tools else ["None"]
                    
                    results.append({
                        "id": i,
                        "query": query,
                        "status": "PASS" if success else "FAIL",
                        "agent": agent,
                        "tools": tool_names,
                        "latency": f"{elapsed:.2f}s",
                        "response_preview": str(data.get("response", {}).get("content", ""))[:100] + "..."
                    })
                else:
                    results.append({
                        "id": i,
                        "query": query,
                        "status": "ERROR",
                        "agent": "N/A",
                        "tools": [],
                        "latency": f"{elapsed:.2f}s",
                        "response_preview": f"HTTP {response.status_code}: {response.text}"
                    })
                    
            except Exception as e:
                results.append({
                    "id": i,
                    "query": query,
                    "status": "EXCEPTION",
                    "agent": "N/A",
                    "tools": [],
                    "latency": "0.00s",
                    "response_preview": str(e)
                })
            
            # Brief pause to avoid overwhelming local LLM if applicable
            await asyncio.sleep(0.5)

    # Generate Report
    generate_report(results)

def generate_report(results: List[Dict]):
    print(f"\n📝 Generating Report: {REPORT_FILE}")
    
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    total_count = len(results)
    
    markdown = f"""# Agent Robustness Test Report

**Date**: {time.strftime("%Y-%m-%d %H:%M:%S")}
**Total Questions**: {total_count}
**Passed**: {pass_count}
**Failed**: {total_count - pass_count}
**Success Rate**: {(pass_count/total_count)*100:.1f}%

## detailed Results

| ID | Question | Status | Agent Used | Tools Used | Latency |
|----|----------|--------|------------|------------|---------|
"""
    
    for r in results:
        tools_str = ", ".join(r["tools"])
        markdown += f"| {r['id']} | {r['query']} | {r['status']} | {r['agent']} | {tools_str} | {r['latency']} |\n"
    
    markdown += "\n## Tool Utilization Strategy\n"
    markdown += "The following tools were exercised during this test suite:\n"
    
    all_tools = set()
    for r in results:
        for t in r["tools"]:
            all_tools.add(t)
            
    for t in sorted(list(all_tools)):
        markdown += f"- {t}\n"

    with open(REPORT_FILE, "w") as f:
        f.write(markdown)
        
    print("✅ Report Generated.")

if __name__ == "__main__":
    asyncio.run(run_test())
