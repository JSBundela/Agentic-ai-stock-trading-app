from app.core.http_client import http_client
from app.config import get_settings
from app.core.logger import logger
from app.core.exceptions import KotakAPIError
from app.utils import cache
import httpx

settings = get_settings()

class AuthService:
    def __init__(self):
        self.trade_url = settings.KOTAK_TRADE_API_URL
        
    async def login_step_1(self, totp: str):
        """
        Step 1: TOTP Login
        URL: https://mis.kotaksecurities.com/login/1.0/tradeApiLogin
        """
        client = await http_client.get_client()
        url = f"{self.trade_url}/login/1.0/tradeApiLogin"
        
        # Ensure mobile number has +91 prefix
        mobile = settings.MOBILE_NUMBER
        if not mobile.startswith("+91"):
            mobile = f"+91{mobile}"
        
        payload = {
            "mobileNumber": mobile,
            "ucc": settings.UCC,
            "totp": totp # Reverting to lowercase
        }
        
        logger.info(f"POST {url} | Payload keys: {list(payload.keys())}")
        logger.debug(f"Payload: {payload}")
        
        try:
            response = await client.post(url, json=payload)
            logger.info(f"Response Status: {response.status_code}")
            logger.debug(f"Response Body: {response.text}")
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Response keys: {list(data.keys())}")
            
            # Kotak API returns tokens inside a 'data' object
            token_data = data.get("data", data)  # Use nested data if exists, otherwise top level
            
            # Store view session - try multiple possible field names
            view_token = None
            view_sid = None
            
            # Check for view_token variations
            for token_key in ["view_token", "viewToken", "token", "access_token"]:
                if token_key in token_data:
                    view_token = token_data[token_key]
                    break
            
            # Check for sid variations
            for sid_key in ["view_sid", "viewSid", "sid"]:
                if sid_key in token_data:
                    view_sid = token_data[sid_key]
                    break
            
            if view_token and view_sid:
                cache.set_view_session(view_token, view_sid)
                logger.info(f"✓ Session stored in cache (token exists: True)")
            else:
                logger.warning(f"Could not extract session from response. Data keys: {list(token_data.keys())}")
            
            # Standardize for frontend
            return {
                "access_token": view_token or "",
                "sid": view_sid or "",
                "token_type": "bearer",
                "message": "TOTP verified"
            }
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Status: {e.response.status_code}")
            raise KotakAPIError(f"Login failed: {e.response.text}")
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise KotakAPIError(str(e))
            
    async def validate_mpin(self, mpin: str):
        """
        Step 2: MPIN Validation
        URL: https://mis.kotaksecurities.com/login/1.0/tradeApiValidate
        """
        # Check cache state
        has_session = cache.has_view_session()
        logger.info(f"Cache check: view_session_exists={has_session}")
        
        view_token, view_sid = cache.get_view_session()
        
        if not view_token or not view_sid:
            raise KotakAPIError("No active session. Please login with TOTP first.")
        
        client = await http_client.get_client()
        url = f"{self.trade_url}/login/1.0/tradeApiValidate"
        
        # Add session headers
        headers = {
            "Auth": view_token,
            "sid": view_sid
        }
        
        payload = {
            "Mpin": mpin
        }
        
        logger.info(f"POST {url}")
        
        try:
            # Log headers (excluding sensitive values)
            logger.info(f"Using Cached View Token: {view_token[:5]}... | SID: {view_sid[:5]}...")
            logger.info(f"Client Default Headers: {dict(client.headers).keys()}")
            
            # NOTE: http_client injects 'Authorization' and 'neo-fin-key' automatically.
            # We must ensure they are not overwritten or missing.
            
            response = await client.post(url, json=payload, headers=headers)
            
            # Log response status and body ON ERROR for debugging
            if response.status_code != 200:
                logger.error(f"❌ MPIN Validation Failed with Status: {response.status_code}")
                logger.error(f"❌ Response Body: {response.text}")
                logger.error(f"❌ Request Headers (masked): Auth={'*' * 5}, sid={'*' * 5}")
            
            response.raise_for_status()
            
            data = response.json()
            
            # Kotak API returns tokens inside a 'data' object
            token_data = data.get("data", data)
            
            # Store trade session
            trade_token = None
            trade_sid = None
            base_url = None
            data_center = None
            
            # Extract trade token
            for token_key in ["token", "access_token", "trade_token"]:
                if token_key in token_data:
                    trade_token = token_data[token_key]
                    break
            
            # Extract sid
            for sid_key in ["sid", "trade_sid"]:
                if sid_key in token_data:
                    trade_sid = token_data[sid_key]
                    break
            
            # Extract baseUrl and dataCenter
            base_url = token_data.get("baseUrl") or token_data.get("base_url")
            data_center = token_data.get("dataCenter") or token_data.get("data_center")
            
            if not trade_token or not trade_sid:
                logger.error(f"❌ Failed to extract Trade Token/SID. Available keys: {list(token_data.keys())}")
                logger.error(f"Response: {data}")
                raise KotakAPIError("Invalid response from Kotak: Missing trade token/sid")

            # Cache the full trade session
            cache.set_trade_session(trade_token, trade_sid, base_url, data_center)
            
            logger.info(f"✅ MPIN validation successful for user: {settings.UCC}")
            logger.info(f"🔗 Authenticated Base URL: {base_url}")
            logger.info(f"📡 Data Center: {data_center}")
            
            # CRITICAL: Connect HSM and Load scrip master AFTER authentication with valid baseUrl
            logger.info("📥 Connecting to HSM and scheduling scrip master load...")
            from app.websocket.kotak_ws_hsm import kotak_hsm
            from app.scripmaster.service import scrip_master
            import asyncio
            
            # 1. Immediate HSM Reconnection (async task)
            asyncio.create_task(kotak_hsm.connect(trade_token, trade_sid))
            
            # 2. Background Scrip Master Load
            asyncio.create_task(scrip_master.load_scrip_master())
            
            logger.info("🚀 HSM Reconnection and Scrip Master load started in background")
            
            # Standardize for frontend
            return {
                "access_token": trade_token,
                "sid": trade_sid,
                "token_type": "bearer",
                "baseUrl": base_url,
                "dataCenter": data_center
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"Status: {e.response.status_code}")
            # Raise the raw text so frontend can see "Invalid MPIN" etc.
            raise KotakAPIError(f"MPIN validation failed: {e.response.text}")
        except Exception as e:
            logger.error(f"MPIN validation failed: {str(e)}")
            raise KotakAPIError(str(e))

auth_service = AuthService()
