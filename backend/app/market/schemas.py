from pydantic import BaseModel, Field
from typing import List, Optional

class QuoteRequest(BaseModel):
    """
    Request body for market quotes.
    Format: exchange_segment|instrument_token
    Examples: 
    - Stocks: nse_cm|11536 (TCS), nse_cm|383 (BEL)
    - Indices: nse_cm|Nifty 50, bse_cm|SENSEX
    """
    instrument_tokens: List[str] = Field(
        default=["nse_cm|Nifty 50", "nse_cm|11536"],
        description="List of instruments in format: exchange_segment|token",
        examples=[
            ["nse_cm|Nifty 50", "nse_cm|11536"],  # Nifty 50 index + TCS
            ["nse_cm|383", "bse_cm|SENSEX"]       # BEL + SENSEX
        ]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "instrument_tokens": ["nse_cm|Nifty 50", "nse_cm|11536"]
            }
        }

class QuoteResponse(BaseModel):
    instrument_token: str
    ltp: float
    change: float
    change_percent: float
    volume: int
    
class MarketDepth(BaseModel):
    buy_orders: List[dict]
    sell_orders: List[dict]
