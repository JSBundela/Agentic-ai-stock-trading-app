
import asyncio
from app.scripmaster.service import scrip_master

async def main():
    await scrip_master.load_scrip_master()
    # Try common MCX symbols
    for sym in ["CRUDEOIL", "GOLD", "SILVER"]:
        res = scrip_master.get_scrip(sym)
        print(f"{sym}: {res}")

if __name__ == "__main__":
    asyncio.run(main())
