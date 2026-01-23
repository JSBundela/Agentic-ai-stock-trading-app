import pandas as pd
import io
import asyncio
from app.core.http_client import http_client
from app.core.logger import logger
from app.config import get_settings
import httpx

settings = get_settings()

class ScripMasterService:
    def __init__(self):
        self.scrip_data = None
        self.base_url = None
        self._token_map = {}  # (token, segment) -> scrip_dict
        
    async def load_scrip_master(self):
        """
        Downloads and parses ALL scrip master CSVs dynamically from Kotak Neo API.
        CRITICAL: This is the SINGLE SOURCE OF TRUTH for all instrument metadata.
        NO regex, NO parsing, NO guessing - scrip master data ONLY.
        """
        logger.info("=" * 80)
        logger.info("SCRIP MASTER LOADER - SINGLE SOURCE OF TRUTH")
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
            
            response = await client.get(file_paths_url, headers={
                "Authorization": settings.KOTAK_ACCESS_TOKEN
            })
            response.raise_for_status()
            
            file_paths_data = response.json()
            
            # Step 2: Extract ALL CSV URLs dynamically (no hardcoding)
            csv_urls = []
            if "data" in file_paths_data and "filesPaths" in file_paths_data["data"]:
                file_list = file_paths_data["data"]["filesPaths"]
                if isinstance(file_list, list):
                    csv_urls = [url for url in file_list if isinstance(url, str) and url.endswith(".csv")]
            
            if not csv_urls:
                logger.error(f"No CSV URLs found in response: {file_paths_data}")
                raise Exception("Could not find any scrip master CSV URLs")
            
            logger.info(f"✅ Found {len(csv_urls)} segment CSV files")
            for url in csv_urls:
                segment_name = url.split('/')[-1].replace('.csv', '')
                logger.info(f"  - {segment_name}")
            
            # Step 3: Download and process ALL CSVs
            all_dataframes = []
            
            async with httpx.AsyncClient(timeout=30.0) as fresh_client:
                for csv_url in csv_urls:
                    segment_name = csv_url.split('/')[-1].replace('.csv', '').upper()
                    
                    try:
                        logger.info(f"📥 Downloading {segment_name}...")
                        csv_response = await fresh_client.get(csv_url)
                        csv_response.raise_for_status()
                        
                        # Parse CSV
                        csv_content = csv_response.text
                        df = pd.read_csv(io.StringIO(csv_content))
                        
                        # CRITICAL: Normalize column names
                        # 1. Strip whitespace
                        # 2. Remove trailing semicolons (e.g., "dStrikePrice;" -> "dStrikePrice")
                        df.columns = df.columns.str.strip().str.rstrip(';')
                        
                        logger.info(f"📋 {segment_name} columns: {list(df.columns)}")
                        
                        # Define ALL possible metadata columns
                        base_columns = ['pTrdSymbol', 'pSymbol', 'pExchSeg', 'lLotSize']
                        metadata_columns = [
                            'pInstType',      # Instrument type (EQ, FUTIDX, OPTIDX, etc.)
                            'pOptionType',    # CE, PE, XX
                            'lExpiryDate',    # REAL expiry date (Unix timestamp)
                            'dStrikePrice',   # Strike price (variant 1)
                            'pStrikePrice',   # Strike price (variant 2)
                            'pSymbolName',    # Full company name (e.g., Bharat Electronics Limited)
                            'pDesc',          # Description
                        ]
                        
                        # Select columns that exist in this CSV
                        columns_to_load = []
                        for col in base_columns + metadata_columns:
                            if col in df.columns:
                                columns_to_load.append(col)
                        
                        if 'pTrdSymbol' not in columns_to_load or 'pSymbol' not in columns_to_load:
                            logger.warning(f"⚠️  {segment_name} missing required columns, skipping")
                            continue
                        
                        # Extract available fields
                        segment_df = df[columns_to_load].copy()
                        
                        # Rename for consistency
                        rename_map = {
                            'pTrdSymbol': 'tradingSymbol',
                            'pSymbol': 'instrumentToken',
                            'lLotSize': 'lotSize',
                            'pExchSeg': 'exchangeSegment',
                            'pInstType': 'instrumentType',
                            'pOptionType': 'optionType',
                            'lExpiryDate': 'expiryEpoch',  # Keep epoch for processing
                            'dStrikePrice': 'strikePrice',
                            'pStrikePrice': 'strikePrice',  # Map both variants to same name
                            'pSymbolName': 'companyName',
                            'pDesc': 'description'
                        }
                        
                        # Only rename columns that exist
                        actual_rename = {k: v for k, v in rename_map.items() if k in segment_df.columns}
                        segment_df = segment_df.rename(columns=actual_rename)
                        
                        # CRITICAL FIX: Convert Kotak expiry epoch to ISO date
                        # Kotak F&O CSV expiryEpoch is seconds since 2000-01-01, NOT Unix epoch
                        if 'expiryEpoch' in segment_df.columns:
                            from datetime import datetime, timedelta
                            
                            def convert_kotak_epoch(epoch_val):
                                """Convert Kotak epoch (seconds since 1980-01-01) to ISO date"""
                                try:
                                    if pd.isna(epoch_val) or epoch_val < 0:
                                        return None
                                    # Base date for Kotak: 1980-01-01 00:00:00
                                    base_date = datetime(1980, 1, 1)
                                    expiry_datetime = base_date + timedelta(seconds=int(epoch_val))
                                    return expiry_datetime.strftime('%Y-%m-%d')
                                except:
                                    return None
                            
                            segment_df['expiryDateISO'] = segment_df['expiryEpoch'].apply(convert_kotak_epoch)
                        
                        # CRITICAL FIX: Normalize strike price
                        # Kotak stores strike prices in scaled units (e.g., 2590000 for 25900)
                        if 'strikePrice' in segment_df.columns and 'instrumentType' in segment_df.columns:
                            def normalize_strike(row):
                                """Normalize strike price for options"""
                                try:
                                    strike = row.get('strikePrice')
                                    inst_type = row.get('instrumentType')
                                    
                                    if pd.isna(strike) or strike < 0:
                                        return strike
                                    
                                    # If options instrument with strike > 1 million, divide by 100
                                    if inst_type and 'OPT' in str(inst_type) and strike > 1_000_000:
                                        normalized = strike / 100
                                        return normalized
                                    
                                    return strike
                                except:
                                    return row.get('strikePrice')
                            
                            segment_df['strikePrice'] = segment_df.apply(normalize_strike, axis=1)
                        
                        # CRITICAL FIX: Set instrumentType = "EQ" for equity segments when null
                        if 'instrumentType' in segment_df.columns and 'CM' in segment_name:
                            segment_df['instrumentType'] = segment_df['instrumentType'].fillna('EQ')
                        
                        # Add segment label
                        segment_df['segment'] = segment_name
                        
                        logger.info(f"✅ {segment_name}: Loaded {len(segment_df)} instruments")
                        logger.info(f"   Columns: {list(segment_df.columns)}")
                        
                        # VERIFICATION: Show sample rows for F&O segments
                        if any(x in segment_name for x in ['FO', 'CD', 'MCX']):
                            logger.info(f"📊 SAMPLE VERIFICATION for {segment_name}:")
                            
                            sample_cols = ['tradingSymbol', 'instrumentType', 'optionType', 'strikePrice', 'expiryDateISO', 'expiryEpoch']
                            available_sample_cols = [c for c in sample_cols if c in segment_df.columns]
                            
                            # Sample FUTIDX
                            fut_samples = segment_df[segment_df['instrumentType'] == 'FUTIDX'].head(3)
                            if not fut_samples.empty:
                                logger.info(f"   📌 FUTIDX Samples:")
                                for idx, row in fut_samples.iterrows():
                                    row_data = {col: row[col] for col in available_sample_cols if col in row.index}
                                    logger.info(f"      {row_data}")
                            
                            # Sample OPTIDX
                            opt_samples = segment_df[segment_df['instrumentType'] == 'OPTIDX'].head(5)
                            if not opt_samples.empty:
                                logger.info(f"   📌 OPTIDX Samples:")
                                for idx, row in opt_samples.iterrows():
                                    row_data = {col: row[col] for col in available_sample_cols if col in row.index}
                                    logger.info(f"      {row_data}")
                        
                        # Sample EQ from nse_cm/bse_cm
                        if 'CM' in segment_name:
                            eq_samples = segment_df.head(3)
                            if not eq_samples.empty:
                                logger.info(f"   📌 EQUITY Samples from {segment_name}:")
                                sample_cols = ['tradingSymbol', 'instrumentType', 'optionType', 'exchangeSegment']
                                available_sample_cols = [c for c in sample_cols if c in segment_df.columns]
                                for idx, row in eq_samples.iterrows():
                                    row_data = {col: row[col] for col in available_sample_cols if col in row.index}
                                    logger.info(f"      {row_data}")
                        
                        all_dataframes.append(segment_df)
                        
                    except Exception as seg_err:
                        logger.error(f"❌ Failed to load {segment_name}: {seg_err}")
                        continue
            
            if not all_dataframes:
                logger.error("❌ No dataframes loaded successfully")
                raise Exception("Failed to load any scrip master data")
            
            # Step 4: Merge ALL segments into single DataFrame
            logger.info("🔗 Merging all segments...")
            self.scrip_data = pd.concat(all_dataframes, ignore_index=True)
            
            # Index by trading symbol for fast lookup
            self.scrip_data = self.scrip_data.set_index('tradingSymbol')
            
            logger.info("=" * 80)
            
            # Optimized Token Map Build
            # 1. Reset index temporarily to include tradingSymbol in dict
            temp_df = self.scrip_data.reset_index()
            
            # 2. Build map using record-based conversion (massively faster than iterrows)
            records = temp_df.to_dict('records')
            self._token_map = {
                (str(r['instrumentToken']), str(r['exchangeSegment']).lower()): r 
                for r in records
            }
            
            logger.info(f"✅ Token map built: {len(self._token_map)} entries (Optimized)")
            
            with open("scrip_master_status.txt", "w") as f:
                f.write(f"Loaded: {len(self.scrip_data) if self.scrip_data is not None else 0} records\n")
                f.write(f"Segments: {self.scrip_data['segment'].unique().tolist() if self.scrip_data is not None else []}\n")
                f.write(f"Columns: {self.scrip_data.columns.tolist() if self.scrip_data is not None else []}\n")
            
        except Exception as e:
            logger.error(f"❌ CRITICAL: Failed to load scrip master: {e}")
            logger.warning("Using empty scrip master - symbol decoding will fail")
            self.scrip_data = pd.DataFrame()
    
    def get_scrip(self, symbol: str):
        """Get scrip details by trading symbol - GROUND TRUTH ONLY"""
        if self.scrip_data is None or self.scrip_data.empty:
            return None
        
        if symbol not in self.scrip_data.index:
            return None
        
        # Get row and replace NaN with None for JSON serialization
        scrip_row = self.scrip_data.loc[symbol]
        # loc can return a DataFrame if duplicate index exists (shouldn't happen with tradingSymbol)
        if isinstance(scrip_row, pd.DataFrame):
            scrip_row = scrip_row.iloc[0]
            
        scrip_dict = scrip_row.where(scrip_row.notna(), None).to_dict()
        scrip_dict['tradingSymbol'] = symbol
        
        return scrip_dict

    def get_scrip_by_token(self, token: str, segment: str):
        """Fast lookup for real-time ticks using token and segment."""
        return self._token_map.get((str(token), str(segment).lower()))

# Global singleton instance
scrip_master = ScripMasterService()
