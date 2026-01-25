import React, { createContext, useContext, useState, useEffect } from 'react';
import { wsService } from '../services/websocket';

// Define types for User and Auth Context
interface User {
    id: string; // UCC or similar
    name?: string;
}

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    login: (token: string, sid?: string) => void;
    logout: () => void;
    loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
    const [loading, setLoading] = useState<boolean>(true);

    useEffect(() => {
        // Check for existing session on mount
        const token = localStorage.getItem('access_token');
        const authFlag = localStorage.getItem('isAuthenticated');

        if (token && authFlag === 'true') {
            setUser({ id: 'User', name: 'M. S. Bundela' }); // Simplified for V3
            setIsAuthenticated(true);
        }
        setLoading(false);
    }, []);

    // Manage WebSocket connection lifecycle
    useEffect(() => {
        if (isAuthenticated) {
            console.log('🔄 Auth detected. Initializing Real-time WebSocket...');
            wsService.connect().catch(err => console.error('WS Auto-connect failed:', err));
        } else {
            wsService.disconnect();
        }
    }, [isAuthenticated]);

    const login = (token: string, sid?: string) => {
        localStorage.setItem('access_token', token);
        if (sid) localStorage.setItem('sid', sid);
        localStorage.setItem('isAuthenticated', 'true');
        setUser({ id: 'User', name: 'M. S. Bundela' });
        setIsAuthenticated(true);
    };

    const logout = () => {
        wsService.disconnect();
        localStorage.removeItem('access_token');
        localStorage.removeItem('sid');
        localStorage.removeItem('isAuthenticated');
        localStorage.removeItem('baseUrl');
        setUser(null);
        setIsAuthenticated(false);
        window.location.href = '/';
    };

    return (
        <AuthContext.Provider value={{ user, isAuthenticated, login, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};

// Custom hook for consuming auth context
export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
