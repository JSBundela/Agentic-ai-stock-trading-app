import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChartContainer } from '../components/ChartContainer';
import { OrderForm } from '../components/trading/OrderForm';
import { scripService } from '../services/scripService';
import type { Scrip } from '../services/scripService';
import { Search, Loader2, ArrowRight, TrendingUp, Activity, Zap } from 'lucide-react';
import { parseSymbol } from '../utils/symbolDecoder';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

const OrderEntry: React.FC = () => {
    const navigate = useNavigate();
    const [searchTerm, setSearchTerm] = useState('');
    const [debouncedSearch, setDebouncedSearch] = useState('');
    const [results, setResults] = useState<Scrip[]>([]);
    const [loading, setLoading] = useState(false);
    const [selectedScrip, setSelectedScrip] = useState<Scrip | null>(null);

    // Debounce search term (400ms delay)
    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedSearch(searchTerm);
        }, 400);
        return () => clearTimeout(timer);
    }, [searchTerm]);

    // Trigger search when debounced value changes
    useEffect(() => {
        const performSearch = async () => {
            if (!debouncedSearch.trim()) {
                setResults([]);
                return;
            }

            setLoading(true);
            try {
                const response = await scripService.search(debouncedSearch);
                setResults(response.data || []);
            } catch (error) {
                console.error('Search failed', error);
            } finally {
                setLoading(false);
            }
        };

        performSearch();
    }, [debouncedSearch]);

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        // Search already handled by debounce, but keep form submit for UX
    };

    const handleSelect = (scrip: Scrip) => {
        setSelectedScrip(scrip);
        setResults([]);
        setSearchTerm('');
    };

    return (
        <div className="space-y-8 animate-in fade-in zoom-in-95 duration-500">
            {/* Search HUD */}
            <div className="flex flex-col md:flex-row gap-6 items-start">
                <div className="flex-1 w-full relative group">
                    <form onSubmit={handleSearch} className="relative z-20">
                        <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-brand transition-colors" size={20} />
                        <input
                            type="text"
                            placeholder="FIND INSTRUMENT (e.g. RELIANCE, NIFTY 23500 CE...)"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full bg-obsidian-900 border border-white/[0.05] rounded-3xl py-5 pl-16 pr-6 text-sm font-display font-bold text-white outline-none focus:border-brand/50 focus:ring-4 focus:ring-brand/5 placeholder:text-gray-700 transition-all backdrop-blur-3xl"
                        />
                        {loading && <Loader2 className="absolute right-6 top-1/2 -translate-y-1/2 animate-spin text-brand" size={20} />}
                    </form>

                    {/* Results Dropdown */}
                    {results.length > 0 && (
                        <div className="absolute top-full mt-4 left-0 right-0 glass-card z-50 p-2 overflow-hidden shadow-[0_30px_100px_rgba(0,0,0,0.8)] border-white/5 animate-in slide-in-from-top-2">
                            <div className="max-h-[400px] overflow-y-auto custom-scrollbar divide-y divide-white/[0.03]">
                                {results.map((scrip) => {
                                    parseSymbol(scrip.tradingSymbol, scrip);
                                    return (
                                        <button
                                            key={scrip.instrumentToken}
                                            onClick={() => handleSelect(scrip)}
                                            className="w-full text-left p-5 hover:bg-brand/5 transition-colors flex justify-between items-center group/item"
                                        >
                                            <div className="flex items-center gap-4">
                                                <div className="w-12 h-12 rounded-2xl bg-obsidian-800 border border-white/5 flex items-center justify-center text-gray-500 group-hover/item:border-brand/30 group-hover/item:text-brand transition-all">
                                                    <TrendingUp size={20} />
                                                </div>
                                                <div>
                                                    <span className="block text-base font-display font-black text-white tracking-tight group-hover/item:text-brand transition-colors">{scrip.description || scrip.companyName || scrip.tradingSymbol}</span>
                                                    <span className="block text-[10px] text-gray-500 font-mono tracking-wider mt-1">{scrip.tradingSymbol}</span>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-4">
                                                <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">{scrip.exchangeSegment}</span>
                                                <ArrowRight size={16} className="text-gray-700 group-hover:text-brand group-hover:translate-x-1 transition-all" />
                                            </div>
                                        </button>
                                    );
                                })}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                {/* Visual Intelligence Center */}
                <div className="lg:col-span-8 space-y-8">
                    {selectedScrip ? (
                        <Card noPadding title={`Analysis Center: ${selectedScrip.tradingSymbol}`} className="border-white/5 overflow-hidden">
                            <div className="bg-obsidian-900/50 border-b border-white/[0.03] p-6 flex justify-between items-center">
                                <div className="flex gap-10">
                                    <div className="space-y-1">
                                        <p className="text-[9px] text-gray-600 font-bold uppercase tracking-widest">Exchange</p>
                                        <p className="text-xs font-bold text-brand uppercase">{selectedScrip.exchangeSegment}</p>
                                    </div>
                                    <div className="space-y-1">
                                        <p className="text-[9px] text-gray-600 font-bold uppercase tracking-widest">Category</p>
                                        <p className="text-xs font-bold text-white uppercase">{selectedScrip.instrumentType || 'EQUITY'}</p>
                                    </div>
                                    <div className="space-y-1">
                                        <p className="text-[9px] text-gray-600 font-bold uppercase tracking-widest">Tick Size</p>
                                        <p className="text-xs font-mono font-bold text-white">0.05</p>
                                    </div>
                                </div>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => navigate(`/instrument/${encodeURIComponent(selectedScrip.tradingSymbol)}`)}
                                    className="text-[9px]"
                                >
                                    View Full Depth <ArrowRight size={12} className="ml-2" />
                                </Button>
                            </div>
                            <div className="h-[650px] bg-black/20">
                                <ChartContainer symbol={selectedScrip.tradingSymbol} height={650} />
                            </div>
                        </Card>
                    ) : (
                        <div className="h-[750px] glass-card flex flex-col items-center justify-center p-20 text-center border-dashed border-white/5">
                            <div className="w-24 h-24 rounded-3xl bg-obsidian-900 border border-white/5 flex items-center justify-center text-gray-700 mb-8 animate-pulse shadow-2xl">
                                <Activity size={48} />
                            </div>
                            <h2 className="text-3xl font-display font-black text-white tracking-tighter mb-4">AWAITING INSTRUMENT</h2>
                            <p className="text-gray-500 text-sm max-w-sm font-medium leading-relaxed uppercase tracking-wider">
                                Use the global radar above to locate any tradable asset across NSE and BSE markets.
                            </p>
                        </div>
                    )}
                </div>

                {/* Execution Cockpit Sidebar */}
                <div className="lg:col-span-4">
                    {selectedScrip ? (
                        <OrderForm
                            symbol={selectedScrip.tradingSymbol}
                            onOrderPlaced={() => navigate('/order-book')}
                        />
                    ) : (
                        <div className="glass-card p-10 border-dashed border-white/5 text-center space-y-6">
                            <div className="w-16 h-16 rounded-2xl bg-obsidian-900 border border-white/5 flex items-center justify-center text-gray-800 mx-auto">
                                <Zap size={32} />
                            </div>
                            <p className="text-[10px] text-gray-600 font-bold uppercase tracking-[0.3em]">Cockpit Offline</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default OrderEntry;
