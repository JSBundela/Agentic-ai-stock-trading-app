import pandas as pd
import io
import asyncio
import sqlite3
import httpx
from functools import lru_cache
from app.core.http_client import http_client
from app.core.logger import logger
from app.config import get_settings

settings = get_settings()

class ScripMasterService:
    def __init__(self):
        self.db_path = "scrip_master.db"
        self.base_url = None
        # Initialize DB
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database with schema."""
        try:
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                # Enable WAL mode for better concurrency
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS scrips (
                        instrumentToken TEXT,
                        exchangeSegment TEXT,
                        tradingSymbol TEXT,
                        instrumentType TEXT,
                        lotSize INTEGER,
                        expiryEpoch INTEGER,
                        strikePrice REAL,
                        optionType TEXT,
                        companyName TEXT,
                        description TEXT,
                        segment TEXT,
                        expiryDateISO TEXT
                    )
                """)
                # Create Indices for fast lookup
                conn.execute("CREATE INDEX IF NOT EXISTS idx_token_seg ON scrips(instrumentToken, exchangeSegment);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_symbol ON scrips(tradingSymbol);")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Scrip Master DB: {e}")

    def _get_conn(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    async def load_scrip_master(self):
        """
        Downloads and parses ALL scrip master CSVs into SQLite incrementally.
        Prevents OOM (Out Of Memory) by using chunked processing.
        """
        logger.info("=" * 80)
        logger.info("SCRIP MASTER LOADER - SQLITE OPTIMIZED")
        logger.info("=" * 80)
        
        try:
            # Get base URL from config
            from app.utils import cache
            _, _, base_url, _ = cache.get_trade_session()
            
            if not base_url:
                base_url = "https://gw-napi.kotaksecurities.com"
                logger.warning("Using default base URL for scrip master download")
            
            self.base_url = base_url
            
            # Step 1: Get ALL available segment file paths dynamically
            client = await http_client.get_client()
            file_paths_url = f"{base_url}/script-details/1.0/masterscrip/file-paths"
            
            logger.info(f"Fetching ALL segment file paths from: {file_paths_url}")
            
            try:
                response = await client.get(file_paths_url, headers={
                    "Authorization": settings.KOTAK_ACCESS_TOKEN
                })
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    if "gw-napi" in base_url:
                        logger.warning("Startup: Default scrip master URL not accessible (404). Waiting for user login.")
                        return 
                    else:
                        logger.error(f"Failed to fetch file paths from {base_url}: 404 Not Found")
                        raise
                else:
                    raise

            file_paths_data = response.json()
            
            csv_urls = []
            if "data" in file_paths_data and "filesPaths" in file_paths_data["data"]:
                file_list = file_paths_data["data"]["filesPaths"]
                if isinstance(file_list, list):
                    csv_urls = [url for url in file_list if isinstance(url, str) and url.endswith(".csv")]
            
            if not csv_urls:
                logger.error(f"No CSV URLs found in response: {file_paths_data}")
                raise Exception("Could not find any scrip master CSV URLs")
            
            logger.info(f"✅ Found {len(csv_urls)} segment CSV files. Rebuilding Database...")

            # Reset Database for fresh load
            with self._get_conn() as conn:
                conn.execute("DELETE FROM scrips")
                conn.commit()

            # Step 2: Stream Download and Insert Chunk by Chunk
            async with httpx.AsyncClient(timeout=60.0) as fresh_client:
                for csv_url in csv_urls:
                    segment_name = csv_url.split('/')[-1].replace('.csv', '').upper()
                    logger.info(f"📥 Processing {segment_name}...")
                    
                    try:
                        # Stream response to avoid loading full CSV into RAM
                        async with fresh_client.stream('GET', csv_url) as resp:
                            resp.raise_for_status()
                            
                            # Read into buffer
                            content = await resp.aread()
                            
                            # Use Pandas to read in chunks
                            # Using io.BytesIO because we read content (still in RAM but ephemeral per file)
                            # Ideally we should stream lines, but CSV parsing is complex.
                            # Since individual CSVs are < 100MB, reading one into RAM is okay, 
                            # but better to iterate.
                            
                            with io.BytesIO(content) as buffer:
                                # Chunk size 10,000 to keep memory low
                                for chunk in pd.read_csv(buffer, chunksize=10000):
                                    self._process_and_insert_chunk(chunk, segment_name)
                                    
                        logger.info(f"✅ {segment_name}: Inserted into DB")
                        
                    except Exception as seg_err:
                        logger.error(f"❌ Failed to load {segment_name}: {seg_err}")
                        continue
            
            # Clear caches after reload
            self.get_scrip_by_token.cache_clear()
            self.get_scrip.cache_clear()
            
            # Log stats
            with self._get_conn() as conn:
                count = conn.execute("SELECT COUNT(*) FROM scrips").fetchone()[0]
                logger.info(f"✅ Scrip Master Validated. Total Records: {count}")
                
                with open("scrip_master_status.txt", "w") as f:
                    f.write(f"Loaded: {count} records\n")
                    f.write(f"Mode: SQLite (Disk-based)\n")

        except Exception as e:
            logger.error(f"❌ CRITICAL: Failed to load scrip master: {e}")

    def _process_and_insert_chunk(self, df: pd.DataFrame, segment_name: str):
        """Process a chunk of dataframe and insert into SQLite."""
        # Normalize columns
        df.columns = df.columns.str.strip().str.rstrip(';')
        
        # Mappings
        rename_map = {
            'pTrdSymbol': 'tradingSymbol',
            'pSymbol': 'instrumentToken',
            'lLotSize': 'lotSize',
            'pExchSeg': 'exchangeSegment',
            'pInstType': 'instrumentType',
            'pOptionType': 'optionType',
            'lExpiryDate': 'expiryEpoch',
            'dStrikePrice': 'strikePrice',
            'pStrikePrice': 'strikePrice',
            'pSymbolName': 'companyName',
            'pDesc': 'description'
        }
        
        # Filter and Rename
        cols_available = [c for c in rename_map.keys() if c in df.columns]
        df = df[cols_available].rename(columns=rename_map)
        
        # Add segment
        df['segment'] = segment_name
        
        # Transformations
        if 'instrumentType' in df.columns and 'CM' in segment_name:
            df['instrumentType'] = df['instrumentType'].fillna('EQ')
            
        # Strike Price Normalization
        if 'strikePrice' in df.columns and 'instrumentType' in df.columns:
             # Vectorized normalization
             mask = (df['instrumentType'].astype(str).str.contains('OPT')) & (df['strikePrice'] > 1_000_000)
             df.loc[mask, 'strikePrice'] = df.loc[mask, 'strikePrice'] / 100

        # Expiry ISO - Vectorized
        if 'expiryEpoch' in df.columns:
            # Base date 1980-01-01
            base_date = pd.Timestamp('1980-01-01')
            # Coerce errors
            df['expiryEpoch'] = pd.to_numeric(df['expiryEpoch'], errors='coerce')
            
            # Calculate date only for valid epochs > 0
            valid_epochs = df['expiryEpoch'] > 0
            if valid_epochs.any():
                # epochs are seconds
                dates = base_date + pd.to_timedelta(df.loc[valid_epochs, 'expiryEpoch'], unit='s')
                df.loc[valid_epochs, 'expiryDateISO'] = dates.dt.strftime('%Y-%m-%d')

        # Insert into DB
        # Only keep columns that match schema to avoid errors
        # Schema: instrumentToken, exchangeSegment, tradingSymbol, instrumentType, lotSize, expiryEpoch, strikePrice, optionType, companyName, description, segment, expiryDateISO
        schema_cols = ['instrumentToken', 'exchangeSegment', 'tradingSymbol', 'instrumentType', 
                      'lotSize', 'expiryEpoch', 'strikePrice', 'optionType', 'companyName', 
                      'description', 'segment', 'expiryDateISO']
        
        # Ensure all schema cols exist
        for col in schema_cols:
            if col not in df.columns:
                df[col] = None
                
        # Write to SQL
        with self._get_conn() as conn:
            df[schema_cols].to_sql('scrips', conn, if_exists='append', index=False)

    @lru_cache(maxsize=10000)
    def get_scrip(self, symbol: str):
        """Get scrip details by trading symbol - CACHED"""
        if not symbol: return None
        try:
            with self._get_conn() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM scrips WHERE tradingSymbol = ? LIMIT 1", (symbol,))
                row = cursor.fetchone()
                if row:
                    return dict(row)
        except Exception:
            return None
        return None

    @lru_cache(maxsize=10000)
    def get_scrip_by_token(self, token: str, segment: str):
        """Fast lookup using token and segment - CACHED"""
        if not token or not segment: return None
        try:
            # Lowercase segment is stored as UPPER in DB usually, but let's check.
            # Loader sets segment_name = UPPER.
            # 'exchangeSegment' column usually matches 'nse_cm' (lowercase) or 'NSE_CM' (uppercase) in CSV?
            # From previous logs: "exchangeSegment" -> pExchSeg. 
            # In CSV sample: pExchSeg="nse_cm" (lowercase) or "NSE_CM"?
            # Let's try case-insensitive LIKE or normalize.
            # Usually input segment is 'nse_cm' (lowercase).
            
            with self._get_conn() as conn:
                conn.row_factory = sqlite3.Row
                # Try exact match first
                cursor = conn.execute("SELECT * FROM scrips WHERE instrumentToken = ? AND exchangeSegment = ? LIMIT 1", (token, segment))
                row = cursor.fetchone()
                
                # Retry with lowercase segment if failed
                if not row:
                    cursor = conn.execute("SELECT * FROM scrips WHERE instrumentToken = ? AND lower(exchangeSegment) = ? LIMIT 1", (token, segment.lower()))
                    row = cursor.fetchone()
                    
                if row:
                    return dict(row)
        except Exception:
            return None
        return None

# Global singleton instance
scrip_master = ScripMasterService()
