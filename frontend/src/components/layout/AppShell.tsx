import React from 'react';
import { useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { AgentChat } from '../agent/AgentChat';

interface AppShellProps {
    children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
    const location = useLocation();

    return (
        <div className="flex h-screen bg-obsidian-950 overflow-hidden relative font-sans selection:bg-brand/30 selection:text-white">
            {/* Global Ambient Background Effects */}
            <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-brand/5 blur-[150px] rounded-full pointer-events-none animate-pulse-slow" />
            <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-trading-profit/5 blur-[150px] rounded-full pointer-events-none animate-pulse-slow" />

            {/* V3 Scanline Overlay - Industrial HUD feel */}
            <div className="absolute inset-0 pointer-events-none opacity-[0.03] z-50 overflow-hidden">
                <div className="w-full h-[2px] bg-white animate-scanline" />
            </div>

            <Sidebar />

            <div className="flex-1 flex flex-col min-w-0 relative">
                <Header />
                <main className="flex-1 overflow-y-auto p-8 custom-scrollbar relative z-10">
                    <div className="max-w-7xl mx-auto">
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={location.pathname}
                                initial={{ opacity: 0, y: 10, scale: 0.99 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0, y: -10, scale: 1.01 }}
                                transition={{
                                    duration: 0.3,
                                    ease: [0.22, 1, 0.36, 1],
                                    opacity: { duration: 0.2 }
                                }}
                            >
                                {children}
                            </motion.div>
                        </AnimatePresence>
                    </div>
                </main>
            </div>

            <AgentChat />
        </div >
    );
};
