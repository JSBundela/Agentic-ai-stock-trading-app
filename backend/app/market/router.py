from fastapi import APIRouter, HTTPException
from app.market.service import market_service
from app.market.schemas import QuoteRequest, QuoteResponse
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
