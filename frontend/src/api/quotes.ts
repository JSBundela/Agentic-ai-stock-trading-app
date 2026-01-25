import apiClient from './client';

/**
 * Quotes API Service - Data Fetch Layer ONLY
 * Based on kotak_api_documentation.md Lines 1353-1491
 * 
 * NO UI RENDERING - Console logging for verification
 */

// Exact types from API documentation (Lines 1443-1471)
export interface QuotesAPIResponse {
    exchange_token: string;       // Instrument token or index name
    display_symbol: string;        // UI display symbol
    exchange: string;              // Exchange segment (nse_cm, bse_cm, nse_fo, bse_fo)
    lstup_time: string;            // Last update time (Unix timestamp)
    ltp: string;                   // Last traded price
    last_traded_quantity: string;  // Last traded quantity
    total_buy: string;             // Top bid quantity
    total_sell: string;            // Top offer quantity
    last_volume: string;           // Most recent trade volume
    change: string;                // Net price change from previous close
    per_change: string;            // Percent price change
    year_high: string;             // 52-week high
    year_low: string;              // 52-week low
    ohlc: {
        open: string;    // Day's open price
        high: string;    // Day's high price
        low: string;     // Day's low price
        close: string;   // Previous close price
    };
    depth: {
        buy: Array<{
            price: string;     // Price level
            quantity: string;  // Quantity at level
            orders: string;    // Order count at level
        }>;
        sell: Array<{
            price: string;
            quantity: string;
            orders: string;
        }>;
    };
}

/**
 * Fetch Quotes from backend API
 * Backend proxies to Kotak Quotes API
 * 
 * @param symbol - Trading symbol (e.g., "RELIANCE-EQ", "11536")
 * @param exchange - Exchange segment (e.g., "nse_cm", "bse_cm")
 * @returns Quotes API response array
 */
export async function fetchQuotes(symbol: string, exchange: string = 'nse_cm'): Promise<QuotesAPIResponse[]> {
    console.group('🔵 Quotes API Fetch');
    // console.log('Symbol:', symbol);
    // console.log('Exchange:', exchange);
    // console.log('Endpoint: POST /market/quotes');

    try {
        const response = await apiClient.post('/market/quotes', {
            instrument_tokens: [`${exchange}|${symbol}`]
        });

        const data = response.data;

        // console.log('✅ RAW API RESPONSE:', JSON.stringify(data, null, 2));
        // console.log('---');
        // console.log('Response Type:', Array.isArray(data) ? 'Array' : typeof data);
        // console.log('Response Length:', Array.isArray(data) ? data.length : 'N/A');

        if (Array.isArray(data) && data.length > 0) {
            const quote = data[0];

            // Log key fields for verification
            console.group('📊 Verified Fields');
            // console.log('LTP:', quote.ltp);
            // console.log('Change:', quote.change);
            // console.log('% Change:', quote.per_change);
            // console.log('Display Symbol:', quote.display_symbol);
            // console.log('Exchange:', quote.exchange);
            // console.log('Last Update:', quote.lstup_time);
            console.groupEnd();

            console.group('📈 OHLC Data');
            // console.log('Open:', quote.ohlc?.open);
            // console.log('High:', quote.ohlc?.high);
            // console.log('Low:', quote.ohlc?.low);
            // console.log('Close:', quote.ohlc?.close);
            console.groupEnd();

            console.group('📊 Market Depth');
            // console.log('Buy Depth (5 levels):', quote.depth?.buy);
            // console.log('Sell Depth (5 levels):', quote.depth?.sell);
            console.groupEnd();

            console.group('📉 Volume & Trading');
            // console.log('Volume:', quote.last_volume);
            // console.log('LastTradedQty:', quote.last_traded_quantity);
            // console.log('Total Buy:', quote.total_buy);
            // console.log('Total Sell:', quote.total_sell);
            console.groupEnd();

            console.group('📅 52-Week Range');
            // console.log('52W High:', quote.year_high);
            // console.log('52W Low:', quote.year_low);
            console.groupEnd();
        } else {
            console.warn('⚠️  Empty or invalid response');
        }

        console.groupEnd();
        return data;

    } catch (error: any) {
        console.error('❌ Quotes API Error:', error);
        console.error('Error Details:', error.response?.data || error.message);
        console.groupEnd();
        throw error;
    }
}

/**
 * Parse string field to number safely
 * API returns all fields as strings (Line 1486)
 * 
 * @param value - String value from API
 * @param fallback - Fallback number if parsing fails
 * @returns Parsed number or fallback
 */
export function parseNumericField(value: string | undefined, fallback: number = 0): number {
    if (!value || value === '') return fallback;
    const parsed = parseFloat(value);
    return isNaN(parsed) ? fallback : parsed;
}

/**
 * Check if market data is valid (not all zeros)
 * Documentation example shows "0" for all fields when no data (Lines 1428-1437)
 * 
 * @param quote - Quote data to check
 * @returns true if data appears valid
 */
export function isValidQuoteData(quote: QuotesAPIResponse | null): boolean {
    if (!quote) return false;

    // Check if LTP is not zero
    const ltp = parseNumericField(quote.ltp);
    if (ltp === 0) {
        console.warn('⚠️  LTP is 0 - market may be closed or data unavailable');
        return false;
    }

    return true;
}

export const quotesAPI = {
    fetchQuotes,
    parseNumericField,
    isValidQuoteData
};
