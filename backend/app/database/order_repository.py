"""
Order repository for CRUD operations on order history database.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from app.database import get_db
from app.core.logger import logger


class OrderRepository:
    """Repository for order history database operations."""
    
    async def save_order(self, order_data: Dict) -> bool:
        """Save order to database."""
        try:
            db = await get_db()
            await db.execute("""
                INSERT OR REPLACE INTO order_history 
                (order_id, trading_symbol, quantity, price, order_type, 
                 transaction_type, product, status, exchange, order_datetime, kotak_response, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                order_data.get('order_id'),
                order_data.get('trading_symbol'),
                order_data.get('quantity'),
                order_data.get('price'),
                order_data.get('order_type'),
                order_data.get('transaction_type'),
                order_data.get('product'),
                order_data.get('status', 'PENDING'),
                order_data.get('exchange'),
                order_data.get('order_datetime'),
                order_data.get('kotak_response')
            ))
            await db.commit()
            logger.info(f"Saved order to DB: {order_data.get('order_id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to save order to DB: {e}")
            return False
    
    async def get_orders_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Get orders within a date range.
        """
        try:
            db = await get_db()
            db.row_factory = sqlite3.Row
            
            # Format dates for comparison (assuming ordDtTm format: "08-Jan-2026 14:30:45")
            cursor = await db.execute("""
                SELECT * FROM order_history
                WHERE order_datetime >= ? AND order_datetime <= ?
                ORDER BY order_datetime DESC
            """, (
                start_date.strftime('%d-%b-%Y 00:00:00'),
                end_date.strftime('%d-%b-%Y 23:59:59')
            ))
            
            rows = await cursor.fetchall()
            orders = []
            
            for row in rows:
                order = dict(row)
                if order.get('kotak_response'):
                    try:
                        order['kotak_response'] = json.loads(order['kotak_response'])
                    except:
                        pass
                orders.append(order)
            
            logger.info(f"Retrieved {len(orders)} orders from DB between {start_date.date()} and {end_date.date()}")
            return orders
                
        except Exception as e:
            logger.error(f"Failed to get orders by date range: {e}")
            return []
    
    async def update_order_status(self, order_id: str, new_status: str) -> bool:
        """Update order status."""
        try:
            db = await get_db()
            await db.execute("""
                UPDATE order_history 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE order_id = ?
            """, (new_status, order_id))
            await db.commit()
            logger.debug(f"Updated order {order_id} status to {new_status}")
            return True
        except Exception as e:
            logger.error(f"Failed to update order status: {e}")
            return False
    
    async def get_order_by_id(self, order_id: str) -> Optional[Dict]:
        """
        Get single order by ID.
        
        Args:
            order_id: Order ID
        
        Returns:
            Order dictionary or None
        """
        try:
            async with await get_db() as db:
                db.row_factory = sqlite3.Row
                cursor = await db.execute("""
                    SELECT * FROM order_history WHERE order_id = ?
                """, (order_id,))
                row = await cursor.fetchone()
                
                if row:
                    order = dict(row)
                    if order.get('kotak_response'):
                        try:
                            order['kotak_response'] = json.loads(order['kotak_response'])
                        except:
                            pass
                    return order
                return None
        except Exception as e:
            logger.error(f"Failed to get order by ID: {e}")
            return None
    
    async def get_all_orders(self, limit: int = 1000) -> List[Dict]:
        """
        Get all orders with optional limit.
        
        Args:
            limit: Maximum number of orders to return
        
        Returns:
            List of order dictionaries
        """
        try:
            async with await get_db() as db:
                db.row_factory = sqlite3.Row
                cursor = await db.execute("""
                    SELECT * FROM order_history
                    ORDER BY order_datetime DESC
                    LIMIT ?
                """, (limit,))
                
                rows = await cursor.fetchall()
                orders = [dict(row) for row in rows]
                
                # Parse kotak_response
                for order in orders:
                    if order.get('kotak_response'):
                        try:
                            order['kotak_response'] = json.loads(order['kotak_response'])
                        except:
                            pass
                
                logger.info(f"Retrieved {len(orders)} orders from DB (limit: {limit})")
                return orders
        except Exception as e:
            logger.error(f"Failed to get all orders: {e}")
            return []


# Singleton instance
order_repository = OrderRepository()
