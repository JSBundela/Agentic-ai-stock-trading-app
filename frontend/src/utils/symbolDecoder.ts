/**
 * Ground Truth Symbol Decoder (PHASE 2)
 * NO REGEX. NO GESSING.
 * Lookup ONLY via Scrip Master pTrdSymbol.
 */

export type InstrumentType = 'EQUITY' | 'FUTURES' | 'OPTIONS' | 'UNKNOWN';

export interface ParsedInstrument {
    symbol: string;
    baseSymbol: string;
    instrumentType: InstrumentType;
    optionType?: string;
    strikePrice?: number;
    expiryDate?: string;
    isDerivative: boolean;
    displayName: string;
    isVerified: boolean;
    exchange: string;
    lotSize: number;
    companyName?: string;
    description?: string;
}

// Scrip master cache
const scripCache = new Map<string, any>();

/**
 * Format ISO date (YYYY-MM-DD) to "DD MMM" (e.g., "13 JAN")
 */
function formatExpiry(isoDate: string | null): string {
    if (!isoDate) return '';
    try {
        const date = new Date(isoDate);
        const day = date.getUTCDate();
        const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
        const month = months[date.getUTCMonth()];
        return `${day} ${month}`;
    } catch {
        return isoDate;
    }
}

/**
 * Pre-fetch scrip data for symbol
 */
async function fetchScrip(symbol: string): Promise<any> {
    try {
        const API = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');
        const response = await fetch(`${API}/scripmaster/scrip/${symbol}`);
        const json = await response.json();
        if (json.stat === 'Ok' && json.data) {
            scripCache.set(symbol, json.data);
            return json.data;
        }
    } catch { }
    return null;
}

/**
 * Parse symbol using Scrip Master Ground Truth
 */
export function parseSymbol(symbol: string, providedScrip?: any): ParsedInstrument {
    if (!symbol || typeof symbol !== 'string') {
        return {
            symbol: 'UNKNOWN',
            baseSymbol: 'UNKNOWN',
            instrumentType: 'UNKNOWN',
            isDerivative: false,
            displayName: 'UNKNOWN',
            isVerified: false,
            exchange: '',
            lotSize: 1
        };
    }
    const s = symbol.trim();
    const scrip = providedScrip || scripCache.get(s);

    if (!scrip) {
        // Not in cache - fetch async in background
        fetchScrip(s);

        // Return raw symbol as UNVERIFIED
        return {
            symbol: s,
            baseSymbol: s,
            instrumentType: 'UNKNOWN',
            isDerivative: false,
            displayName: s,
            isVerified: false,
            exchange: '',
            lotSize: 1
        };
    }

    // Scrip data available - GROUND TRUTH DECODING
    const {
        exchangeSegment,
        instrumentType: inst,
        optionType: optType,
        expiryDateISO,
        strikePrice,
        tradingSymbol,
        lotSize
    } = scrip;

    const exchange = (exchangeSegment || '').toLowerCase().includes('nse') ? 'NSE' : 'BSE';

    // Determine Type
    let type: InstrumentType = 'UNKNOWN';
    if (inst === 'EQ') type = 'EQUITY';
    else if (inst && inst.includes('FUT')) type = 'FUTURES';
    else if (inst && inst.includes('OPT')) type = 'OPTIONS';

    // Base Symbol (usually before digits or special chars)
    // For lookup, we rely on tradingSymbol or s
    const raw = tradingSymbol || s;
    const base = raw.split(/[0-9-]/)[0];

    let displayName: string;
    const expiry = formatExpiry(expiryDateISO);

    if (type === 'EQUITY') {
        displayName = `${base} ${exchange}`;
    } else if (type === 'FUTURES') {
        displayName = `${base} FUT (${expiry} ${exchange})`;
    } else if (type === 'OPTIONS') {
        const callPut = optType === 'CE' ? 'CALL' : optType === 'PE' ? 'PUT' : optType;
        const strike = strikePrice > 0 ? strikePrice : '';
        displayName = `${base} ${strike} ${callPut} (${expiry} ${exchange})`;
    } else {
        displayName = raw;
    }

    return {
        symbol: raw,
        baseSymbol: base,
        instrumentType: type,
        optionType: optType !== 'XX' ? optType : undefined,
        strikePrice: strikePrice > 0 ? strikePrice : undefined,
        expiryDate: expiry,
        isDerivative: type !== 'EQUITY' && type !== 'UNKNOWN',
        displayName: displayName,
        isVerified: true,
        exchange,
        lotSize: parseInt(lotSize) || 1,
        companyName: scrip.companyName,
        description: scrip.description
    };
}

/**
 * Prefetch scrips for all order symbols
 */
export async function prefetchSymbols(symbols: string[]): Promise<void> {
    const uniqueSymbols = Array.from(new Set(symbols));
    await Promise.all(uniqueSymbols.map(s => fetchScrip(s)));
}
