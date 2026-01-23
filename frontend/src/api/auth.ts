import apiClient from './client';
import type { LoginRequest, MPINRequest, TokenResponse } from '../types/api';

/**
 * Authentication APIs
 * Uses verified backend endpoints - NO MODIFICATIONS
 */

export const authAPI = {
    /**
     * POST /auth/totp-login
     * Authenticate with TOTP
     */
    totpLogin: async (data: LoginRequest): Promise<TokenResponse> => {
        const response = await apiClient.post<TokenResponse>('/auth/totp-login', data);
        return response.data;
    },

    /**
     * POST /auth/validate-mpin
     * Validate MPIN and complete authentication
     */
    validateMPIN: async (data: MPINRequest): Promise<TokenResponse> => {
        const response = await apiClient.post<TokenResponse>('/auth/validate-mpin', data);
        return response.data;
    },
};
