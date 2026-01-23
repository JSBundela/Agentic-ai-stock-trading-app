import apiClient from './client';
import type { QuoteRequest } from '../types/api';

/**
 * Market Data APIs
 * Uses verified backend endpoints - NO MODIFICATIONS
 */

export const marketAPI = {
    /**
     * POST /market/quotes
     * Get live market quotes
     */
    getQuotes: async (data: QuoteRequest): Promise<any> => {
        const response = await apiClient.post('/market/quotes', data);
        return response.data;
    },
};
