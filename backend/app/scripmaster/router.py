from fastapi import APIRouter, Query, HTTPException
from app.scripmaster.service import scrip_master

router = APIRouter(prefix="/scripmaster", tags=["ScripMaster"])

@router.get("/search")
async def search_scrips(q: str = Query(..., min_length=1, description="Search query (symbol or name)")):
    """
    READ-ONLY scrip search endpoint.
    Searches SQLite scrip master loaded at startup.
    Returns matching symbols for autocomplete.
    """
    query = q.upper()
    try:
        results = scrip_master.search_scrips(query)
        return {"data": results}
    except Exception as e:
        # If scrip master is empty or DB error
        return {"data": []}

@router.get("/scrip/{trading_symbol}")
async def get_scrip_details(trading_symbol: str):
    """
    Get full scrip details including metadata for symbol decoding.
    Returns comprehensive instrument data from scrip master CSV.
    """
    scrip = scrip_master.get_scrip(trading_symbol)
    
    if not scrip:
        return {
            "stat": "Not Ok",
            "message": f"Symbol {trading_symbol} not found in scrip master"
        }
    
    return {
        "stat": "Ok",
        "data": scrip
    }
