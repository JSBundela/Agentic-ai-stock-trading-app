from fastapi import APIRouter, HTTPException
from app.orders.service import order_service
from app.orders.schemas import PlaceOrderRequest, ModifyOrderRequest, OrderResponse

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/place")
async def place_order(order: PlaceOrderRequest):
    try:
        # Returns actual Kotak API response
        result = await order_service.place_order(order)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/order-book")
async def get_order_book(days: int = 3):
    """
    Fetch orders from order book.
    
    Args:
        days: Number of days to fetch orders for (default: 3)
              Use 0 or negative for all orders
    
    Per official documentation: GET /quick/user/orders
    """
    try:
        result = await order_service.get_order_book(days=days)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/trade-book")
async def get_trade_book():
    """
    Fetch all executed trades.
    Per official documentation: GET /quick/user/trades
    """
    try:
        result = await order_service.get_trade_book()
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/modify")
async def modify_order(request: ModifyOrderRequest):
    try:
        await order_service.modify_order(request)
        return {"message": "Order modified"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{order_id}")
async def cancel_order(order_id: str):
    try:
        await order_service.cancel_order(order_id)
        return {"message": "Order cancelled"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
