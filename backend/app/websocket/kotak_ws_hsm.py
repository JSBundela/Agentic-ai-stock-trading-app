import asyncio
import json
import websockets
import time
import struct
from typing import Dict, List, Callable, Optional, Set
from app.core.logger import logger
from app.scripmaster.service import scrip_master
from app.utils.symbol_formatter import format_display_name
from app.utils.market_hours import get_market_session_info

# --- Binary Protocol Constants (from hslib.js) ---
class BinTypes:
    CONNECTION_TYPE = 1
    THROTTLING_TYPE = 2
    ACK_TYPE = 3
    SUBSCRIBE_TYPE = 4
    UNSUBSCRIBE_TYPE = 5
    DATA_TYPE = 6

class ResponseTypes:
    SNAP = 83    # 'S'
    UPDATE = 85  # 'U'

class TopicTypes:
    SCRIP = "sf"
    INDEX = "if"
    DEPTH = "dp"

class FieldTypes:
    FLOAT32 = 1
    LONG = 2
    DATE = 3
    STRING = 4

# Map indices to names and types (from SCRIP_MAPPING in hslib.js)
SCRIP_MAP = {
    4: ("v", FieldTypes.LONG),
    5: ("ltp", FieldTypes.FLOAT32),
    6: ("ltq", FieldTypes.LONG),
    9: ("bp", FieldTypes.FLOAT32),
    10: ("sp", FieldTypes.FLOAT32),
    14: ("lo", FieldTypes.FLOAT32),
    15: ("h", FieldTypes.FLOAT32),
    20: ("op", FieldTypes.FLOAT32),
    21: ("c", FieldTypes.FLOAT32),
    23: ("mul", FieldTypes.LONG),
    24: ("prec", FieldTypes.LONG),
    52: ("tk", FieldTypes.STRING),
    53: ("e", FieldTypes.STRING),
}

class KotakHSMClient:
    """
    Kotak Neo Market Data (HSM) Binary WebSocket Client.
    Uses the discovered binary protocol (Phase 3).
    """
    
    def __init__(self):
        self.url = "wss://mlhsm.kotaksecurities.com"
        self.ws = None
        self.connected = False
        self.session_token = None
        self.sid = None
        
        # Internal state
        self._heartbeat_task = None
        self._listen_task = None
        self._callbacks: List[Callable] = []
        
        # Topic ID -> Topic Info
        self._topics: Dict[int, dict] = {}
        
        self._connect_callbacks = []

    def add_connect_callback(self, cb):
        self._connect_callbacks.append(cb)
        
    async def connect(self, session_token: str, sid: str):
        """Connect to HSM and perform binary handshake."""
        print(f"💎💎💎 [HSM] Binary connect: token={session_token[:10]}...")
        self.session_token = session_token
        self.sid = sid
        
        try:
            print(f"🚀 [HSM] Connecting (Binary Mode) to {self.url}...")
            # Headers are still required for the initial upgrade
            additional_headers = {
                "sid": sid,
                "Authorization": session_token # NO BEARER per neo.js/hslib.js findings
            }
            
            self.ws = await asyncio.wait_for(
                websockets.connect(self.url, additional_headers=additional_headers), 
                timeout=10.0
            )
            print("🔗 [HSM] Binary Connection OPENED")
            
            # --- BUILD BINARY HANDSHAKE ---
            src = "JS_API"
            # Field 1: JWT (Token)
            f1 = b"\x01" + struct.pack(">H", len(session_token)) + session_token.encode()
            # Field 2: SID
            f2 = b"\x02" + struct.pack(">H", len(sid)) + sid.encode()
            # Field 3: SRC
            f3 = b"\x03" + struct.pack(">H", len(src)) + src.encode()
            
            packet = struct.pack("BB", BinTypes.CONNECTION_TYPE, 3) + f1 + f2 + f3
            handshake = struct.pack(">H", len(packet)) + packet
            
            print(f"📤 [HSM] Sending Binary Handshake ({len(handshake)} bytes)...")
            await self.ws.send(handshake)
            
            self.connected = True
            
            # Start Heartbeat (Uses type 'ti' but we'll adapt to binary if needed)
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # Start Listener
            if self._listen_task:
                self._listen_task.cancel()
            self._listen_task = asyncio.create_task(self._listen_loop())
            
            logger.info(f"🚀 Kotak HSM Client initialized (Binary). Handshake sent. Callbacks: {len(self._connect_callbacks)}")
            
            # Notify on_connect listeners (e.g. for resubscription)
            for cb in self._connect_callbacks:
                try:
                    if asyncio.iscoroutinefunction(cb): asyncio.create_task(cb())
                    else: cb()
                except Exception as e:
                    logger.error(f"Error in on_connect callback: {e}")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Kotak HSM (Binary): {e}")
            self.connected = False
            raise
            
    async def _heartbeat_loop(self):
        """Official Heartbeat: {"type": "ti", "scrips": ""} JSON is still accepted for timing info."""
        # Note: If JSON heartbeats cause issues, we may need binary throttling interval packets.
        while self.connected:
            try:
                await asyncio.sleep(25)
                if self.ws:
                    # Kotak Neo sometimes accepts JSON heartbeat even on binary socket
                    await self.ws.send(json.dumps({"type": "ti", "scrips": ""}))
                    logger.debug("💓 HSM Heartbeat sent")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"HSM Heartbeat error: {e}")
                self.connected = False
                break
                
    async def _listen_loop(self):
        """Listen for binary packets from Kotak."""
        should_reconnect = True
        try:
            async for message in self.ws:
                if isinstance(message, bytes):
                    await self._process_binary_message(message)
                else:
                    # In case they send JSON status messages
                    try:
                        data = json.loads(message)
                        if data.get("type") == "cn" and data.get("stat") == "Ok":
                            logger.info("💎💎💎 HSM Handshake SUCCESS (via JSON)")
                    except Exception:
                        pass
        except asyncio.CancelledError:
            logger.info("HSM Listener cancelled - stopping.")
            should_reconnect = False
            raise
        except (websockets.ConnectionClosed, Exception) as e:
            logger.warning(f"Kotak HSM connection lost: {e}")
        finally:
            self.connected = False
            close_code = getattr(self.ws, 'close_code', 'Unknown')
            logger.warning(f"⚠️ HSM Listener stopped (Close Code: {close_code}). Reconnect={should_reconnect}")
            
            if should_reconnect:
                await asyncio.sleep(5)
                # Reconnect using stored credentials
                if hasattr(self, 'session_token') and hasattr(self, 'sid'):
                    asyncio.create_task(self.connect(self.session_token, self.sid))

    async def _process_binary_message(self, message: bytes):
        """Parse the binary protocol packets."""
        if len(message) < 3:
            return
        
        # First 2 bytes: Packet Length
        msg_len = struct.unpack(">H", message[:2])[0]
        body = message[2:]
        
        if len(body) < 1:
            return
            
        packet_type = body[0]
        
        if packet_type == BinTypes.CONNECTION_TYPE:
            status = self._parse_status_packet(body)
            if status == "K": # OK
                print("💎💎💎 BINARY HSM Handshake SUCCESS - ACK RECEIVED")
            else:
                logger.error(f"HSM Handshake FAILED: status={status}")
        
        elif packet_type == BinTypes.DATA_TYPE:
            # Data Packet: multiple ticks!
            # Structure: Type(1), PacketCount(2), Packets...
            # Note: Packets often have their own structure (Snap/Update)
            await self._handle_binary_data(body[1:])
            
    def _parse_status_packet(self, body: bytes) -> str:
        # Structure: Type(1), FieldCount(1), FieldID(1), Len(2), Value(1 char 'K')
        try:
            f_count = body[1]
            if f_count >= 1:
                # Field 1 is usually status
                pos = 2
                f_id = body[pos]
                f_len = struct.unpack(">H", body[pos+1:pos+3])[0]
                status_val = body[pos+3:pos+3+f_len].decode()
                return status_val
        except:
            pass
        return "N"

    async def _handle_binary_data(self, data: bytes):
        """
        Handle binary tick frames.
        Structure: 
        TopicID (4 bytes)
        PacketCount (2 bytes)
        For each packet:
            Length (2 bytes)
            ResponseType (1 byte: SNAP=83/UPDATE=85)
            ... fields ...
        """
        try:
            pos = 0
            if len(data) < 6: return
            topic_id = struct.unpack(">I", data[pos:pos+4])[0]
            pos += 4
            packet_count = struct.unpack(">H", data[pos:pos+2])[0]
            pos += 2
            
            for _ in range(packet_count):
                if pos + 2 > len(data): break
                pkt_len = struct.unpack(">H", data[pos:pos+2])[0]
                pkt_body = data[pos+2 : pos+2+pkt_len]
                pos += 2 + pkt_len
                
                if not pkt_body: continue
                resp_type = pkt_body[0]
                
                if resp_type == ResponseTypes.SNAP:
                    await self._parse_snapshot(pkt_body[1:])
                elif resp_type == ResponseTypes.UPDATE:
                    await self._parse_update(pkt_body[1:])
        except Exception as e:
            logger.error(f"Binary Tick Parsing Error: {e}")

    async def _parse_snapshot(self, body: bytes):
        # TopicID(4), NameLen(1), Name(N), LongFCount(1), LongFields(4ea), StringFCount(1), StringFields...
        try:
            pos = 0
            topic_id = struct.unpack(">I", body[pos:pos+4])[0]
            pos += 4
            
            name_len = body[pos]
            pos += 1
            topic_name = body[pos:pos+name_len].decode()
            pos += name_len
            
            # Initializing topic data
            topic_data = {"tk": None, "e": None, "ltp": 0.0, "c": 0.0, "v": 0, "mul": 1, "prec": 2, "name": topic_name}
            
            # Long Fields
            f_count1 = body[pos]
            pos += 1
            for i in range(f_count1):
                val = struct.unpack(">i", body[pos:pos+4])[0] # Signed int
                self._update_topic_field(topic_data, i, val)
                pos += 4
                
            # String Fields
            f_count2 = body[pos]
            pos += 1
            for _ in range(f_count2):
                f_id = body[pos]
                s_len = body[pos+1]
                s_val = body[pos+2 : pos+2+s_len].decode()
                self._update_topic_field(topic_data, f_id, s_val)
                pos += 2 + s_len
                
            self._topics[topic_id] = topic_data
            await self._emit_normalized_tick(topic_data)
            
        except Exception as e:
             logger.debug(f"Snapshot parse error topic_id={topic_id if 'topic_id' in locals() else '?'}: {e}")

    async def _parse_update(self, body: bytes):
        try:
            pos = 0
            topic_id = struct.unpack(">I", body[pos:pos+4])[0]
            pos += 4
            
            if topic_id not in self._topics: return
            
            topic_data = self._topics[topic_id]
            f_count = body[pos]
            pos += 1
            
            for i in range(f_count):
                val = struct.unpack(">i", body[pos:pos+4])[0]
                self._update_topic_field(topic_data, i, val)
                pos += 4
                
            await self._emit_normalized_tick(topic_data)
        except Exception as e:
            pass

    def _update_topic_field(self, topic_data: dict, index: int, val):
        if index in SCRIP_MAP:
            name, f_type = SCRIP_MAP[index]
            topic_data[name] = val

    async def _emit_normalized_tick(self, topic_data: dict):
        """Translate raw binary data to Phase 2 standards."""
        token = topic_data.get('tk')
        segment = topic_data.get('e')
        
        if not token or not segment: return
        
        scrip = scrip_master.get_scrip_by_token(token, str(segment).lower())
        
        # Fallback for Indices or unknown instruments
        if not scrip:
            # Use topic name (often "Nifty 50" etc.) or construct from token
            symbol = topic_data.get('name') or f"{segment}|{token}"
            display_name = symbol
            is_index = "idx" in str(segment).lower() or "if" in topic_data.get('name', '')
            multiplier = 1
            precision = 2
            company_name = symbol
            inst_type = "INDEX" if is_index else "UNKNOWN"
            exchange = "NSE" if "nse" in str(segment).lower() else "BSE"
        else:
            symbol = scrip['tradingSymbol']
            display_name = format_display_name(scrip)
            is_index = scrip.get('instrumentType') == 'INDEX'
            multiplier = scrip.get('multiplier', 1)
            precision = scrip.get('precision', 2)
            company_name = scrip.get('companyName')
            inst_type = scrip.get('instrumentType')
            exchange = "NSE" if "NSE" in str(segment).upper() else "BSE"

        # Scaling
        mul = float(topic_data.get('mul', multiplier))
        prec = float(topic_data.get('prec', precision))
        scale = mul * (10 ** prec)
        
        def normalize(v):
            return float(v) / scale if v else 0.0

        normalized = {
            "symbol": symbol,  # This might be 'nse_cm|26000' or 'Nifty 50' if scrip missing
            "displayName": display_name,
            "companyName": company_name,
            "ltp": normalize(topic_data.get('ltp')),
            "open": normalize(topic_data.get('op')),
            "high": normalize(topic_data.get('h')),
            "low": normalize(topic_data.get('lo')),
            "close": normalize(topic_data.get('c')),
            "volume": int(topic_data.get('v', 0)),
            "timestamp": int(time.time()),
            "instrumentType": inst_type,
            "exchange": exchange,
            "session": "OPEN", # Simplified
            "isAmo": False
        }

        # LOG FOR VERIFICATION
        logger.info(f"💎 [HSM] TICK: {normalized['symbol']} | LTP: {normalized['ltp']} | VOL: {normalized['volume']}")
        
        for cb in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(cb): await cb(normalized)
                else: cb(normalized)
            except: pass

    async def subscribe(self, scrips_str: str):
        """Subscribe to scrips using the binary protocol."""
        if not self.connected or not self.ws: return
        
        # Structure: Type(1), FieldCount(1), Field1: Scrips, Field2: Channel
        # Scrips field: Count(2), [len(1)+str]
        
        scrips = scrips_str.strip('&').split('&')
        
        # Intelligent Prefixing: Use if| for indices (identified by 'idx')
        scrip_list = []
        for s in scrips:
             if "idx" in s.lower():
                 scrip_list.append(f"if|{s}")
             else:
                 scrip_list.append(f"sf|{s}")
        
        scrip_bytes = struct.pack(">H", len(scrip_list))
        for s in scrip_list:
            scrip_bytes += struct.pack("B", len(s)) + s.encode()
            
        f1 = b"\x01" + struct.pack(">H", len(scrip_bytes)) + scrip_bytes
        f2 = b"\x02" + struct.pack(">H", 1) + b"\x01" # Channel 1
        
        packet = struct.pack("BB", BinTypes.SUBSCRIBE_TYPE, 2) + f1 + f2
        msg = struct.pack(">H", len(packet)) + packet
        
        await self.ws.send(msg)
        logger.info(f"HSM Binary Subscribed: {scrips_str}")

    def add_callback(self, cb: Callable):
        self._callbacks.append(cb)

    async def disconnect(self):
        self.connected = False
        if self.ws: await self.ws.close()
        if self._heartbeat_task: self._heartbeat_task.cancel()
        if self._listen_task: self._listen_task.cancel()

# Singleton for the app lifetime
kotak_hsm = KotakHSMClient()
