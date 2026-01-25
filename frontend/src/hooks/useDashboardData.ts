import { useState, useEffect } from 'react';
import { portfolioService } from '../services/portfolioService';
import { orderService } from '../services/orderService';
import { useAuth } from '../context/AuthContext';

// Module-level cache (persists as long as the app is loaded)
let dashboardCache: {
    data: any;
    orders: any[];
    timestamp: number;
} | null = null;

export const useDashboardData = () => {
    const { isAuthenticated } = useAuth();
    const [data, setData] = useState<any>(dashboardCache?.data || null);
    const [orders, setOrders] = useState<any[]>(dashboardCache?.orders || []);
    const [loading, setLoading] = useState(!dashboardCache);

    useEffect(() => {
        let isMounted = true;
        let interval: any = null;

        const fetchDashboardData = async () => {
            // Skip fetching if not authenticated
            if (!isAuthenticated) {
                if (isMounted) setLoading(false);
                return;
            }

            try {
                // Fetch fresh data (including holdings for portfolio value calculation)
                const results = await Promise.allSettled([
                    portfolioService.getLimits(),
                    portfolioService.getPositions(),
                    portfolioService.getHoldings(),
                    orderService.getOrderBook(1)
                ]);

                const limits = results[0].status === 'fulfilled' ? results[0].value : {};
                const positions = results[1].status === 'fulfilled' ? results[1].value : { data: [] };
                const holdings = results[2].status === 'fulfilled' ? results[2].value : { data: [] };
                const orderBook = results[3].status === 'fulfilled' ? results[3].value : { data: [] };

                if (isMounted) {
                    const newData = { limits, positions, holdings };
                    const newOrders = (orderBook.data || []).slice(0, 6);

                    // Update state
                    setData(newData);
                    setOrders(newOrders);
                    setLoading(false);

                    // Update cache
                    dashboardCache = {
                        data: newData,
                        orders: newOrders,
                        timestamp: Date.now()
                    };
                }
            } catch (error) {
                console.error('Dashboard load failed', error);
                if (isMounted) setLoading(false);
            }
        };

        // Fetch immediately if authenticated
        if (isAuthenticated) {
            fetchDashboardData();
            // Poll every 10s
            interval = setInterval(fetchDashboardData, 10000);
        } else {
            setLoading(false);
        }

        return () => {
            isMounted = false;
            if (interval) clearInterval(interval);
        };
    }, [isAuthenticated]); // Re-run when auth state changes

    return { data, orders, loading };
};
