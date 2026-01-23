from app.core.http_client import http_client
from app.core.logger import logger
from app.orders.schemas import PlaceOrderRequest, ModifyOrderRequest
from app.core.exceptions import OrderError, KotakAPIError
from app.scripmaster.service import scrip_master
from app.utils import cache
import httpx
import json
import asyncio
from datetime import datetime, timedelta

class OrderService:
    # Exchange segment mapping
    SEGMENT_MAP = {
        "nse_cm": "NSE",
        "bse_cm": "BSE",
        "nse_fo": "NFO",
        "bse_fo": "BFO",
        "mcx_fo": "MCX"
    }
    
    # Order type mapping
    ORDER_TYPE_MAP = {
        "LIMIT": "L",
        "MARKET": "MKT",
        "SL": "SL",
        "SL-LMT": "SL",
        "SL-M": "SL-M",
        "SL-MKT": "SL-M"
    }
    
    # Transaction type mapping
    TRANSACTION_TYPE_MAP = {
        "BUY": "B",
        "SELL": "S"
    }
    
    async def get_order_book(self, days: int = 3):
        """
        Fetch orders from order book with date filtering.
        Merges today's Kotak orders with historical orders from local database.
        
        Args:
            days: Number of days to fetch orders for (default: 3)
                  Use 0 or negative for all orders
        
        Per official documentation: GET /quick/user/orders (only returns today's orders)
        """
        trade_token, trade_sid, base_url, _ = cache.get_trade_session()
        
        if not trade_token or not trade_sid or not base_url:
            raise OrderError("Not authenticated. Please complete TOTP + MPIN login first.")
        
        url = f"{base_url}/quick/user/orders"
        
        logger.info(f"GET {url} (fetching today + DB historical for last {days} days)")
        
        try:
            # STEP 1: Get TODAY's orders from Kotak API (live, current status)
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers={
                        "Auth": trade_token,
                        "sid": trade_sid,
                        "neo-fin-key": "neotradeapi"
                    }
                )
                response.raise_for_status()
                
                kotak_result = response.json()
                logger.info(f"Kotak order book status: {kotak_result.get('stat')}")
                
                kotak_orders = kotak_result.get('data', [])
                kotak_order_ids = {order.get('nOrdNo') for order in kotak_orders if order.get('nOrdNo')}
                
                logger.info(f"Kotak returned {len(kotak_orders)} orders (today)")
            
            # STEP 2: Get HISTORICAL orders from local database (if days > 0)
            db_orders = []
            if days > 0:
                try:
                    from app.database.order_repository import order_repository
                    cutoff_date = datetime.now() - timedelta(days=days)
                    db_orders = await order_repository.get_orders_by_date_range(
                        cutoff_date,
                        datetime.now()
                    )
                    logger.info(f"Database returned {len(db_orders)} historical orders")
                except Exception as db_error:
                    logger.warning(f"Failed to fetch historical orders from DB: {db_error}")
            
            # STEP 3: MERGE orders (Kotak takes precedence for today, DB fills historical)
            merged_orders = []
            
            # Add all Kotak orders (today's data with live status)
            merged_orders.extend(kotak_orders)
            
            # Add DB orders that are NOT in Kotak (historical orders)
            for db_order in db_orders:
                order_id = db_order.get('order_id')
                if order_id and order_id not in kotak_order_ids:
                    # Convert DB format to Kotak API format
                    merged_orders.append({
                        'nOrdNo': db_order.get('order_id'),
                        'trdSym': db_order.get('trading_symbol'),
                        'qty': db_order.get('quantity'),
                        'prc': str(db_order.get('price', 0)),
                        'ordSt': db_order.get('status', 'UNKNOWN'),
                        'trnsTp': db_order.get('transaction_type'),
                        'prcTp': db_order.get('order_type'),
                        'prod': db_order.get('product'),
                        'ordDtTm': db_order.get('order_datetime'),
                        'exSeg': db_order.get('exchange'),
                        '_source': 'database'  # Mark as DB source for debugging
                    })
            
            logger.info(f"Merged result: {len(kotak_orders)} Kotak + {len(merged_orders) - len(kotak_orders)} DB = {len(merged_orders)} total")
            
            # Return in Kotak API format
            return {
                "stat": kotak_result.get("stat", "Ok"),
                "data": merged_orders
            }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Order book fetch failed: Status {e.response.status_code}")
            logger.error(f"Full response: {e.response.text}")
            raise OrderError(f"Failed to fetch order book: {e.response.text}")
        except Exception as e:
            logger.error(f"Order book fetch failed: {str(e)}")
            raise OrderError(str(e))
    
    async def get_trade_book(self):
        """
        Fetch all executed trades.
        Per official documentation: GET /quick/user/trades
        """
        trade_token, trade_sid, base_url, _ = cache.get_trade_session()
        
        if not trade_token or not trade_sid or not base_url:
            raise OrderError("Not authenticated. Please complete TOTP + MPIN login first.")
        
        url = f"{base_url}/quick/user/trades"
        
        logger.info(f"GET {url}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers={
                        "Auth": trade_token,
                        "sid": trade_sid,
                        "neo-fin-key": "neotradeapi"
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Trade book status: {result.get('stat')}")
                
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Trade book fetch failed: Status {e.response.status_code}")
            logger.error(f"Full response: {e.response.text}")
            raise OrderError(f"Failed to fetch trade book: {e.response.text}")
        except Exception as e:
            logger.error(f"Trade book fetch failed: {str(e)}")
            raise OrderError(str(e))
    
    async def _verify_order_in_orderbook(self, order_number: str, base_url: str, trade_token: str, trade_sid: str, max_retries: int = 3) -> dict:
        """Verify order in order book with retry logic."""
        url = f"{base_url}/quick/user/orders"
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Checking order book (attempt {attempt + 1}/{max_retries})")
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(
                        url,
                        headers={
                            "Auth": trade_token,
                            "sid": trade_sid,
                            "neo-fin-key": "neotradeapi"
                        }
                    )
                    response.raise_for_status()
                    
                    order_book = response.json()
                    
                    # Search for order in order book
                    if "data" in order_book and isinstance(order_book["data"], list):
                        for order in order_book["data"]:
                            if order.get("nOrdNo") == order_number:
                                return {
                                    "found": True,
                                    "status": order.get("ordSt", "UNKNOWN"),
                                    "message": order.get("rejRsn", "")
                                }
                
                # Order not found, retry after delay (except last attempt)
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    
            except Exception as e:
                logger.error(f"Order book check failed: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
        
        return {"found": False, "status": None, "message": "Order not found in order book"}
    
    async def place_order(self, order: PlaceOrderRequest) -> dict:
        """Places an order and verifies via order book."""
        logger.info(f"Placing order: {order.trading_symbol}")
        
        # Get trade session from cache
        trade_token, trade_sid, base_url, _ = cache.get_trade_session()
        
        if not trade_token or not trade_sid:
            raise OrderError("Not authenticated. Please complete TOTP + MPIN login first.")
        
        if not base_url:
            raise OrderError("Base URL not available. Please re-authenticate.")
        
        # Validate order
        if order.quantity <= 0:
            raise OrderError("Quantity must be greater than 0")
        
        # Get scrip details
        scrip = scrip_master.get_scrip(order.trading_symbol)
        if not scrip:
            raise OrderError(f"Symbol not found in scrip master: {order.trading_symbol}")
        
        instrument_token = scrip.get("instrumentToken", "")
        raw_segment = scrip.get("exchangeSegment", "nse_cm")
        
        logger.info(f"Scrip details: symbol={order.trading_symbol}, token={instrument_token}, segment={raw_segment}")
        
        # Map fields using rules
        exchange_segment = self.SEGMENT_MAP.get(raw_segment, raw_segment)
        order_type = self.ORDER_TYPE_MAP.get(order.order_type, order.order_type)
        transaction_type = self.TRANSACTION_TYPE_MAP.get(order.transaction_type, order.transaction_type)
        
        # Map product code
        product_code = order.product_type
        if product_code == "CASH":
            product_code = "CNC"
        
        if exchange_segment == "NSE":
            if order.product_type == "NRML":
                product_code = "CNC"
        
        # Build OMS endpoint
        url = f"{base_url}/quick/order/rule/ms/place"
        
        # Build OMS jData payload - EXACT format from Kotak documentation
        payload = {
            "am": "YES" if order.amo else "NO",
            "dq": str(order.disclosed_quantity) if order.disclosed_quantity else "0",
            "es": raw_segment,
            "mp": "0",
            "pc": product_code,
            "pf": "N",
            "pr": f"{order.price:.2f}" if order.price else "0",
            "pt": order_type,
            "qt": str(order.quantity),
            "rt": "DAY",
            "tp": "0",
            "ts": order.trading_symbol,
            "tt": transaction_type
        }
        
        # Override retention if not GFD
        if order.validity != "GFD":
            payload["rt"] = order.validity
            
        # Override trigger price for SL/SL-M orders
        if order.trigger_price and order.trigger_price > 0:
            payload["tp"] = f"{order.trigger_price:.2f}"
            
        # BRACKET ORDER FIELDS
        if order.product_type == "BO" or order.product_type == "B":
            # For BO, Kotak usually expects sl, tg, and optionally tsl
            if order.sl_spread:
                payload["sl"] = str(order.sl_spread)
            if order.tg_spread:
                payload["tg"] = str(order.tg_spread)
            if order.trailing_sl:
                payload["tsl"] = str(order.trailing_sl)
            
            # product_code for BO in Kotak Neo is usually "B"
            payload["pc"] = "B"
        
        logger.info(f"POST {url}")
        logger.info(f"OMS jData: {json.dumps(payload)}")
        
        # Wrap in jData parameter for form-encoded submission
        form_data = {"jData": json.dumps(payload, separators=(',', ':'))}
        
        try:
            # STEP 1: Place order using fresh client with form-encoded jData
            async with httpx.AsyncClient(timeout=30.0) as oms_client:
                response = await oms_client.post(
                    url,
                    data=form_data,  # Form-encoded, not JSON
                    headers={
                        "Auth": trade_token,
                        "sid": trade_sid,
                        "neo-fin-key": "neotradeapi"
                    }
                )
                response.raise_for_status()
                response.raise_for_status()
                
                oms_response = response.json()
                logger.info(f"OMS response status: {oms_response.get('stat')}")
                logger.info(f"OMS response status: {oms_response.get('stat')}")
                
                # Check if order was accepted
                if oms_response.get("stat") == "Ok" and "nOrdNo" in oms_response:
                    order_number = oms_response["nOrdNo"]
                    logger.info(f"Order accepted by OMS: {order_number}")
                    
                    # STEP 2: Verify in order book
                    verification = await self._verify_order_in_orderbook(
                        order_number, base_url, trade_token, trade_sid
                    )
                    
                    # STEP 2.5: Save order to local database
                    try:
                        from app.database.order_repository import order_repository
                        await order_repository.save_order({
                            'order_id': order_number,
                            'trading_symbol': order.trading_symbol,
                            'quantity': order.quantity,
                            'price': order.price if order.price else 0,
                            'order_type': order.order_type,
                            'transaction_type': order.transaction_type,
                            'product': order.product_type,
                            'status': verification.get("status", "PENDING"),
                            'exchange': exchange_segment,
                            'order_datetime': datetime.now().strftime('%d-%b-%Y %H:%M:%S'),
                            'kotak_response': json.dumps(oms_response)
                        })
                    except Exception as db_error:
                        logger.error(f"Failed to save order to database: {db_error}")
                        # Don't fail the order placement if DB save fails
                    
                    # STEP 3: Determine final status
                    if verification["found"]:
                        oms_status = verification["status"]
                        
                        # SUCCESS cases
                        if oms_status in ["OPEN", "AMO", "PENDING", "TRIGGER PENDING"]:
                            return {
                                "order_number": order_number,
                                "oms_status": oms_status,
                                "final_result": "SUCCESS",
                                "message": f"Order placed successfully with status: {oms_status}"
                            }
                        
                        # FAILURE cases
                        elif oms_status in ["REJECTED", "CANCELLED"]:
                            return {
                                "order_number": order_number,
                                "oms_status": oms_status,
                                "final_result": "FAILURE",
                                "message": verification["message"] or f"Order {oms_status.lower()}"
                            }
                        
                        # Unknown status
                        else:
                            return {
                                "order_number": order_number,
                                "oms_status": oms_status,
                                "final_result": "UNKNOWN",
                                "message": f"Order in unexpected status: {oms_status}"
                            }
                    else:
                        # Order not found in order book
                        return {
                            "order_number": order_number,
                            "oms_status": "NOT_FOUND",
                            "final_result": "FAILURE",
                            "message": "OMS did not persist order (not found in order book)"
                        }
                else:
                    # Order rejected by OMS
                    raise OrderError(f"Order rejected: {json.dumps(oms_response)}")
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Order placement failed: Status {e.response.status_code}")
            logger.error(f"Full response: {e.response.text}")
            raise OrderError(f"{e.response.text}")
        except OrderError:
            raise
        except Exception as e:
            logger.error(f"Order placement failed: {str(e)}")
            raise OrderError(str(e))
    
    async def modify_order(self, request: ModifyOrderRequest):
        """
        Modify an existing order.
        Per official documentation: POST /quick/order/vr/modify
        Requires fetching original order details from order book first.
        """
        trade_token, trade_sid, base_url, _ = cache.get_trade_session()
        
        if not trade_token or not trade_sid or not base_url:
            raise OrderError("Not authenticated. Please complete TOTP + MPIN login first.")
        
        logger.info(f"Modifying order: {request.order_id}")
        
        # STEP 1: Fetch original order details from order book
        try:
            order_book_url = f"{base_url}/quick/user/orders"
            async with httpx.AsyncClient(timeout=30.0) as client:
                ob_response = await client.get(
                    order_book_url,
                    headers={
                        "Auth": trade_token,
                        "sid": trade_sid,
                        "neo-fin-key": "neotradeapi"
                    }
                )
                ob_response.raise_for_status()
                order_book = ob_response.json()
                
                # Find the order
                original_order = None
                if "data" in order_book and isinstance(order_book["data"], list):
                    for order in order_book["data"]:
                        if order.get("nOrdNo") == request.order_id:
                            original_order = order
                            break
                
                if not original_order:
                    raise OrderError(f"Order {request.order_id} not found in order book")
                
                logger.info(f"Original order status: {original_order.get('ordSt')}")
                
        except Exception as e:
            raise OrderError(f"Failed to fetch order details: {str(e)}")
        
        # STEP 2: Build modify payload using original + new values
        url = f"{base_url}/quick/order/vr/modify"
        
        payload = {
            "no": request.order_id,
            "am": "YES" if original_order.get("ordGenTp") == "AMO" else "NO",
            "es": original_order.get("exSeg", "nse_cm"),
            "ts": original_order.get("trdSym", ""),
            "tt": original_order.get("trnsTp", "B"),
            "pc": original_order.get("prod", "CNC"),
            "pt": original_order.get("prcTp", "L"),
            "qt": str(request.quantity if request.quantity else original_order.get("qty", 1)),
            "pr": f"{float(request.price):.2f}" if request.price else str(original_order.get("prc", "0")),
            "tp": "0",
            "mp": "0",
            "dq": "0",
            "vd": original_order.get("vldt", "DAY")  # FIX: 'vd' not 'rt'
        }
        
        # Override order type if provided
        if request.order_type:
            order_type_map = {"LIMIT": "L", "MARKET": "MKT", "SL": "SL", "SL-M": "SL-M"}
            payload["pt"] = order_type_map.get(request.order_type, "L")
        
        form_data = {"jData": json.dumps(payload, separators=(',', ':'))}
        
        logger.info(f"POST {url}")
        logger.info(f"Modify jData: {json.dumps(payload)}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    data=form_data,
                    headers={
                        "Auth": trade_token,
                        "sid": trade_sid,
                        "neo-fin-key": "neotradeapi"
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Modify response: {result.get('stat')}")
                
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Order modification failed: Status {e.response.status_code}")
            logger.error(f"Full response: {e.response.text}")
            raise OrderError(f"Failed to modify order: {e.response.text}")
        except Exception as e:
            logger.error(f"Order modification failed: {str(e)}")
            raise OrderError(str(e))
    
    async def cancel_order(self, order_id: str):
        """
        Cancel an existing order.
        Per official documentation: POST /quick/order/cancel
        For AMO orders, trading symbol (ts) is required.
        """
        trade_token, trade_sid, base_url, _ = cache.get_trade_session()
        
        if not trade_token or not trade_sid or not base_url:
            raise OrderError("Not authenticated. Please complete TOTP + MPIN login first.")
        
        logger.info(f"Cancelling order: {order_id}")
        
        # STEP 1: Fetch order details to check if AMO
        try:
            order_book_url = f"{base_url}/quick/user/orders"
            async with httpx.AsyncClient(timeout=30.0) as client:
                ob_response = await client.get(
                    order_book_url,
                    headers={
                        "Auth": trade_token,
                        "sid": trade_sid,
                        "neo-fin-key": "neotradeapi"
                    }
                )
                ob_response.raise_for_status()
                order_book = ob_response.json()
                
                # Find the order
                is_amo = False
                trading_symbol = ""
                if "data" in order_book and isinstance(order_book["data"], list):
                    for order in order_book["data"]:
                        if order.get("nOrdNo") == order_id:
                            is_amo = (order.get("ordGenTp") == "AMO")
                            trading_symbol = order.get("trdSym", "")
                            break
                
                logger.info(f"Order is AMO: {is_amo}, symbol: {trading_symbol}")
                
        except Exception as e:
            logger.warning(f"Could not fetch order details: {str(e)}, will try cancel anyway")
            is_amo = False
            trading_symbol = ""
        
        # STEP 2: Build cancel payload
        url = f"{base_url}/quick/order/cancel"
        
        payload = {
            "on": order_id,
            "am": "YES" if is_amo else "NO"
        }
        
        # Add trading symbol for AMO orders
        if is_amo and trading_symbol:
            payload["ts"] = trading_symbol
        
        form_data = {"jData": json.dumps(payload, separators=(',', ':'))}
        
        logger.info(f"POST {url}")
        logger.info(f"Cancel jData: {json.dumps(payload)}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    data=form_data,
                    headers={
                        "Auth": trade_token,
                        "sid": trade_sid,
                        "neo-fin-key": "neotradeapi"
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Cancel response: {result.get('stat')}")
                
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Order cancellation failed: Status {e.response.status_code}")
            logger.error(f"Full response: {e.response.text}")
            raise OrderError(f"Failed to cancel order: {e.response.text}")
        except Exception as e:
            logger.error(f"Order cancellation failed: {str(e)}")
            raise OrderError(str(e))

order_service = OrderService()
