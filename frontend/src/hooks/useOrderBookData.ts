import { useState, useEffect, useCallback } from 'react';
import { orderService } from '../services/orderService';

// Module-level cache
let orderBookCache: {
    data: any[];
    timestamp: number;
} | null = null;

/**
 * Normalize Kotak API order fields to frontend expectations
 * API: trdSym, ordSt, trnsTp, exSeg, ordDtTm, prdType
 * Frontend: tsym, status, trantype, exch, ordTime, prdtype
 */
const normalizeOrder = (apiOrder: any) => {
    console.log('[ORDER NORMALIZATION] Raw API order:', apiOrder);

    const normalized = {
        ...apiOrder,
        // Map API fields → Frontend fields
        tsym: apiOrder.trdSym || apiOrder.tsym,
        status: (apiOrder.ordSt || apiOrder.status || '').toLowerCase(),
        trantype: apiOrder.trnsTp || apiOrder.trantype,
        exch: apiOrder.exSeg || apiOrder.exch,
        ordTime: apiOrder.ordDtTm || apiOrder.ordTime,
        prdtype: apiOrder.prdType || apiOrder.prdtype || apiOrder.prod,
        fillqty: apiOrder.fldQty || apiOrder.fillqty || '0',
        // Keep original fields for reference
        _apiFields: {
            trdSym: apiOrder.trdSym,
            ordSt: apiOrder.ordSt,
            trnsTp: apiOrder.trnsTp,
            exSeg: apiOrder.exSeg
        }
    };

    console.log('[ORDER NORMALIZATION] Normalized order:', normalized);
    return normalized;
};

export const useOrderBookData = () => {
    const [orders, setOrders] = useState<any[]>(orderBookCache?.data || []);
    const [loading, setLoading] = useState(!orderBookCache);

    const fetchOrders = useCallback(async (isManualRefresh = false) => {
        if (isManualRefresh) setLoading(true);

        try {
            const response = await orderService.getOrderBook();
            const rawOrders = response.data || [];

            // CRITICAL: Normalize all orders
            const normalizedOrders = rawOrders.map(normalizeOrder);

            console.log('[ORDER BOOK] Fetched orders:', rawOrders.length);
            console.log('[ORDER BOOK] Sample normalized order:', normalizedOrders[0]);

            setOrders(normalizedOrders);

            orderBookCache = {
                data: normalizedOrders,
                timestamp: Date.now()
            };
        } catch (error) {
            console.error('Failed to fetch orders', error);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        // Initial fetch (only show loading if no cache)
        if (!orderBookCache) setLoading(true);
        fetchOrders();

        const interval = setInterval(() => fetchOrders(false), 5000);
        return () => clearInterval(interval);
    }, [fetchOrders]);

    const refresh = () => fetchOrders(true);

    return { orders, loading, refresh };
};
