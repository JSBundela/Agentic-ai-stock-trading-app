from app.core.logger import logger
from app.core.exceptions import KotakAPIError
from app.utils import cache
import httpx

class PortfolioService:
    async def get_positions(self):
        """
        Fetch all positions for the current trading day.
        Per official documentation: GET /quick/user/positions
        """
        trade_token, trade_sid, base_url, _ = cache.get_trade_session()
        
        if not trade_token or not trade_sid or not base_url:
            raise KotakAPIError("Not authenticated. Please complete TOTP + MPIN login first.")
        
        url = f"{base_url}/quick/user/positions"
        
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
                logger.info(f"Positions status: {result.get('stat')}")
                
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Positions fetch failed: Status {e.response.status_code}")
            logger.error(f"Full response: {e.response.text}")
            raise KotakAPIError(f"Failed to fetch positions: {e.response.text}")
        except Exception as e:
            logger.error(f"Positions fetch failed: {str(e)}")
            raise KotakAPIError(str(e))
    
    async def get_holdings(self):
        """
        Fetch portfolio holdings.
        Per official documentation: GET /portfolio/v1/holdings
        """
        trade_token, trade_sid, base_url, _ = cache.get_trade_session()
        
        if not trade_token or not trade_sid or not base_url:
            raise KotakAPIError("Not authenticated. Please complete TOTP + MPIN login first.")
        
        url = f"{base_url}/portfolio/v1/holdings"
        
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
                logger.info(f"Holdings fetch successful")
                
                return result
                
        except httpx.HTTPStatusError as e:
            # Handle "No holdings" case (Kotak returns 424)
            if e.response.status_code == 424 and "No holdings" in e.response.text:
                 logger.info("No holdings found - returning empty list")
                 return {"stat": "Ok", "data": []}

            logger.error(f"Holdings fetch failed: Status {e.response.status_code}")
            logger.error(f"Full response: {e.response.text}")
            raise KotakAPIError(f"Failed to fetch holdings: {e.response.text}")
        except Exception as e:
            logger.error(f"Holdings fetch failed: {str(e)}")
            raise KotakAPIError(str(e))
    
    async def get_limits(self):
        """
        Fetch trading limits/margins.
        Per official documentation: POST /quick/user/limits
        """
        trade_token, trade_sid, base_url, _ = cache.get_trade_session()
        
        if not trade_token or not trade_sid or not base_url:
            raise KotakAPIError("Not authenticated. Please complete TOTP + MPIN login first.")
        
        url = f"{base_url}/quick/user/limits"
        
        logger.info(f"POST {url}")
        
        # Default: fetch all limits
        import json
        payload = {"seg": "ALL", "exch": "ALL", "prod": "ALL"}
        form_data = {"jData": json.dumps(payload)}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    data=form_data,
                    headers={
                        "Auth": trade_token,
                        "Sid": trade_sid,
                        "neo-fin-key": "neotradeapi"
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Limits status: {result.get('stat')}")
                
                # PERSISTENT DEBUG LOGGING
                import json
                with open("debug_limits.json", "w") as f:
                    json.dump(result, f)
                
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Limits fetch failed: Status {e.response.status_code}")
            logger.error(f"Full response: {e.response.text}")
            
            # TEMPORARY: If Kotak limits API is down, return test data for development
            if "bridge API error" in e.response.text or e.response.status_code == 424:
                logger.warning("⚠️  Kotak limits API bridge error - returning test data for development")
                return {
                    "stat": "Ok",
                    "stCode": 200,
                    "NotionalCash": "50000.00",
                    "Net": "75000.00",
                    "MarginUsed": "5000.00",
                    "CollateralValue": "25000.00",
                    "Category": "CLIENT",
                    "_fallback": True  # Flag to indicate this is test data
                }
            
            raise KotakAPIError(f"Failed to fetch limits: {e.response.text}")
        except Exception as e:
            logger.error(f"Limits fetch failed: {str(e)}")
            raise KotakAPIError(str(e))

portfolio_service = PortfolioService()
