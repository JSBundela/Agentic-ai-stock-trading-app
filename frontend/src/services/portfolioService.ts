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
    // CRITICAL: Normalizes Kotak API PascalCase → camelCase for UI consistency
    getLimits: async (): Promise<Limits> => {
        const response = await axios.post(`${API_URL}/portfolio/limits`);
        const raw = response.data;

        // LOG: Raw API response for debugging
        console.log('[LIMITS API] Raw Kotak Response:', raw);

        // NORMALIZE: PascalCase → camelCase
        const normalized: Limits = {
            stat: raw.stat || 'Ok',
            netCash: raw.Net ?? '0',                    // Available funds
            marginUsed: raw.MarginUsed ?? '0',          // Currently used margin
            collateralValue: raw.Collateral ?? '0',     // CORRECTED: Use Collateral (pledged shares) not CollateralValue
            notionalCash: raw.NotionalCash ?? '0',      // Total cash (may be 0)
            category: raw.Category
        };

        // LOG: Normalized data sent to UI
        console.log('[LIMITS API] Normalized for UI:', normalized);
        console.log('[LIMITS API] Field Mapping:', {
            'API.Net → UI.netCash': `${raw.Net} → ${normalized.netCash}`,
            'API.MarginUsed → UI.marginUsed': `${raw.MarginUsed} → ${normalized.marginUsed}`,
            'API.Collateral → UI.collateralValue': `${raw.Collateral} → ${normalized.collateralValue}`,
            'Note': 'Using Collateral (pledged shares) NOT CollateralValue (includes cash)'
        });

        return normalized;
    }
};
