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
async def get_live_indices():
    """
    Get live index prices for NIFTY 50 and SENSEX.
    
    Uses MCP getIndexQuotes tool.
    Returns live data ONLY (no fallback to dummy data).
    """
    try:
        # Fetch both indices
        nifty_result = await mcp_server.call_tool("getIndexQuotes", {"index": "NIFTY 50"})
        sensex_result = await mcp_server.call_tool("getIndexQuotes", {"index": "SENSEX"})
        
        response = {
            "success": True,
            "data": {
                "NIFTY_50": nifty_result.get("data") if nifty_result.get("success") else {"error": "Data unavailable"},
                "SENSEX": sensex_result.get("data") if sensex_result.get("success") else {"error": "Data unavailable"}
            }
        }
        
        logger.info(f"[LiveIndices] NIFTY LTP: {nifty_result.get('data', {}).get('ltp')}, SENSEX LTP: {sensex_result.get('data', {}).get('ltp')}")
        
        return response
        
    except Exception as e:
        logger.error(f"[LiveIndices] Error: {e}")
        # Return error structure (NO fallback data)
        return {
            "success": False,
            "error": str(e),
            "data": {
                "NIFTY_50": {"error": "Live data unavailable"},
                "SENSEX": {"error": "Live data unavailable"}
            }
        }
