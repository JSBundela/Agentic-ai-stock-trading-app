from pydantic import BaseModel, Field
from typing import Optional

class PlaceOrderRequest(BaseModel):
    """
    Place order request - pre-filled with BEL-EQ test order.
    Just click Execute to place a market order!
    """
    trading_symbol: str = Field(default="BEL-EQ", description="Trading symbol from scrip master")
    transaction_type: str = Field(default="BUY", description="BUY or SELL")
    order_type: str = Field(default="MARKET", description="LIMIT, MARKET, SL, SL-M")
    product_type: str = Field(default="CNC", description="CNC (delivery), MIS (intraday), NRML")
    quantity: int = Field(default=1, description="Order quantity")
    price: Optional[float] = Field(default=0, description="Price (0 for market orders)")
    trigger_price: Optional[float] = Field(default=0, description="Trigger price for SL orders")
    validity: str = Field(default="GFD", description="GFD (Day), IOC")
    amo: bool = Field(default=False, description="After Market Order")
    disclosed_quantity: Optional[int] = Field(default=0, description="Disclosed quantity for large orders")
    
    # Bracket Order Details (optional)
    sl_spread: Optional[float] = Field(default=None, description="Stoploss spread for Bracket Orders")
    tg_spread: Optional[float] = Field(default=None, description="Target spread for Bracket Orders")
    trailing_sl: Optional[float] = Field(default=None, description="Trailing Stoploss step for Bracket Orders")
    
    class Config:
        json_schema_extra = {
            "example": {
                "trading_symbol": "BEL-EQ",
                "transaction_type": "BUY",
                "order_type": "MARKET",
                "product_type": "CNC",
                "quantity": 1,
                "price": 0,
                "trigger_price": 0,
                "validity": "GFD",
                "amo": False
            }
        }

class OrderResponse(BaseModel):
    order_number: str
    status: str
    message: Optional[str] = None
    new_price: Optional[float] = None
    new_trigger_price: Optional[float] = None

class ModifyOrderRequest(BaseModel):
    """
    Modify order request - update order parameters.
    """
    order_id: str = Field(description="Order number (nOrdNo) to modify")
    quantity: Optional[int] = Field(default=None, description="New quantity")
    price: Optional[float] = Field(default=None, description="New price")
    order_type: Optional[str] = Field(default=None, description="New order type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "260106000727961",
                "quantity": 2,
                "price": 350.0,
                "order_type": "LIMIT"
            }
        }
