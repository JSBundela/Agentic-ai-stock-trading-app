from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.core.logger import logger
from app.auth.router import router as auth_router
from app.market.router import router as market_router
from app.orders.router import router as orders_router
from app.portfolio.router import router as portfolio_router
from app.scripmaster.router import router as scripmaster_router
from app.websocket.router import router as websocket_router
from app.websocket.kotak_ws_hsm import kotak_hsm
from app.utils.cache import get_trade_session, get_view_session
from app.historical.routes import router as historical_router
from app.scripmaster.service import scrip_master
from app.strategy.engine import strategy_engine
import asyncio

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(market_router)
app.include_router(orders_router)
app.include_router(portfolio_router)
app.include_router(scripmaster_router)
app.include_router(websocket_router)
app.include_router(historical_router)

async def _ensure_hsm_connected():
    """Connect to Kotak HSM using cached session (Trade preferred)."""
    token, sid, _, _ = get_trade_session()
    session_type = "TRADE"
    
    if not token:
        token, sid = get_view_session()
        session_type = "VIEW"

    logger.warning(f"🏁🏁🏁 [MAIN] ensure_hsm_connected ({session_type}): exists={token is not None}")
    
    if token and sid:
        try:
            await kotak_hsm.connect(token, sid)
            logger.warning(f"🏁🏁🏁 [MAIN] Broker connected to Kotak HSM ({session_type})")
        except Exception as e:
            logger.error(f"❌ [MAIN] Broker failed to connect to HSM: {e}")
    else:
        logger.warning("⚠️ [MAIN] No active session found in cache.")

@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    msg = "\n" + "="*80 + "\n" + "🏁🏁🏁 [MAIN] APPLICATION STARTUP EVENT - CRITICAL TRACE" + "\n" + "="*80 + "\n"
    logger.warning(msg)
    print(msg)
    
    # Initialize order history database
    from app.database import init_database
    await init_database()
    
    # Connect HSM and Load Scrip Master
    # This logic is now encapsulated in _ensure_hsm_connected and called directly.
    # The original logic for session retrieval and HSM connection is replaced by the call to _ensure_hsm_connected.
    # The scrip master loading is still separate as it's not part of the HSM connection itself.
    
    await _ensure_hsm_connected()
    
    # Load Scrip Master (this part remains as it was, but now after HSM connection attempt)
    # We assume _ensure_hsm_connected will log if no session is found, so we don't need a redundant check here.
    # However, scrip_master.load_scrip_master() might depend on a successful HSM connection or at least a session.
    # For now, we'll keep it as a separate task.
    asyncio.create_task(scrip_master.load_scrip_master())

    # Start Strategy Engine
    await strategy_engine.start()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down...")
    await strategy_engine.stop()

@app.get("/")
async def root():
    return {"message": "Kotak Neo Trading API is running"}
