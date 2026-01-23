import axios from 'axios';
import type { PortfolioResponse, Position, Holding, Limits } from '../types/portfolio';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const portfolioService = {
    // Get Positions (Day/Net)
    getPositions: async (): Promise<PortfolioResponse<Position>> => {
        const response = await axios.get(`${API_URL}/portfolio/positions`);
        return response.data;
    },

    // Get Holdings (Long term)
    getHoldings: async (): Promise<PortfolioResponse<Holding>> => {
        const response = await axios.get(`${API_URL}/portfolio/holdings`);
        return response.data;
    },

    // Get Limits (Funds)
    getLimits: async (): Promise<Limits> => {
        const response = await axios.post(`${API_URL}/portfolio/limits`);
        return response.data;
    }
};
