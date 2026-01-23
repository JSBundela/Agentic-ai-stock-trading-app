import apiClient from './client';
import type { LimitsResponse } from '../types/api';

/**
 * Portfolio APIs
 * Uses verified backend endpoints - NO MODIFICATIONS
 */

export const portfolioAPI = {
    /**
     * GET /portfolio/limits
     * Fetch margin/limits data
     */
    getLimits: async (): Promise<LimitsResponse> => {
        const response = await apiClient.post<LimitsResponse>('/portfolio/limits');
        return response.data;
    },

    /**
     * GET /portfolio/positions
     * Fetch positions
     */
    getPositions: async (): Promise<any> => {
        const response = await apiClient.get('/portfolio/positions');
        return response.data;
    },

    /**
     * GET /portfolio/holdings
     * Fetch holdings
     */
    getHoldings: async (): Promise<any> => {
        const response = await apiClient.get('/portfolio/holdings');
        return response.data;
    },
};
