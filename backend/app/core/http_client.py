import httpx
from app.config import get_settings
from app.core.logger import logger

settings = get_settings()

class HTTPClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HTTPClient, cls).__new__(cls)
            
            # Validate KOTAK_ACCESS_TOKEN exists
            if not settings.KOTAK_ACCESS_TOKEN:
                raise RuntimeError("KOTAK_ACCESS_TOKEN not configured")
            
            cls._instance.client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": settings.KOTAK_ACCESS_TOKEN,  # Plain, no Bearer
                    "neo-fin-key": "neotradeapi"  # Exact casing
                }
            )
        return cls._instance

    async def get_client(self) -> httpx.AsyncClient:
        return self.client
    
    async def close(self):
        await self.client.aclose()
        
http_client = HTTPClient()
