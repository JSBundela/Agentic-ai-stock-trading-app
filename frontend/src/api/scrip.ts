import apiClient from './client';

export const scripAPI = {
    search: async (q: string) => {
        const response = await apiClient.get(`/scripmaster/search?q=${encodeURIComponent(q)}`);
        return response.data;
    },
    getScrip: async (symbol: string) => {
        const response = await apiClient.get(`/scripmaster/scrip/${symbol}`);
        return response.data;
    }
};
