"""
Instrument Symbol Decoder (Python Backend)

Pure parsing layer for Kotak Neo trading symbols.
Decodes equity, futures, and options symbols into structured metadata.
"""

import re
from typing import Optional, Dict, List, TypedDict
from datetime import datetime, timedelta
from calendar import monthrange


class ParsedInstrumentDict(TypedDict, total=False):
    """Type definition for parsed instrument dictionary"""
    symbol: str
    base_symbol: str
    instrument_type: str  # EQUITY, FUTURES, OPTIONS
    segment: str  # EQUITY, FUTURES, OPTIONS_CE, OPTIONS_PE
    option_type: Optional[str]  # CE, PE, CALL, PUT
    strike_price: Optional[float]
    expiry_raw: Optional[str]
    expiry_date: Optional[str]  # YYYY-MM-DD
    expiry_year: Optional[int]
    expiry_month: Optional[int]
    expiry_day: Optional[int]
    is_derivative: bool
    display_name: str


# Month name to number mapping
MONTHS = {
    'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4,
    'MAY': 5, 'JUN': 6, 'JUL': 7, 'AUG': 8,
    'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
}

MONTH_NAMES = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def get_last_thursday(year: int, month: int) -> int:
    """Get last Thursday of a month (NSE standard expiry)"""
    # Get last day of month
    last_day = monthrange(year, month)[1]
    
    # Count backwards to find last Thursday
    for day in range(last_day, 0, -1):
        date = datetime(year, month, day)
        if date.weekday() == 3:  # Thursday is 3
            return day
    
    return last_day  # Fallback


def parse_symbol(symbol: str) -> ParsedInstrumentDict:
    """
    Parse trading symbol and return structured instrument data
    
    Args:
        symbol: Trading symbol (e.g., "NIFTY26JANFUT", "YESBANK-EQ")
    
    Returns:
        Dictionary with parsed instrument data
    """
    trimmed = symbol.strip()
    
    # Default fallback (EQUITY)
    fallback: ParsedInstrumentDict = {
        'symbol': trimmed,
        'base_symbol': re.sub(r'-EQ$', '', trimmed, flags=re.IGNORECASE),
        'instrument_type': 'EQUITY',
        'segment': 'EQUITY',
        'is_derivative': False,
        'display_name': trimmed
    }
    
    # EQUITY: Check for -EQ suffix
    if re.search(r'-EQ$', trimmed, re.IGNORECASE):
        base = re.sub(r'-EQ$', '', trimmed, flags=re.IGNORECASE)
        return {
            **fallback,
            'base_symbol': base,
            'display_name': base
        }
    
    # OPTIONS: Compact format (NIFTY2611326900CE or NIFTY26FEB26000PE)
    options_compact = re.match(r'^([A-Z]+)(\d{2})([A-Z]{3}|\d{2})(\d+)(CE|PE)$', trimmed, re.IGNORECASE)
    if options_compact:
        base, year, month_or_day, strike, opt_type = options_compact.groups()
        opt_type = opt_type.upper()
        strike_num = int(strike)
        year_num = 2000 + int(year)
        
        # Check if third group is month name (FEB) or numeric (11)
        if re.match(r'^[A-Z]{3}$', month_or_day, re.IGNORECASE):
            month_num = MONTHS.get(month_or_day.upper(), 1)
            day_num = get_last_thursday(year_num, month_num)
        else:
            # Numeric format: NIFTY2611326900CE → year=26, month=11, day+strike=326900
            month_num = int(month_or_day)
            # Extract day from strike (first 2 digits)
            if len(strike) >= 2:
                day_num = int(strike[:2])
                strike_num = int(strike[2:])
            else:
                day_num = get_last_thursday(year_num, month_num)
        
        expiry_date = f"{year_num}-{str(month_num).zfill(2)}-{str(day_num).zfill(2)}"
        
        return {
            'symbol': trimmed,
            'base_symbol': base,
            'instrument_type': 'OPTIONS',
            'segment': f'OPTIONS_{opt_type}',
            'option_type': opt_type,
            'strike_price': float(strike_num),
            'expiry_year': year_num,
            'expiry_month': month_num,
            'expiry_day': day_num,
            'expiry_date': expiry_date,
            'expiry_raw': f"{day_num}-{MONTH_NAMES[month_num]}-{year_num}",
            'is_derivative': True,
            'display_name': f"{base} {strike_num} {opt_type} ({day_num}-{MONTH_NAMES[month_num]}-{year_num})"
        }
    
    # OPTIONS: Web format (NIFTY 25965 CALL 13-JAN)
    options_web = re.match(r'^([A-Z]+)\s+(\d+)\s+(CALL|PUT)\s+(\d{1,2})-([A-Z]{3})$', trimmed, re.IGNORECASE)
    if options_web:
        base, strike, opt_type, day, month = options_web.groups()
        opt_type_short = 'CE' if opt_type.upper() == 'CALL' else 'PE'
        strike_num = int(strike)
        day_num = int(day)
        month_num = MONTHS.get(month.upper(), 1)
        year_num = datetime.now().year
        
        expiry_date = f"{year_num}-{str(month_num).zfill(2)}-{str(day_num).zfill(2)}"
        
        return {
            'symbol': trimmed,
            'base_symbol': base,
            'instrument_type': 'OPTIONS',
            'segment': f'OPTIONS_{opt_type_short}',
            'option_type': opt_type_short,
            'strike_price': float(strike_num),
            'expiry_year': year_num,
            'expiry_month': month_num,
            'expiry_day': day_num,
            'expiry_date': expiry_date,
            'expiry_raw': f"{day_num}-{month}",
            'is_derivative': True,
            'display_name': f"{base} {strike_num} {opt_type.upper()} ({day_num}-{MONTH_NAMES[month_num]}-{year_num})"
        }
    
    # FUTURES: FUT suffix (NIFTY26JANFUT)
    futures_match = re.match(r'^([A-Z]+)(\d{2})([A-Z]{3})FUT$', trimmed, re.IGNORECASE)
    if futures_match:
        base, year, month = futures_match.groups()
        year_num = 2000 + int(year)
        month_num = MONTHS.get(month.upper(), 1)
        day_num = get_last_thursday(year_num, month_num)
        expiry_date = f"{year_num}-{str(month_num).zfill(2)}-{str(day_num).zfill(2)}"
        
        return {
            'symbol': trimmed,
            'base_symbol': base,
            'instrument_type': 'FUTURES',
            'segment': 'FUTURES',
            'expiry_year': year_num,
            'expiry_month': month_num,
            'expiry_day': day_num,
            'expiry_date': expiry_date,
            'expiry_raw': f"{month}-{year}",
            'is_derivative': True,
            'display_name': f"{base} {month.upper()}{year_num} FUT"
        }
    
    # FUTURES: Space format (NIFTY 26-JAN)
    futures_space = re.match(r'^([A-Z]+)\s+(\d{2})-([A-Z]{3})$', trimmed, re.IGNORECASE)
    if futures_space:
        base, year, month = futures_space.groups()
        year_num = 2000 + int(year)
        month_num = MONTHS.get(month.upper(), 1)
        day_num = get_last_thursday(year_num, month_num)
        expiry_date = f"{year_num}-{str(month_num).zfill(2)}-{str(day_num).zfill(2)}"
        
        return {
            'symbol': trimmed,
            'base_symbol': base,
            'instrument_type': 'FUTURES',
            'segment': 'FUTURES',
            'expiry_year': year_num,
            'expiry_month': month_num,
            'expiry_day': day_num,
            'expiry_date': expiry_date,
            'expiry_raw': f"{month}-{year}",
            'is_derivative': True,
            'display_name': f"{base} {month.upper()}{year_num} FUT"
        }
    
    # Fallback: Plain equity
    return fallback


def parse_symbols(symbols: List[str]) -> List[ParsedInstrumentDict]:
    """Batch parse multiple symbols"""
    return [parse_symbol(s) for s in symbols]


def get_display_name(symbol: str) -> str:
    """Get display name for a symbol"""
    return parse_symbol(symbol)['display_name']


def is_derivative(symbol: str) -> bool:
    """Check if symbol is a derivative"""
    return parse_symbol(symbol)['is_derivative']


def get_base_symbol(symbol: str) -> str:
    """Get base symbol (underlying)"""
    return parse_symbol(symbol)['base_symbol']
