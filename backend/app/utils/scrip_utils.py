"""
Scrip Master Utilities - Symbol to Token Conversion
"""
import sqlite3
from typing import Optional
from app.core.logger import logger

DB_PATH = "scrip_master.db"

def get_instrument_token(symbol: str, prefer_exchange: str = "nse_cm") -> Optional[str]:
    """
    Convert a trading symbol to instrument token from scrip master.
    Tries NSE first, falls back to BSE if NSE not available.
    
    Args:
        symbol: Trading symbol (e.g., "HDFCBANK", "RELIANCE")
        prefer_exchange: Preferred exchange segment (default: "nse_cm")
    
    Returns:
        Instrument token (e.g., "11536") - NO exchange prefix, just the token number
    """
    try:
        # Normalize symbol to uppercase for DB lookup
        symbol = symbol.upper()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Try NSE first (preferred for liquidity)
        # We select instrumentToken AND exchangeSegment to construct the result
        cursor.execute(
            "SELECT instrumentToken FROM scrips WHERE tradingSymbol = ? AND exchangeSegment = 'nse_cm' AND instrumentType = 'EQ' LIMIT 1",
            (symbol,)
        )
        result = cursor.fetchone()
        exchange = 'nse_cm'
        
        # If NSE not found, try BSE as fallback
        if not result:
            logger.info(f"Symbol {symbol} not found in NSE, trying BSE as fallback")
            cursor.execute(
                "SELECT instrumentToken FROM scrips WHERE tradingSymbol = ? AND exchangeSegment = 'bse_cm' AND instrumentType = 'EQ' LIMIT 1",
                (symbol,)
            )
            result = cursor.fetchone()
            exchange = 'bse_cm'
        
        # Last resort: try any exchange (excluding derivatives if possible, or just take whatever)
        if not result:
            logger.warning(f"Symbol {symbol} not found in NSE/BSE, trying other exchanges")
            cursor.execute(
                "SELECT instrumentToken, exchangeSegment FROM scrips WHERE tradingSymbol = ? AND instrumentType = 'EQ' LIMIT 1",
                (symbol,)
            )
            result = cursor.fetchone()
            if result and len(result) > 1:
               exchange = result[1]
               result = (result[0],)
        
        conn.close()
        
        if result:
            # result[0] is the token (e.g. "11536"). We need "exchange|token"
            token = result[0]
            full_token = f"{exchange}|{token}"
            logger.info(f"✅ Resolved {symbol} → {full_token}")
            return full_token
        else:
            logger.error(f"❌ Symbol {symbol} not found in scrip master")
            return None
            
    except Exception as e:
        logger.error(f"Scrip lookup failed for {symbol}: {e}")
        return None
