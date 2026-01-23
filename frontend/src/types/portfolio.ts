export interface Position {
    uid: string;              // User ID (or unique key if available)
    trdSym: string;           // Trading Symbol (e.g. RELIANCE-EQ)
    exSeg: string;            // Exchange Segment
    prod: string;             // Product (CNC, MIS)

    // Core Quantities
    netQty: string;           // Net Quantity (can be negative for Short)
    buyQty: string;
    sellQty: string;

    // Prices
    buyAvg: string;           // Average Buy Price
    sellAvg: string;          // Average Sell Price
    ltp: string;              // Last Traded Price (from API or WS)

    // P&L
    rpnl: string;             // Realized P&L
    urmtom: string;           // Unrealized MTM (from API)

    // Greeks/Extra (Optional)
    cfBuyQty?: string;
    cfSellQty?: string;
}

export interface Holding {
    trdSym: string;           // Trading Symbol
    exSeg: string;
    holdQty: string;          // Holdings Quantity
    colQty?: string;          // Collateral Qty

    // Prices
    avgPrc: string;           // Average Cost Price
    ltp: string;             // LTP

    // Attributes
    isCollateral?: boolean;
}

export interface Limits {
    stat: string;

    // Cash
    netCash: string;          // Net Cash Available
    cashBal: string;          // Opening Balance?

    // Margin
    marginUsed: string;       // Total Margin Used
    marginUtilized?: string;

    // Collateral
    collateralVal?: string;   // Collateral Value

    // Fallback/Test flags
    _fallback?: boolean;
}

export interface PortfolioResponse<T> {
    stat: string;
    stCode?: number;
    data: T[];
    message?: string;
}
