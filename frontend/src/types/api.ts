// TypeScript interfaces matching backend APIs

export interface LoginRequest {
    totp: string;
}

export interface MPINRequest {
    mpin: string;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
    expires_in?: number;
    refresh_token?: string;
    sid?: string;
    baseUrl?: string;
    dataCenter?: string;
    message?: string;
}

export interface OrderRequest {
    trading_symbol: string;
    transaction_type: "BUY" | "SELL";
    order_type: "LIMIT" | "MARKET" | "SL-LMT" | "SL-MKT";
    product_type: "CNC" | "MIS" | "NRML" | "BO" | "CASH" | "MTF" | "CO";
    quantity: number;
    price: number;
    trigger_price: number;
    validity: "GFD" | "IOC";
    amo: boolean;
    disclosed_quantity?: number;
    sl_spread?: number;
    tg_spread?: number;
    trailing_sl?: number;
}

export interface ModifyOrderRequest {
    order_id: string;
    quantity?: number;
    price?: number;
    order_type?: string;
}

export interface Order {
    nOrdNo: string;          // Order number
    trdSym: string;          // Trading symbol
    qty: number;             // Quantity
    prc: string;             // Price
    ordSt: string;           // Order status (OPEN, AMO, REJECTED, etc.)
    trnsTp: string;          // Transaction type (B/S)
    prcTp: string;           // Price type (L/MKT)
    prod: string;            // Product (CNC/MIS)
    vldt: string;            // Validity (DAY/IOC)
    ordGenTp: string;        // Order gen type (AMO or empty)
    rejRsn?: string;         // Rejection reason
    avgPrc?: string;         // Average price
    [key: string]: any;      // Other fields from backend
}

export interface OrderBookResponse {
    stat: string;
    stCode: number;
    data: Order[];
}

export interface LimitsResponse {
    stat: string;
    stCode: number;
    data?: any;
    Net?: string;
    [key: string]: any;
}

export interface QuoteRequest {
    instrument_tokens: string[];
}
