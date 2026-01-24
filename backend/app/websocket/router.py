"""
FastAPI WebSocket Router for Phase 2 Market Data (HSM).
Relays standardized ticks from Kotak HSM to frontend clients.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import asyncio
import json
from app.core.logger import logger
logger.warning("🏁🏁🏁 [ROUTER] MODULE IS LOADING...")
from app.websocket.kotak_ws_hsm import kotak_hsm
from app.utils.cache import get_trade_session, get_view_session
from app.scripmaster.service import scrip_master

router = APIRouter(prefix="/ws", tags=["websocket"])

class ConnectionManager:
    """Manages frontend WebSocket connections and HSM aggregation."""
    
    # KOTAK HSM LIMITS (PHASE 2 MANDATORY)
    MAX_INSTRUMENTS = 200
    MAX_CHANNELS = 16
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        # symbol -> set of websockets
        self.subscriptions: Dict[str, Set[WebSocket]] = {}
        self._hsm_initialized = False

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.debug(f"DEBUG: Frontend client connected. Total clients: {len(self.active_connections)}")
        
        # Initialize Kotak HSM connection on first client
        if not self._hsm_initialized:
            await self._ensure_hsm_connected()
            self._hsm_initialized = True
            kotak_hsm.add_callback(self.broadcast_tick)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Cleanup subscriptions for this socket
        for symbol in list(self.subscriptions.keys()):
            if websocket in self.subscriptions[symbol]:
                self.subscriptions[symbol].remove(websocket)
                if not self.subscriptions[symbol]:
                    del self.subscriptions[symbol]
        
        logger.debug(f"DEBUG: Frontend client disconnected. Total clients: {len(self.active_connections)}")

    async def _ensure_hsm_connected(self):
        """Connect to Kotak HSM using cached session (Trade preferred)."""
        token, sid, _, _ = get_trade_session()
        session_type = "TRADE"
        
        if not token:
            token, sid = get_view_session()
            session_type = "VIEW"

        logger.warning(f"🏁🏁🏁 [ROUTER] ensure_hsm_connected ({session_type}): exists={token is not None}")
        
        if token and sid:
            try:
                await kotak_hsm.connect(token, sid)
                logger.warning(f"🏁🏁🏁 [ROUTER] Broker connected to Kotak HSM ({session_type})")
            except Exception as e:
                logger.error(f"❌ [ROUTER] Broker failed to connect to HSM: {e}")
        else:
            logger.warning("⚠️ [ROUTER] No active session found in cache.")

    async def subscribe_client(self, websocket: WebSocket, symbol: str):
        """Register client for a symbol and subscribe in HSM if new."""
        subscription_string = ""
        normalized_symbol = symbol

        # 0. DIRECT TOKEN SUBSCRIPTION (Bypass Scrip Master)
        # Used for Indices: "nse_cm|Nifty 50" or "nse_cm|26000"
        if "|" in symbol:
            logger.info(f"⚡ [ROUTER] Direct token subscription detected: {symbol}")
            subscription_string = symbol
            # Ensure it ends with & for Kotak API if not present (logic below adds it if needed, but standardizing here helps)
        else:
            # 1. Validate symbol via Scrip Master (SINGLE SOURCE OF TRUTH)
            scrip = scrip_master.get_scrip(symbol)
            
            # Fallback: Try without common suffixes (e.g., BEL-EQ -> BEL)
            if not scrip and "-" in symbol:
                base_symbol = symbol.split("-")[0]
                logger.debug(f"Symbol {symbol} not found. Retrying with base: {base_symbol}")
                scrip = scrip_master.get_scrip(base_symbol)
                if scrip:
                    logger.info(f"✅ Found match for {symbol} using base symbol {base_symbol}")
                    normalized_symbol = base_symbol
            
            if not scrip:
                logger.warning(f"Rejected local subscription: reason=UNKNOWN_SYMBOL, symbol={symbol}")
                return
            
            # Construct standard Kotak subscription string
            subscription_string = f"{scrip['exchangeSegment']}|{scrip['instrumentToken']}"

        # 2. Add to local subscriber sets (use the original requested symbol or normalized one as key)
        # Note: For direct tokens, we use the token string as the key
        
        if normalized_symbol not in self.subscriptions:
            # 3. ENFORCE HSM LIMITS (PHASE 2 MANDATORY)
            if len(self.subscriptions) >= self.MAX_INSTRUMENTS:
                logger.warning(f"Rejected HSM subscription: reason=MAX_INSTRUMENTS_REACHED, limit={self.MAX_INSTRUMENTS}, symbol={symbol}")
                await websocket.send_json({"type": "error", "message": "Global HSM subscription limit reached"})
                return

            self.subscriptions[normalized_symbol] = set()
            
            # 4. Trigger HSM subscription
            if not subscription_string.endswith("&"):
                subscription_string += "&"
                
            if kotak_hsm.connected:
                await kotak_hsm.subscribe(subscription_string)
            else:
                logger.warning(f"HSM not connected. Queuing subscription for {normalized_symbol}")
        
        self.subscriptions[normalized_symbol].add(websocket)
        logger.info(f"Client subscribed to {normalized_symbol}. Active instruments: {len(self.subscriptions)}")

    async def broadcast_tick(self, tick: dict):
        """Relay standardized tick to all interested clients."""
        symbol = tick.get('symbol')
        if symbol in self.subscriptions:
            message = json.dumps(tick)
            dead_links = []
            for ws in self.subscriptions[symbol]:
                try:
                    await ws.send_text(message)
                except Exception:
                    dead_links.append(ws)
            
            # Concurrent cleanup
            for dead in dead_links:
                self.disconnect(dead)

    async def resubscribe_all(self):
        """Resubscribe to all active symbols (e.g. after HSM reconnect)."""
        logger.info(f"🔄 Resubscribing to {len(self.subscriptions)} symbols after HSM reconnect...")
        for symbol in self.subscriptions:
            scrip = scrip_master.get_scrip(symbol)
            if scrip:
                sub_str = f"{scrip['exchangeSegment']}|{scrip['instrumentToken']}&"
                if kotak_hsm.connected:
                    await kotak_hsm.subscribe(sub_str)
        logger.info("✅ Resubscription complete.")

manager = ConnectionManager()
# Register callback for auto-resubscription
kotak_hsm.add_connect_callback(manager.resubscribe_all)

@router.websocket("/market-data")
async def market_data_websocket(websocket: WebSocket):
    logger.warning("🏁🏁🏁 [ROUTER] NEW FRONTEND CONNECTION")
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"RECEIVED FROM FRONTEND: {data}")
            try:
                msg = json.loads(data)
                # Support both 'type' (backend standard) and 'action' (frontend legacy/V3)
                action = msg.get("action") or msg.get("type")
                symbols = msg.get("symbols", [])
                
                if not isinstance(symbols, list):
                    symbols = [symbols]

                if action == "subscribe":
                    # CRITICAL: Check if scrip master is ready
                    if scrip_master.scrip_data is None or scrip_master.scrip_data.empty:
                        logger.warning("Subscription rejected: Scrip Master not ready")
                        await websocket.send_json({
                            "type": "error",
                            "message": "Market data engine initializing (Scrip Master loading). Please wait ~60s.",
                            "code": "SCRIP_NOT_READY"
                        })
                        continue

                    for sym in symbols:
                        await manager.subscribe_client(websocket, str(sym))
                
                elif action == "unsubscribe":
                    # Local cleanup (HSM aggregation remains for other clients)
                    for sym in symbols:
                        if sym in manager.subscriptions and websocket in manager.subscriptions[sym]:
                            manager.subscriptions[sym].remove(websocket)
                            
            except json.JSONDecodeError:
                continue
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
        manager.disconnect(websocket)
