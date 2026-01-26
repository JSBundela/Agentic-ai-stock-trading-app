import httpx
import asyncio
import json
from datetime import datetime

# Tool-specific test questions
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

async def test_single_query(client, query, session_id="tool-test"):
    """Test a single query and return results."""
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

def validate_response(query, result, expected_tool):
    """Validate that response matches query requirements."""
    validation = {
        "query": query,
        "expected_tool": expected_tool,
        "passed": False,
        "issues": []
    }
    
    # Check if tool was called
    tools_called = [tc.get('tool') for tc in result.get('mcp_tool_calls', [])]
    
    if expected_tool not in tools_called:
        validation["issues"].append(f"❌ Expected tool '{expected_tool}' was not called. Tools called: {tools_called}")
    else:
        validation["passed"] = True
        validation["issues"].append(f"✅ Tool '{expected_tool}' was called correctly")
    
    # Check for response content
    content = result.get('response', {}).get('content', '')
    if not content or len(content) < 20:
        validation["issues"].append(f"⚠️  Response is too short (< 20 chars): '{content[:50]}'")
        validation["passed"] = False
    else:
        validation["issues"].append(f"✅ Response has meaningful content ({len(content)} chars)")
    
    # Check for errors
    if result.get('error'):
        validation["issues"].append(f"⚠️  Error reported: {result['error']}")
        validation["passed"] = False
    
    # Tool-specific validation
    if expected_tool == "getIndexQuotes" and validation["passed"]:
        if not any(idx in query.upper() for idx in ["NIFTY", "SENSEX", "BANK"]):
            validation["issues"].append("⚠️  Query doesn't mention an index")
    
    if expected_tool == "searchNews" and validation["passed"]:
        if not any(word in content.lower() for word in ["news", "report", "headline", "update"]):
            validation["issues"].append("⚠️  Response doesn't seem to contain news content")
    
    if expected_tool == "navigateTo" and validation["passed"]:
        if "navigat" not in content.lower():
            validation["issues"].append("⚠️  Response doesn't confirm navigation")
    
    return validation

async def run_tool_validation():
    """Run comprehensive tool-by-tool validation."""
    results = {}
    total_tests = sum(len(queries) for queries in TOOL_TESTS.values())
    current_test = 0
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test health first
        try:
            health = await client.get('http://localhost:8000/agent/health')
            print(f"✅ Server health: {health.json()['status']}\n")
        except:
            print("❌ Server is not responding!\n")
            return {}
        
        for tool, queries in TOOL_TESTS.items():
            print(f"\n{'='*60}")
            print(f"Testing: {tool}")
            print(f"{'='*60}\n")
            
            results[tool] = {"tests": [], "passed": 0, "failed": 0}
            
            for query in queries:
                current_test += 1
                print(f"[{current_test}/{total_tests}] {query}")
                
                result = await test_single_query(client, query)
                validation = validate_response(query, result, tool)
                
                # Print validation results
                for issue in validation["issues"]:
                    print(f"  {issue}")
                
                results[tool]["tests"].append(validation)
                if validation["passed"]:
                    results[tool]["passed"] += 1
                else:
                    results[tool]["failed"] += 1
                
                print()
                
                # Small delay to avoid overwhelming server
                await asyncio.sleep(1.5)
    
    return results

def generate_markdown_report(results):
    """Generate detailed markdown validation report."""
    report = f"# Agent Tool Validation Report\n\n"
    report += f"**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # Summary table
    report += "## Summary\n\n"
    report += "| Tool | Tests | Passed | Failed | Success Rate |\n"
    report += "|------|-------|--------|--------|--------------|\n"
    
    total_tests = 0
    total_passed = 0
    
    for tool, data in results.items():
        tests = len(data["tests"])
        passed = data["passed"]
        failed = data["failed"]
        rate = f"{(passed/tests*100):.1f}%" if tests > 0 else "0%"
        
        total_tests += tests
        total_passed += passed
        
        status = "✅" if failed == 0 else "❌"
        report += f"| {status} {tool} | {tests} | {passed} | {failed} | {rate} |\n"
    
    overall_rate = f"{(total_passed/total_tests*100):.1f}%" if total_tests > 0 else "0%"
    report += f"| **TOTAL** | **{total_tests}** | **{total_passed}** | **{total_tests-total_passed}** | **{overall_rate}** |\n\n"
    
    # Detailed results
    report += "---\n\n## Detailed Validation Results\n\n"
    
    for tool, data in results.items():
        report += f"### {tool}\n\n"
        
        for test in data["tests"]:
            status_icon = "✅" if test["passed"] else "❌"
            report += f"#### {status_icon} Query: \"{test['query']}\"\n\n"
            
            for issue in test["issues"]:
                report += f"- {issue}\n"
            
            report += "\n"
        
        report += "---\n\n"
    
    return report

if __name__ == "__main__":
    print("="*60)
    print("TOOL-BY-TOOL VALIDATION TEST")
    print("="*60)
    
    results = asyncio.run(run_tool_validation())
    
    if results:
        print("\n" + "="*60)
        print("GENERATING DETAILED REPORT...")
        print("="*60)
        
        report = generate_markdown_report(results)
        
        with open('tool_validation_report.md', 'w') as f:
            f.write(report)
        
        print("\n✅ Report saved to: tool_validation_report.md")
    else:
        print("\n❌ Tests failed to run - check server status")
