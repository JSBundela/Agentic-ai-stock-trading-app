from datetime import datetime, time
import pytz

# IST Timezone
IST = pytz.timezone('Asia/Kolkata')

def get_market_session_info(segment: str):
    """
    Returns market session status strictly based on exchange rules.
    - Equity (NSE_CM, BSE_CM): 9:15 AM - 3:30 PM
    - F&O (NSE_FO, BSE_FO): 9:15 AM - 3:30 PM
    - Currency (CDE_FO): 9:00 AM - 5:00 PM
    - MCX: 9:00 AM - 11:30 PM
    
    Returns:
    {
        "status": "OPEN" | "CLOSED",
        "is_amo": bool,
        "segment": str
    }
    """
    now = datetime.now(IST)
    current_time = now.time()
    weekday = now.weekday() # 0 = Monday, 6 = Sunday
    
    # Weekends - All markets CLOSED
    if weekday >= 5:
        return {"status": "CLOSED", "is_amo": True, "segment": segment}
    
    seg = segment.upper()
    
    # Market timings
    timings = {
        "CM": (time(9, 15), time(15, 30)),
        "FO": (time(9, 15), time(15, 30)),
        "CD": (time(9, 0), time(17, 0)),
        "MCX": (time(9, 0), time(23, 30))
    }
    
    # Default to CM/FO timing if segment not found
    seg_type = "CM" if "CM" in seg else "FO" if "FO" in seg else "CD" if "CD" in seg else "MCX" if "MCX" in seg else "CM"
    start, end = timings.get(seg_type)
    
    is_open = start <= current_time <= end
    
    return {
        "status": "OPEN" if is_open else "CLOSED",
        "is_amo": not is_open,
        "segment": segment
    }
