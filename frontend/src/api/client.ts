import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const apiClient = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 60000, // 60 seconds resilience
});

// Request interceptor for logging and auth
apiClient.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        const sid = localStorage.getItem('sid');

        if (token) {
            config.headers['Auth'] = token;
        }
        if (sid) {
            config.headers['sid'] = sid;
        }

        console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
        return config;
    },
    (error) => {
        console.error('[API] Request error:', error);
        return Promise.reject(error);
    }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
    (response) => {
        console.log(`[API] Response from ${response.config.url}:`, response.status);
        return response;
    },
    (error) => {
        if (error.response) {
            console.error('[API] Error response:', error.response.status, error.response.data);

            // Handle session expiration or backend restart
            if (error.response.status === 401) {
                console.warn('Session expired or not authenticated. Redirecting to login.');
                localStorage.clear();
                // Avoid infinite redirect loop if already on login page
                if (window.location.pathname !== '/') {
                    window.location.href = '/';
                }
            }
        } else if (error.request) {
            console.error('[API] No response received:', error.request);
        } else {
            console.error('[API] Error:', error.message);
        }
        return Promise.reject(error);
    }
);

export default apiClient;
