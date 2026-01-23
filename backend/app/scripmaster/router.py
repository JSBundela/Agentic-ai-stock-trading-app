from fastapi import APIRouter, Query, HTTPException
from app.scripmaster.service import scrip_master

router = APIRouter(prefix="/scripmaster", tags=["ScripMaster"])

@router.get("/search")
async def search_scrips(q: str = Query(..., min_length=1, description="Search query (symbol or name)")):
    """
    READ-ONLY scrip search endpoint.
    Searches in-memory scrip master loaded at startup.
    Returns matching symbols for autocomplete.
    """
    if scrip_master.scrip_data is None or scrip_master.scrip_data.empty:
        # If scrip master is empty, session probably lost or reload required
        raise HTTPException(status_code=401, detail="Scrip master not loaded. Please login again.")
    
    df = scrip_master.scrip_data
    query = q.upper()
    
    # Match symbols or company names
    mask = (df.index.str.contains(query, case=False, na=False)) | \
           (df['companyName'].str.contains(query, case=False, na=False))
    matches = df[mask]
    
    # Reset index to get tradingSymbol as a column for result extraction
    results_df = matches.head(20).reset_index()
    # Replace NaN with None for JSON serialization
    results = results_df.where(results_df.notna(), None).to_dict('records')
    
    return {"data": results}

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
