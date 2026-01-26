import httpx
import asyncio
import json

async def verify_memory():
    async with httpx.AsyncClient() as client:
        session_id = f"test-session-{json.dumps(asyncio.get_event_loop().is_running())}"
        
        print("--- Step 1: Set Context ---")
        r1 = await client.post('http://localhost:8000/agent/chat', json={
            'query': 'I want to know about RELIANCE',
            'session_id': session_id
        }, timeout=30)
        print(f"Step 1 Response: {r1.json().get('agent')}")
        
        print("\n--- Step 2: Contextual Query (Memory Check) ---")
        # Agent should remember RELIANCE from Step 1
        r2 = await client.post('http://localhost:8000/agent/chat', json={
            'query': 'Why is it up?', 
            'session_id': session_id
        }, timeout=30)
        
        result = r2.json()
        print(f"Step 2 Response: {result.get('agent')}")
        print(f"Intent: {result.get('intent')}")
        
        tool_calls = result.get('mcp_tool_calls', [])
        found_reliance = any('RELIANCE' in str(tc) for tc in tool_calls)
        
        if found_reliance:
            print("\n✅ SUCCESS: Agent remembered RELIANCE from history!")
        else:
            print("\n❌ FAILURE: Agent did not use memory to identify 'it'.")
            print(f"Tool Calls: {tool_calls}")

if __name__ == "__main__":
    asyncio.run(verify_memory())
