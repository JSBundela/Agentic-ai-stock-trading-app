import httpx
import asyncio
import json
from datetime import datetime

# Comprehensive test questions covering all tools and capabilities
TEST_QUESTIONS = [
    # Market Explainer + getIndexQuotes
    "Why is NIFTY 50 down today?",
    "What happened to SENSEX recently?",
    "Explain the movement in NIFTY BANK",
    
    # Market Explainer + getQuotes
    "Tell me about RELIANCE stock price",
    "What's happening with HDFC Bank?",
    "Show me INFY price movement",
    
    # Market Explainer + generateChart
    "Show me a 1-month chart of TATAMOTORS",
    "Generate a 6-month chart for NIFTY 50",
    "Plot a 1-year graph of RELIANCE",
    
    # Market Explainer + getMarketDepth
    "What is the market depth for NIFTY 50?",
    
    # Trend News + searchNews
    "What's the latest news on Reliance Industries?",
    "Tell me recent updates about Indian stock market",
    "Any news on Tata Motors?",
    "What are the headlines for SBI?",
    
    # Data Interpreter + getLimits
    "What's my available margin?",
    "Show me my account balance",
    "How much cash do I have available?",
    
    # Data Interpreter + getPositions
    "Show me my current positions",
    "What are my open positions?",
    
    # Data Interpreter + getWebSocketStatus
    "Is the market data connection working?",
    "Check WebSocket status",
    
    # UI Navigation + navigateTo
    "Take me to the funds page",
    "Go to orders section",
    "Navigate to dashboard",
    
    # Multi-Intent (Chart + News)
    "Show me a 1-week chart of RELIANCE and tell me the latest news about it",
    "Get me NIFTY chart and recent market updates"
]

async def run_comprehensive_test():
    """Run all test questions and collect results."""
    results = []
    session_id = f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for idx, question in enumerate(TEST_QUESTIONS, 1):
            print(f"\n[{idx}/25] Testing: {question}")
            
            try:
                response = await client.post(
                    'http://localhost:8000/agent/chat',
                    json={'query': question, 'session_id': session_id}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract key information
                    result = {
                        'question_num': idx,
                        'question': question,
                        'success': data.get('success', False),
                        'agent': data.get('agent', 'Unknown'),
                        'intent': data.get('intent', 'Unknown'),
                        'response': data.get('response', {}).get('content', ''),
                        'tools_called': [tc.get('tool') for tc in data.get('mcp_tool_calls', [])],
                        'error': data.get('error')
                    }
                    
                    print(f"  ✓ Agent: {result['agent']}")
                    print(f"  ✓ Tools: {', '.join(result['tools_called']) if result['tools_called'] else 'None'}")
                    
                else:
                    result = {
                        'question_num': idx,
                        'question': question,
                        'success': False,
                        'error': f"HTTP {response.status_code}"
                    }
                    print(f"  ✗ HTTP Error: {response.status_code}")
                
            except Exception as e:
                result = {
                    'question_num': idx,
                    'question': question,
                    'success': False,
                    'error': str(e)
                }
                print(f"  ✗ Exception: {str(e)[:100]}")
            
            results.append(result)
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(2)
    
    return results

async def generate_report(results):
    """Generate a detailed markdown report."""
    
    # Calculate statistics
    total = len(results)
    successful = sum(1 for r in results if r.get('success'))
    failed = total - successful
    
    # Count tool usage
    tool_usage = {}
    for result in results:
        for tool in result.get('tools_called', []):
            tool_usage[tool] = tool_usage.get(tool, 0) + 1
    
    # Generate report
    report = f"""# Agent Comprehensive Test Report
    
**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Questions:** {total}  
**Successful:** {successful} ({successful/total*100:.1f}%)  
**Failed:** {failed} ({failed/total*100:.1f}%)

---

## Tool Usage Summary

"""
    
    for tool, count in sorted(tool_usage.items(), key=lambda x: x[1], reverse=True):
        report += f"- **{tool}**: {count} calls\n"
    
    report += "\n---\n\n## Detailed Results\n\n"
    
    for result in results:
        report += f"### Q{result['question_num']}: {result['question']}\n\n"
        
        if result.get('success'):
            # Build response summary
            response_text = result.get('response', '')
            
            # Extract bullet points if present
            bullets = []
            if '•' in response_text or '-' in response_text:
                lines = response_text.split('\n')
                bullets = [line.strip() for line in lines if line.strip().startswith(('•', '-', '*'))]
            
            report += f"**Agent:** {result.get('agent', 'Unknown')}  \n"
            report += f"**Intent:** {result.get('intent', 'Unknown')}  \n"
            report += f"**Tools Used:** {', '.join(result.get('tools_called', [])) if result.get('tools_called') else 'None'}  \n\n"
            
            report += "**Response:**\n\n"
            
            if bullets and len(bullets) >= 3:
                for bullet in bullets[:5]:
                    report += f"{bullet}\n"
                report += "\n"
            else:
                # Use first 500 chars as summary
                summary = response_text[:500].strip()
                if len(response_text) > 500:
                    summary += "..."
                report += f"{summary}\n\n"
        else:
            report += f"**Status:** ❌ Failed  \n"
            report += f"**Error:** {result.get('error', 'Unknown error')}  \n\n"
        
        report += "---\n\n"
    
    return report

if __name__ == "__main__":
    print("=" * 60)
    print("AGENT COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    results = asyncio.run(run_comprehensive_test())
    
    print("\n" + "=" * 60)
    print("GENERATING REPORT...")
    print("=" * 60)
    
    report = asyncio.run(generate_report(results))
    
    # Save report
    with open('agent_test_report.md', 'w') as f:
        f.write(report)
    
    print("\n✓ Report saved to: agent_test_report.md")
