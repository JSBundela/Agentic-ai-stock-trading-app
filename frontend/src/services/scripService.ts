import apiClient from '../api/client';

export interface Scrip {
    tradingSymbol: string;
    instrumentToken: string;
    exchangeSegment: string;
    [key: string]: any;
}

export const scripService = {
    search: async (query: string): Promise<{ data: Scrip[] }> => {
        const response = await apiClient.get(`/scripmaster/search?q=${encodeURIComponent(query)}`);
        return response.data;
    },
    getScrip: async (symbol: string): Promise<Scrip> => {
        const response = await apiClient.get(`/scripmaster/scrip/${symbol}`);
        return response.data;
    }
};
