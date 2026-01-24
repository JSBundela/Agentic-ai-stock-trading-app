import apiClient from '../api/client';

export interface Quote {
    instrumentToken: string;
    tradingSymbol: string;
    companyName?: string;
    lastPrice: number; // ltp
    change: number;
    pChange: number; // percent change
    open: number;
    high: number;
    low: number;
    close: number;
    vtt: number; // volume
    time: string;
}

export const marketService = {
    /**
     * Get snapshot quotes for instruments or indices
     * @param tokens Format: "exchange_segment|token" or "exchange_segment|IndexName"
     * Example: ["nse_cm|22", "nse_cm|Nifty 50"]
     */
    getQuotes: async (tokens: string[]): Promise<any> => {
        const response = await apiClient.post('/market/quotes', {
            instrument_tokens: tokens
        });
        return response.data;
    }
};
