// User preferences stored in localStorage
export interface UserPreferences {
    defaultOrderType: 'LIMIT' | 'MARKET';
    defaultProduct: string; // CNC, MIS, NRML
    defaultQuantity: number;
    autoRefreshOrders: boolean;
    refreshInterval: number; // seconds
}

const DEFAULT_PREFERENCES: UserPreferences = {
    defaultOrderType: 'LIMIT',
    defaultProduct: 'CNC',
    defaultQuantity: 1,
    autoRefreshOrders: true,
    refreshInterval: 10
};

const STORAGE_KEY = 'kotak_user_preferences';

export const getPreferences = (): UserPreferences => {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            return { ...DEFAULT_PREFERENCES, ...JSON.parse(stored) };
        }
    } catch (error) {
        console.error('Failed to load preferences:', error);
    }
    return DEFAULT_PREFERENCES;
};

export const savePreferences = (preferences: Partial<UserPreferences>): void => {
    try {
        const current = getPreferences();
        const updated = { ...current, ...preferences };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    } catch (error) {
        console.error('Failed to save preferences:', error);
    }
};

export const resetPreferences = (): void => {
    try {
        localStorage.removeItem(STORAGE_KEY);
    } catch (error) {
        console.error('Failed to reset preferences:', error);
    }
};
