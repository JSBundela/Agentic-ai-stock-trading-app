from fastapi import APIRouter, HTTPException
from app.market.service import market_service
from app.market.schemas import QuoteRequest, QuoteResponse
from app.mcp import mcp_server
from app.core.logger import logger
from typing import List

router = APIRouter(prefix="/market", tags=["Market Data"])

@router.post("/quotes")
async def get_quotes(request: QuoteRequest):
    """
    Fetch market quotes - returns raw Kotak API response.
    Response fields vary by instrument type.
    """
    try:
        data = await market_service.get_quotes(request.instrument_tokens)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indices/live")
async def get_live_indices(demo: bool = False):
    """
    Get live index prices for NIFTY 50 and SENSEX.
    
    Uses MCP getIndexQuotes tool for real data.
    Falls back to demo mode if `demo=true` query param or if markets closed.
    
    Args:
        demo: Force demo mode even during market hours
    """
    try:
        # If demo mode requested, use simulated data
        if demo:
            from app.market.demo_service import demo_service
            return {
                "success": True,
                "demo_mode": True,
                "data": {
                    "NIFTY_50": demo_service.get_index_quote("NIFTY 50"),
                    "SENSEX": demo_service.get_index_quote("SENSEX")
                }
            }
        
        # Fetch both indices via MCP
        nifty_result = await mcp_server.call_tool("getIndexQuotes", {"index": "NIFTY 50"})
        sensex_result = await mcp_server.call_tool("getIndexQuotes", {"index": "SENSEX"})
        
        # Check if both failed (market closed)
        nifty_success = nifty_result.get("success")
        sensex_success = sensex_result.get("success")
        
        if not nifty_success and not sensex_success:
            # Auto-fallback to demo mode
            logger.info("[LiveIndices] Markets closed, using demo mode")
            from app.market.demo_service import demo_service
            return {
                "success": True,
                "demo_mode": True,
                "data": {
                    "NIFTY_50": demo_service.get_index_quote("NIFTY 50"),
                    "SENSEX": demo_service.get_index_quote("SENSEX")
                }
            }
        
        response = {
            "success": True,
            "demo_mode": False,
            "data": {
                "NIFTY_50": nifty_result.get("data") if nifty_success else {"error": "Data unavailable"},
                "SENSEX": sensex_result.get("data") if sensex_success else {"error": "Data unavailable"}
            }
        }
        
        logger.info(f"[LiveIndices] NIFTY LTP: {nifty_result.get('data', {}).get('ltp')}, SENSEX LTP: {sensex_result.get('data', {}).get('ltp')}")
        
        return response
        
    except Exception as e:
        logger.error(f"[LiveIndices] Error: {e}")
        # Fallback to demo mode on error
        from app.market.demo_service import demo_service
        return {
            "success": True,
            "demo_mode": True,
            "error": f"Live data error: {str(e)}",
            "data": {
                "NIFTY_50": demo_service.get_index_quote("NIFTY 50"),
                "SENSEX": demo_service.get_index_quote("SENSEX")
            }
        }
