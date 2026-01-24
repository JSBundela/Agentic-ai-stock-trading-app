from app.scripmaster.service import ScripMasterService
import asyncio

async def main():
    service = ScripMasterService()
    await service.load_scrip_master()
    
    print("\n--- SEARCHING FOR INDICES ---")
    indices = ["Nifty 50", "NIFTY 50", "NIFTY", "SENSEX", "BSE SENSEX", "Nifty Bank"]
    
    for name in indices:
        # Try finding by name
        results = await service.search_scrip(name)
        for r in results:
             # Check if it looks like an index (segment might be 'nse_idx' or similar)
             if 'idx' in r.get('exchangeSegment', '').lower() or r.get('instrumentType') == 'INDEX':
                 print(f"FOUND: {r['tradingSymbol']} | Token: {r['instrumentToken']} | Segment: {r['exchangeSegment']}")
                 
if __name__ == "__main__":
    asyncio.run(main())
