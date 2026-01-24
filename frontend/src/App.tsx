import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AppShell } from './components/layout/AppShell';

// Lazy load page components
const LoginPage = React.lazy(() => import('./pages/LoginPage'));
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const OrderEntry = React.lazy(() => import('./pages/OrderEntry'));
const OrderBook = React.lazy(() => import('./pages/OrderBook'));
const PortfolioPage = React.lazy(() => import('./pages/PortfolioPage'));
const FundsPage = React.lazy(() => import('./pages/FundsPage'));
const InstrumentPage = React.lazy(() => import('./pages/InstrumentPage'));

const LoadingScreen = ({ message = 'Loading...' }: { message?: string }) => (
  <div className="min-h-screen bg-surface-primary flex items-center justify-center text-gray-500">
    <div className="flex flex-col items-center gap-4">
      <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-brand"></div>
      <span className="text-sm font-medium tracking-widest uppercase">{message}</span>
    </div>
  </div>
);

// Component that consumes AuthContext must be a child of AuthProvider
const AppRoutes: React.FC = () => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <LoadingScreen message="Initializing Session..." />;
  }

  return (
    <Suspense fallback={<LoadingScreen />}>
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
          path="/funds"
          element={
            isAuthenticated ? <AppShell><FundsPage /></AppShell> : <Navigate to="/" replace />
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
    </Suspense>
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
