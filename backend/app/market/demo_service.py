"""
Demo Mode Service - Simulates live market data for recording/testing.

Provides realistic price movements when markets are closed.
"""
import random
import time
from datetime import datetime
from typing import Dict

class DemoDataService:
    """Generates realistic demo market data."""
    
    # Base prices (realistic Indian market levels)
    BASE_PRICES = {
        "NIFTY 50": 25048.65,
        "SENSEX": 81537.70,
        "RELIANCE": 1285.50,
        "TCS": 3950.20,
        "INFY": 1825.75,
        "HDFCBANK": 1750.30,
        "ICICIBANK": 1285.60
    }
    
    def __init__(self):
        self.start_time = time.time()
        self.tick_count = 0
    
    def get_realistic_price(self, symbol: str) -> Dict:
        """
        Generate realistic price with small fluctuations.
        Simulates intraday volatility.
        """
        base_price = self.BASE_PRICES.get(symbol, 100.0)
        
        # Time-based volatility (increases over time for realism)
        elapsed = time.time() - self.start_time
        volatility = 0.001 + (elapsed / 3600) * 0.0005  # Max 0.15% per hour
        
        # Random walk with mean reversion
        change_pct = random.gauss(0, volatility)
        change_pct = max(min(change_pct, 0.02), -0.02)  # Cap at ±2%
        
        ltp = base_price * (1 + change_pct)
        change = ltp - base_price
        pct_change = (change / base_price) * 100
        
        self.tick_count += 1
        
        return {
            "ltp": round(ltp, 2),
            "change": round(change, 2),
            "percent_change": round(pct_change, 2),
            "volume": random.randint(100000, 5000000),
            "timestamp": int(time.time()),
            "is_demo": True  # Flag for UI
        }
    
    def get_index_quote(self, index_name: str) -> Dict:
        """Get demo index quote."""
        return {
            "index_name": index_name,
            **self.get_realistic_price(index_name)
        }

# Global instance
demo_service = DemoDataService()
