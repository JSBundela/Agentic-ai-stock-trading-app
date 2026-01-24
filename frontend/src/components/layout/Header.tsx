import React, { useEffect, useState } from 'react';
import { Bell, Search, User, Zap } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { wsService } from '../../services/websocket';
import { formatCurrency } from '../../utils/formatters';

export const Header: React.FC = () => {
    const { user } = useAuth();
    const [indices, setIndices] = useState({
        nifty: { price: 0, change: 0, pChange: 0 },
        sensex: { price: 0, change: 0, pChange: 0 }
    });

    useEffect(() => {
        let unsubNifty: (() => void) | undefined;
        let unsubSensex: (() => void) | undefined;

        const connectAndSubscribe = async () => {
            try {
                // Fetch live indices using new MCP-based endpoint
                const response = await fetch('http://localhost:8000/market/indices/live');
                const result = await response.json();

                console.log('[HEADER] Live Index Data:', result);

                if (result.success && result.data) {
                    // Update NIFTY 50
                    const niftyData = result.data.NIFTY_50;
                    if (niftyData && !niftyData.error) {
                        setIndices(prev => ({
                            ...prev,
                            nifty: {
                                price: niftyData.ltp || 0,
                                change: niftyData.change || 0,
                                pChange: niftyData.percent_change || 0
                            }
                        }));

                        // Subscribe to WebSocket for live updates
                        const wsToken = 'nse_cm|Nifty 50';
                        console.log(`[HEADER] Subscribing WS Nifty: ${wsToken}`);
                        unsubNifty = wsService.subscribeQuotes(wsToken, (tick) => {
                            setIndices(prev => ({
                                ...prev,
                                nifty: {
                                    price: tick.ltp,
                                    change: tick.change || prev.nifty.change,
                                    pChange: tick.per_change || prev.nifty.pChange
                                }
                            }));
                        });
                    } else {
                        console.warn('[HEADER] NIFTY data unavailable:', niftyData?.error);
                    }

                    // Update SENSEX
                    const sensexData = result.data.SENSEX;
                    if (sensexData && !sensexData.error) {
                        setIndices(prev => ({
                            ...prev,
                            sensex: {
                                price: sensexData.ltp || 0,
                                change: sensexData.change || 0,
                                pChange: sensexData.percent_change || 0
                            }
                        }));

                        // Subscribe to WebSocket for live updates
                        const wsToken = 'bse_cm|SENSEX';
                        console.log(`[HEADER] Subscribing WS Sensex: ${wsToken}`);
                        unsubSensex = wsService.subscribeQuotes(wsToken, (tick) => {
                            setIndices(prev => ({
                                ...prev,
                                sensex: {
                                    price: tick.ltp,
                                    change: tick.change || prev.sensex.change,
                                    pChange: tick.per_change || prev.sensex.pChange
                                }
                            }));
                        });
                    } else {
                        console.warn('[HEADER] SENSEX data unavailable:', sensexData?.error);
                    }
                } else {
                    console.error('[HEADER] Live indices endpoint failed:', result.error);
                }
            } catch (error) {
                console.error('[HEADER] Failed to fetch live indices:', error);
            }
        };

        connectAndSubscribe();

        return () => {
            if (unsubNifty) unsubNifty();
            if (unsubSensex) unsubSensex();
        };
    }, []);

    const renderChange = (change: number, pChange: number) => {
        const isPositive = change >= 0;
        const colorClass = isPositive ? 'text-trading-profit neon-glow-profit' : 'text-trading-loss neon-glow-loss';
        return (
            <span className={`text-[10px] font-bold ${colorClass}`}>
                {isPositive ? '+' : ''}{pChange.toFixed(2)}%
            </span>
        );
    };

    return (
        <header className="h-20 bg-obsidian-900/30 backdrop-blur-xl border-b border-glass-border flex items-center justify-between px-8 z-20">
            <div className="flex items-center gap-8 flex-1">
                {/* Global Market Ticker */}
                <div className="relative max-w-md w-full group">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-brand transition-colors" size={16} />
                    <input
                        type="text"
                        placeholder="Search Instruments (e.g. NIFTY, RELIANCE...)"
                        className="w-full bg-glass-surface border border-glass-border rounded-2xl py-2.5 pl-12 pr-4 text-xs font-bold font-display outline-none focus:border-brand/50 focus:bg-white/[0.04] transition-all placeholder:text-gray-600"
                    />
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 flex gap-1">
                        <kbd className="px-1.5 py-0.5 rounded-md bg-white/5 border border-white/10 text-[9px] font-mono text-gray-500">⌘</kbd>
                        <kbd className="px-1.5 py-0.5 rounded-md bg-white/5 border border-white/10 text-[9px] font-mono text-gray-500">K</kbd>
                    </div>
                </div>

                <div className="hidden lg:flex items-center gap-6">
                    <div className="flex flex-col">
                        <span className="text-[9px] text-gray-500 font-bold uppercase tracking-[0.2em] mb-0.5">NIFTY 50</span>
                        <div className="flex items-center gap-2">
                            <span className="text-sm font-mono font-black text-white">{formatCurrency(indices.nifty.price)}</span>
                            {renderChange(indices.nifty.change, indices.nifty.pChange)}
                        </div>
                    </div>
                    <div className="w-px h-8 bg-glass-border" />
                    <div className="flex flex-col">
                        <span className="text-[9px] text-gray-500 font-bold uppercase tracking-[0.2em] mb-0.5">SENSEX</span>
                        <div className="flex items-center gap-2">
                            <span className="text-sm font-mono font-black text-white">{formatCurrency(indices.sensex.price)}</span>
                            {renderChange(indices.sensex.change, indices.sensex.pChange)}
                        </div>
                    </div>
                </div>
            </div>

            <div className="flex items-center gap-6">
                <button className="relative p-2.5 bg-glass-surface border border-glass-border rounded-xl text-gray-400 hover:text-white transition-all hover:bg-glass-hover">
                    <Bell size={20} />
                    <span className="absolute top-2 right-2 w-2 h-2 bg-brand rounded-full border-2 border-obsidian-950 shadow-[0_0_8px_#6366F1]" />
                </button>

                <div className="flex items-center gap-4 pl-6 border-l border-glass-border">
                    <div className="text-right hidden sm:block">
                        <p className="text-xs font-display font-black text-white uppercase tracking-tight">
                            {user?.name || 'Guest User'}
                        </p>
                        <p className="text-[9px] text-brand font-bold uppercase tracking-widest flex items-center justify-end gap-1">
                            <Zap size={8} className="fill-brand" /> {user ? 'PRO ACCOUNT' : 'GUEST ACCESS'}
                        </p>
                    </div>
                    <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-brand to-indigo-800 flex items-center justify-center border border-white/20 shadow-lg shadow-brand/20">
                        <User size={20} className="text-white" />
                    </div>
                </div>
            </div>
        </header>
    );
};
