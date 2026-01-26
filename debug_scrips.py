
import sqlite3


def check_script(symbol_query):
    conn = sqlite3.connect('backend/scrip_master.db')
    cursor = conn.cursor()
    
    print(f"Searching for '%{symbol_query}%'...")
    cursor.execute("SELECT tradingSymbol, exchangeSegment, instrumentToken, companyName FROM scrips WHERE tradingSymbol LIKE ? OR companyName LIKE ?", (f'%{symbol_query}%', f'%{symbol_query}%'))
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} results:")
    for row in rows:
        print(row)
        
    conn.close()

if __name__ == "__main__":
    check_script("RELIANCE-EQ")
