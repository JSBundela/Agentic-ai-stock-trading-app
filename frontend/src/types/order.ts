export interface Order {
    nOrdNo: string;           // Order Number
    trdSym: string;           // Trading Symbol (e.g., RELIANCE-EQ)
    qty: number;              // Quantity
    fldQty?: number;          // Filled Quantity (some APIs return this)
    prc: string;              // Price (string from API)
    avgPrc?: string;          // Average Price
    ordSt: string;            // Status (OPEN, COMPLETE, REJECTED, etc.)
    trnsTp: string;           // Transaction Type (B/S)
    prcTp: string;            // Price Type (L, MKT, SL, SL-M)
    prod: string;             // Product (CNC, MIS, NRML)
    ordDtTm: string;          // Order Date Time
    exSeg: string;            // Exchange Segment (nse_cm, etc.)
    rejRsn?: string;          // Rejection Reason

    // AMO fields
    ordGenTp?: string;        // "AMO" if AMO order

    // Database fields (merged)
    _source?: string;         // 'database' if historical
}

export interface PlaceOrderRequest {
    trading_symbol: string;
    transaction_type: 'BUY' | 'SELL';
    order_type: 'LIMIT' | 'MARKET' | 'SL' | 'SL-M';
    product_type: 'CNC' | 'MIS' | 'NRML';
    quantity: number;
    price: number;
    trigger_price: number;
    validity: 'GFD' | 'IOC';
    amo: boolean;
    disclosed_quantity?: number;
}

export interface ModifyOrderRequest {
    order_id: string;
    quantity?: number;
    price?: number;
    order_type?: string;
}

export interface OrderBookResponse {
    stat: string;
    data: Order[];
}
