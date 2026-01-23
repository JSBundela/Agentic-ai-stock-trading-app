import apiClient from '../api/client';
import type { OrderBookResponse, ModifyOrderRequest } from '../types/order';

export const orderService = {
    // Place Order
    placeOrder: async (data: any): Promise<any> => {
        const response = await apiClient.post('/orders/place', data);
        return response.data;
    },

    // Fetch Order Book
    getOrderBook: async (days: number = 3): Promise<OrderBookResponse> => {
        const response = await apiClient.get(`/orders/order-book?days=${days}`);
        return response.data;
    },

    // Modify Order
    modifyOrder: async (request: ModifyOrderRequest): Promise<any> => {
        const response = await apiClient.post('/orders/modify', request);
        return response.data;
    },

    // Cancel Order
    cancelOrder: async (orderId: string): Promise<any> => {
        const response = await apiClient.delete(`/orders/${orderId}`);
        return response.data;
    }
};
