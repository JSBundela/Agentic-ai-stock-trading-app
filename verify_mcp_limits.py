import asyncio
import json
from app.mcp.mcp_tools import mcp_tools

async def test_mcp_limits():
    print("Testing MCP getLimits tool...")
    try:
        result = await mcp_tools.get_limits()
        print(f"Success: {result.success}")
        if result.success:
            print(f"Data: {result.data.model_dump()}")
            # Check for non-None values if possible (depends on session)
            # Based on debug_limits.json, we expect Net=40, CollateralValue=40
            data = result.data
            if data.cash_available is not None:
                print(f"✅ Cash Available: {data.cash_available}")
            else:
                print("❌ Cash Available is None (Check mapping!)")
                
            if data.collateral is not None:
                print(f"✅ Collateral: {data.collateral}")
            else:
                print("❌ Collateral is None (Check mapping!)")
        else:
            print(f"Error: {result.data.error}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_limits())
