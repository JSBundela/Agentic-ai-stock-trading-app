
import asyncio
import json
import httpx
from app.utils import cache
from app.core.logger import logger

async def check_recent_orders():
    trade_token, trade_sid, base_url, _ = cache.get_trade_session()
    
    if not trade_token or not trade_sid or not base_url:
        print("❌ Not authenticated. Please login first.")
        return
    
    from app.orders.service import order_service
    
    print(f"🔍 Fetching orders for last 3 days...")
    
    try:
        # Use the actual service to get merged orders (Today + DB)
        response_obj = await order_service.get_order_book(days=3)
        
        # Service returns {"stat": "Ok", "data": [...]}
        orders = response_obj.get('data', []) if isinstance(response_obj, dict) else response_obj
        
        if not orders:
            print("📭 No orders found.")
            return
        
        print(f"✅ Found {len(orders)} orders.")
        print("-" * 60)
        
        for order in orders:
            # Kotak fields
            symbol = order.get('trdSym') or order.get('tsym') or order.get('sym')
            order_id = order.get('nOrdNo') or order.get('ordNo')
            status = order.get('stat') or order.get('ordSt') or order.get('status')
            qty = order.get('qty') or order.get('qQty')
            price = order.get('prc') or order.get('pPrc')
            side = order.get('trnsTp') or order.get('trantype') or order.get('side')
            time_str = order.get('ordTm') or order.get('updRecvTm')
            
            # Map side B -> BUY, S -> SELL
            side_display = "BUY" if side == "B" else "SELL" if side == "S" else side
            
            print(f"Scrip:  {symbol}")
            print(f"Side:   {side_display}")
            print(f"Qty:    {qty}")
            print(f"Price:  {price}")
            print(f"Status: {status}")
            print(f"ID:     {order_id}")
            print("-" * 60)
                
    except Exception as e:
        print(f"❌ Error fetching orders: {e}")
                
    except Exception as e:
        print(f"❌ Error fetching orders: {e}")

if __name__ == "__main__":
    asyncio.run(check_recent_orders())
