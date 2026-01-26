import httpx
import asyncio
import json

async def verify_multi_intent():
    async with httpx.AsyncClient(timeout=60.0) as client:
        session_id = "multi-verify-session"
        
        print("--- Testing Multi-Intent Query ---")
        query = "Show me a 1-week chart of RELIANCE and tell me the latest news about it."
        r = await client.post('http://localhost:8000/agent/chat', json={
            'query': query,
            'session_id': session_id
        })
        
        result = r.json()
        print(f"Agent: {result.get('agent')}")
        print(f"Intent: {result.get('intent')}")
        print(f"Intents List: {result.get('intents', 'N/A')}")
        
        tool_calls = [tc.get('tool') for tc in result.get('mcp_tool_calls', [])]
        print(f"Tools Called: {tool_calls}")
        
        has_chart = "generateChart" in tool_calls
        has_news = "searchNews" in tool_calls
        
        if has_chart and has_news:
            print("\n✅ SUCCESS: Both Chart and News tools were called parallel/sequentially!")
        else:
            print(f"\n❌ FAILURE: Missing tools. Chart: {has_chart}, News: {has_news}")
            
        print("\nResponse Preview:")
        print(result.get('response', {}).get('content', '')[:200] + "...")

if __name__ == "__main__":
    asyncio.run(verify_multi_intent())
