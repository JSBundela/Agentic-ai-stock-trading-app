from datetime import datetime

def format_display_name(scrip: dict) -> str:
    """
    Generates human-readable name strictly following Phase 2 rules.
    - Equity: YESBANK NSE
    - Futures: NIFTY FUT (27 JAN NSE)
    - Options: NIFTY 26000 CALL (24 FEB NSE)
    """
    symbol = scrip.get('tradingSymbol', '')
    inst_type = scrip.get('instrumentType', '')
    exchange = "NSE" if "NSE" in scrip.get('exchangeSegment', '').upper() else "BSE"
    
    # Extract base symbol (e.g., RELIANCE from RELIANCE-EQ or RELIANCE24JANFUT)
    # Since we have the scrip master, we don't need regex, but we need the base component.
    # Usually tradingSymbol for EQ is SYMBOL-EQ. For F&O it's SYMBOLYYMMMFUT.
    # However, the user says "YESBANK NSE". YESBANK is the base.
    
    # For Equity
    if inst_type == 'EQ':
        base = symbol.split('-')[0] if '-' in symbol else symbol
        return f"{base} {exchange}"
    
    # For F&O, we use metadata
    expiry_iso = scrip.get('expiryDateISO')
    expiry_str = ""
    if expiry_iso:
        try:
            dt = datetime.strptime(expiry_iso, '%Y-%m-%d')
            expiry_str = dt.strftime('%d %b').upper() # 27 JAN
        except:
            expiry_str = expiry_iso
            
    # Derive base from tradingSymbol (e.g. NIFTY25JANFUT -> NIFTY)
    # We don't want regex, but we need the ROOT. 
    # Let's use the scrip master's 'tradingSymbol' and strip the suffix if possible, 
    # or just use the prefix before digits.
    import re
    base = re.split(r'\d', symbol)[0] # This is safe as it's just for display name prefix
    
    if 'FUT' in str(inst_type):
        return f"{base} FUT ({expiry_str} {exchange})"
    
    if 'OPT' in str(inst_type):
        opt_type = "CALL" if scrip.get('optionType') == 'CE' else "PUT"
        strike = scrip.get('strikePrice', '')
        # Remove .0 if it's an integer strike
        if isinstance(strike, float) and strike.is_integer():
            strike = int(strike)
        return f"{base} {strike} {opt_type} ({expiry_str} {exchange})"
    
    return symbol
