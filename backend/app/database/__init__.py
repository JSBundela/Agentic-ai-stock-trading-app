"""
Database initialization and connection management for order history.
Uses SQLite for local order storage.
"""

import sqlite3
import aiosqlite
import asyncio
from pathlib import Path
from app.core.logger import logger

# Database file path
DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "orders.db"

# SQL schema for order history
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS order_history (
    order_id TEXT PRIMARY KEY,
    trading_symbol TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price REAL,
    order_type TEXT,
    transaction_type TEXT,
    product TEXT,
    status TEXT,
    exchange TEXT,
    order_datetime TEXT NOT NULL,
    kotak_response TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_order_datetime ON order_history(order_datetime);
CREATE INDEX IF NOT EXISTS idx_trading_symbol ON order_history(trading_symbol);
CREATE INDEX IF NOT EXISTS idx_status ON order_history(status);
"""


# Persistent connection singleton
_db_connection = None
_db_lock = asyncio.Lock()

async def init_database():
    """Initialize the database and create schema if needed."""
    global _db_connection
    async with _db_lock:
        try:
            DB_DIR.mkdir(exist_ok=True)
            # Create connection if not exists
            if _db_connection is None:
                _db_connection = await aiosqlite.connect(DB_PATH)
                
            await _db_connection.executescript(SCHEMA_SQL)
            await _db_connection.commit()
            logger.info(f"Order history database initialized at {DB_PATH}")
        except Exception as e:
            logger.error(f"Failed to initialize order history database: {e}")
            raise

async def get_db():
    """Get persistent database connection."""
    global _db_connection
    async with _db_lock:
        if _db_connection is None:
            _db_connection = await aiosqlite.connect(DB_PATH)
        return _db_connection
