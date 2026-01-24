import asyncio
from app.market.service import market_service
from app.config import get_settings

async def main():
    settings = get_settings()
    
    # Only test the one we use in Header.tsx
    variations = ["nse_cm|Nifty 50"]
    
    try:
         quotes = await market_service.get_quotes(variations)
         print(f"Response ({len(quotes)} items):")
         for q in quotes:
             print(f"NIFTY OBJ: {q}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
