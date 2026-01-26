import httpx
import asyncio
import json
from datetime import datetime

# Comprehensive tool tests with agent names
TOOL_TESTS = {
    "getIndexQuotes": [
        "Why is NIFTY 50 down today?",
        "What happened to SENSEX?",
        "Show me NIFTY BANK price"
    ],
    "getQuotes": [
        "Tell me about RELIANCE stock",
        "What's HDFC price?",
        "Show me INFY details"
    ],
    "getMarketDepth": [
        "What is the market depth for NIFTY 50?",
    ],
    "searchNews": [
        "Latest news on Reliance",
        "Tell me recent updates about Indian stock market",
        "Any news on Tata Motors?"
    ],
    "getLimits": [
        "What's my available margin?",
        "Show me my account balance",
        "How much cash do I have?"
    ],
    "getPositions": [
        "Show me my current positions",
        "What are my open positions?"
    ],
    "getWebSocketStatus": [
        "Is the market data connection working?",
        "Check WebSocket status"
    ],
    "navigateTo": [
        "Take me to the funds page",
        "Go to orders section",
        "Navigate to dashboard"
    ]
}

async def test_query(client, query, session_id="final-test"):
    """Test a query and return detailed results."""
    try:
        response = await client.post(
            'http://localhost:8000/agent/chat',
            json={'query': query, 'session_id': session_id}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def validate_with_agent(query, result, expected_tool):
    """Validate response and extract agent info."""
    validation = {
        "query": query,
        "expected_tool": expected_tool,
        "actual_tools": [tc.get('tool') for tc in result.get('mcp_tool_calls', [])],
        "agent_name": result.get('agent', 'Unknown'),
        "response_length": len(result.get('response', {}).get('content', '')),
        "passed": False,
        "issues": []
    }
    
    # Check if expected tool was called
    if expected_tool in validation["actual_tools"]:
        validation["passed"] = True
        validation["issues"].append(f"✅ Tool '{expected_tool}' called correctly")
    else:
        validation["issues"].append(f"❌ Expected '{expected_tool}', got: {validation['actual_tools']}")
    
    # Check response quality
    if validation["response_length"] < 20:
        validation["issues"].append(f"⚠️  Short response ({validation['response_length']} chars)")
        validation["passed"] = False
    else:
        validation["issues"].append(f"✅ Response: {validation['response_length']} chars")
    
    # Check for errors
    if result.get('error'):
        validation["issues"].append(f"⚠️  Error: {result['error']}")
        validation["passed"] = False
    
    return validation

async def run_final_validation():
    """Run final comprehensive validation with agent tracking."""
    results = {}
    total = sum(len(queries) for queries in TOOL_TESTS.values())
    current = 0
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Health check
        try:
            health = await client.get('http://localhost:8000/agent/health')
            print(f"✅ Server healthy\n")
        except:
            print("❌ Server not responding!\n")
            return {}
        
        for tool, queries in TOOL_TESTS.items():
            print(f"\n{'='*70}")
            print(f"Testing: {tool}")
            print('='*70)
            
            results[tool] = {"tests": [], "passed": 0, "failed": 0}
            
            for query in queries:
                current += 1
                print(f"\n[{current}/{total}] {query}")
                
                result = await test_query(client, query)
                validation = validate_with_agent(query, result, tool)
                
                # Print results
                print(f"  Agent: {validation['agent_name']}")
                print(f"  Tools: {validation['actual_tools']}")
                for issue in validation["issues"]:
                    print(f"  {issue}")
                
                results[tool]["tests"].append(validation)
                if validation["passed"]:
                    results[tool]["passed"] += 1
                else:
                    results[tool]["failed"] += 1
                
                await asyncio.sleep(1.5)
    
    return results

def generate_detailed_report(results):
    """Generate comprehensive markdown report with agent names."""
    report = "# 🎯 Final Agent Validation Report\n\n"
    report += f"**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # Summary table
    report += "## Executive Summary\n\n"
    report += "| Tool | Tests | Passed | Failed | Success Rate |\n"
    report += "|------|-------|--------|--------|--------------|\n"
    
    total_tests = total_passed = 0
    for tool, data in results.items():
        tests = len(data["tests"])
        passed = data["passed"]
        rate = f"{(passed/tests*100):.0f}%" if tests > 0 else "0%"
        total_tests += tests
        total_passed += passed
        icon = "✅" if passed == tests else ("⚠️" if passed > 0 else "❌")
        report += f"| {icon} **{tool}** | {tests} | {passed} | {data['failed']} | {rate} |\n"
    
    overall = f"{(total_passed/total_tests*100):.0f}%" if total_tests > 0 else "0%"
    report += f"| **TOTAL** | **{total_tests}** | **{total_passed}** | **{total_tests-total_passed}** | **{overall}** |\n\n"
    
    report += "---\n\n"
    report += "## Detailed Test Results By Tool\n\n"
    
    for tool, data in results.items():
        report += f"### {tool}\n\n"
        
        for test in data["tests"]:
            icon = "✅" if test["passed"] else "❌"
            report += f"#### {icon} \"{test['query']}\"\n\n"
            report += f"**Agent Used:** `{test['agent_name']}`  \n"
            report += f"**Expected Tool:** `{test['expected_tool']}`  \n"
            report += f"**Actual Tools:** `{test['actual_tools']}`  \n"
            report += f"**Response Length:** {test['response_length']} characters  \n\n"
            
            report += "**Validation:**\n"
            for issue in test["issues"]:
                report += f"- {issue}\n"
            
            report += "\n"
        
        report += "---\n\n"
    
    # Agent distribution
    report += "## Agent Distribution\n\n"
    agent_counts = {}
    for tool_data in results.values():
        for test in tool_data["tests"]:
            agent = test["agent_name"]
            agent_counts[agent] = agent_counts.get(agent, 0) + 1
    
    report += "| Agent | Queries Handled |\n"
    report += "|-------|----------------|\n"
    for agent, count in sorted(agent_counts.items(), key=lambda x: x[1], reverse=True):
        report += f"| **{agent}** | {count} |\n"
    
    return report

if __name__ == "__main__":
    print("="*70)
    print("FINAL COMPREHENSIVE AGENT VALIDATION")
    print("="*70)
    
    results = asyncio.run(run_final_validation())
    
    if results:
        print("\n" + "="*70)
        print("GENERATING DETAILED REPORT...")
        print("="*70)
        
        report = generate_detailed_report(results)
        
        with open('final_validation_report.md', 'w') as f:
            f.write(report)
        
        print("\n✅ Report saved to: final_validation_report.md")
    else:
        print("\n❌ Tests failed - check server status")
