import apiClient from './client';
import type { OrderRequest, ModifyOrderRequest, OrderBookResponse } from '../types/api';

/**
 * Order Management APIs
 * Uses verified backend endpoints - NO MODIFICATIONS
 */

export const ordersAPI = {
    /**
     * POST /orders/place
     * Place a new order (regular or AMO)
     */
    placeOrder: async (data: OrderRequest): Promise<any> => {
        const response = await apiClient.post('/orders/place', data);
        return response.data;
    },

    /**
     * GET /orders/order-book
     * Fetch all orders
     */
    getOrderBook: async (): Promise<OrderBookResponse> => {
        const response = await apiClient.get<OrderBookResponse>('/orders/order-book');
        return response.data;
    },

    /**
     * POST /orders/modify
     * Modify an existing order
     */
    modifyOrder: async (data: ModifyOrderRequest): Promise<any> => {
        const response = await apiClient.post('/orders/modify', data);
        return response.data;
    },

    /**
     * DELETE /orders/{order_id}
     * Cancel an order
     */
    cancelOrder: async (orderId: string): Promise<any> => {
        const response = await apiClient.delete(`/orders/${orderId}`);
        return response.data;
    },

    /**
     * GET /orders/trade-book
     * Fetch executed trades
     */
    getTradeBook: async (): Promise<any> => {
        const response = await apiClient.get('/orders/trade-book');
        return response.data;
    },
};
