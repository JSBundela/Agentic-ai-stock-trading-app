import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import OrderEntry from './pages/OrderEntry';
import OrderBook from './pages/OrderBook';
import PortfolioPage from './pages/PortfolioPage';
import InstrumentPage from './pages/InstrumentPage';

import { AppShell } from './components/layout/AppShell';

// Component that consumes AuthContext must be a child of AuthProvider
const AppRoutes: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-surface-primary flex items-center justify-center text-gray-500">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-brand"></div>
          <span className="text-sm font-medium tracking-widest uppercase">Initializing Session...</span>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route
        path="/"
        element={
          isAuthenticated ? <Navigate to="/dashboard" replace /> : <LoginPage />
        }
      />
      <Route
        path="/dashboard"
        element={
          isAuthenticated ? <AppShell><Dashboard /></AppShell> : <Navigate to="/" replace />
        }
      />
      <Route
        path="/order-entry"
        element={
          isAuthenticated ? <AppShell><OrderEntry /></AppShell> : <Navigate to="/" replace />
        }
      />
      <Route
        path="/order-book"
        element={
          isAuthenticated ? <AppShell><OrderBook /></AppShell> : <Navigate to="/" replace />
        }
      />
      <Route
        path="/portfolio"
        element={
          isAuthenticated ? <AppShell><PortfolioPage /></AppShell> : <Navigate to="/" replace />
        }
      />
      <Route
        path="/instrument/:symbol"
        element={
          isAuthenticated ? <AppShell><InstrumentPage /></AppShell> : <Navigate to="/" replace />
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
