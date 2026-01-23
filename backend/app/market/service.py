from app.core.logger import logger
from app.core.exceptions import KotakAPIError
from app.utils import cache
import httpx
from typing import List

class MarketService:
    async def get_quotes(self, instrument_tokens: List[str]):
        """
        Fetch market quotes for instruments.
        Per official documentation: GET /script-details/1.0/quotes/neosymbol/{query}[/{filter}]
        
        Format: exchange_segment|instrument
        - Stocks: nse_cm|11536 (token from scrip master)
        - Indices: nse_cm|Nifty 50 (exact case-sensitive name)
        """
        # Get access token (not session token - quotes uses accesstoken only)
        from app.config import get_settings
        settings = get_settings()
        
        if not settings.KOTAK_ACCESS_TOKEN:
            raise KotakAPIError("Access token not configured")
        
        # Get base URL from trade session (if available)
        try:
            _, _, base_url, _ = cache.get_trade_session()
        except:
            # Fallback to default if not authenticated yet
            base_url = "https://gw-napi.kotaksecurities.com"
        
        # Build query string: nse_cm|11536,nse_cm|Nifty 50
        query = ",".join(instrument_tokens)
        
        # Default filter: "all" returns all fields
        url = f"{base_url}/script-details/1.0/quotes/neosymbol/{query}/all"
        
        logger.info(f"GET {url}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    headers={
                        "Authorization": settings.KOTAK_ACCESS_TOKEN,
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Quotes fetch successful: {len(result) if isinstance(result, list) else 1} instruments")
                
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Quotes fetch failed: Status {e.response.status_code}")
            logger.error(f"Full response: {e.response.text}")
            raise KotakAPIError(f"Failed to fetch quotes: {e.response.text}")
        except Exception as e:
            logger.error(f"Quotes fetch failed: {str(e)}")
            raise KotakAPIError(str(e))

market_service = MarketService()
