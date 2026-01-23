import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { scripService } from '../services/scripService';
import { wsService } from '../services/websocket';
import { ChartContainer } from '../components/ChartContainer';
import { MarketDepth } from '../components/trading/MarketDepth';
import { OrderForm } from '../components/trading/OrderForm';
import { formatCurrency } from '../utils/formatters';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import {
    Activity,
    ArrowLeft,
    TrendingUp,
    TrendingDown,
    Zap,
    Clock,
    Target
} from 'lucide-react';

const InstrumentPage: React.FC = () => {
    const { symbol } = useParams<{ symbol: string }>();
    const navigate = useNavigate();
    const [scrip, setScrip] = useState<any>(null);
    const [quotes, setQuotes] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!symbol) return;

        const fetchData = async () => {
            try {
                const searchRes = await scripService.search(symbol);
                const foundScrip = searchRes.data?.find((s: any) => s.tradingSymbol === symbol);
                setScrip(foundScrip);
            } catch (error) {
                console.error('Failed to load instrument', error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();

        const unsubscribe = wsService.subscribeQuotes(symbol, (data) => {
            setQuotes((prev: any) => ({ ...prev, ...data }));
        });

        return () => unsubscribe();
    }, [symbol]);

    if (loading) return (
        <div className="h-[80vh] flex flex-col items-center justify-center space-y-6">
            <Activity size={48} className="text-brand animate-spin" />
            <p className="text-[10px] text-gray-600 font-bold uppercase tracking-[0.4em]">Initializing Core Sync</p>
        </div>
    );

    const priceChange = parseFloat(quotes?.change || '0');
    const isUp = priceChange >= 0;

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-6 duration-700">
            {/* Cinematic Header HUD */}
            <div className="flex flex-col xl:flex-row justify-between items-start xl:items-end gap-6 bg-obsidian-900/50 p-8 rounded-3xl border border-white/5 shadow-2xl backdrop-blur-3xl relative overflow-hidden">
                <div className="absolute top-0 left-0 w-1 h-full bg-brand" />
                <div className="absolute top-0 right-0 w-[300px] h-full bg-brand/5 blur-[80px] pointer-events-none" />

                <div className="space-y-4 relative z-10">
                    <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="text-[10px] pl-0 hover:bg-transparent hover:translate-x-1 transition-all">
                        <ArrowLeft size={14} className="mr-2" /> RETURN TO RADAR
                    </Button>
                    <div className="flex items-center gap-6">
                        <div className="p-4 bg-obsidian-800 rounded-2xl border border-glass-border shadow-inner">
                            <Target size={32} className="text-brand" />
                        </div>
                        <div>
                            <div className="flex items-center gap-3 mb-1">
                                <h1 className="text-4xl font-display font-black text-white tracking-tighter uppercase">{symbol}</h1>
                                <div className="px-2 py-0.5 rounded-lg bg-brand/10 border border-brand/20 text-[9px] font-black text-brand tracking-widest uppercase">
                                    {scrip?.exchangeSegment}
                                </div>
                            </div>
                            <p className="text-[10px] text-gray-500 font-bold uppercase tracking-[0.25em]">{scrip?.companyName || scrip?.description}</p>
                        </div>
                    </div>
                </div>

                <div className="flex flex-wrap gap-10 items-end relative z-10">
                    <div className="space-y-1 text-right">
                        <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest">Market Status</p>
                        <div className="flex items-center justify-end gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-trading-profit animate-pulse" />
                            <span className="text-xs font-mono font-black text-trading-profit">LIVE</span>
                        </div>
                    </div>
                    <div className="space-y-px text-right">
                        <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest">Current Price</p>
                        <p className={`text-4xl font-mono font-black tracking-tighter ${isUp ? 'text-trading-profit neon-glow-profit' : 'text-trading-loss neon-glow-loss'}`}>
                            {formatCurrency(quotes?.ltp)}
                        </p>
                        <div className={`flex items-center justify-end gap-2 text-[11px] font-bold ${isUp ? 'text-trading-profit' : 'text-trading-loss'}`}>
                            {isUp ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                            {quotes?.change || '0.00'} ({quotes?.pchange || '0.00'}%)
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
                {/* Visual Analysis Main Component */}
                <div className="xl:col-span-8 space-y-8">
                    <Card noPadding title="Technical Core Projection" className="border-white/5 overflow-hidden shadow-2xl bg-black/40">
                        <div className="h-[700px]">
                            <ChartContainer symbol={symbol!} height={700} />
                        </div>
                    </Card>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <Card title="Order Book Dynamics" className="border-white/5">
                            <MarketDepth
                                bids={quotes?.depth?.buy || []}
                                asks={quotes?.depth?.sell || []}
                            />
                        </Card>

                        <Card title="Intraday Metrics" className="border-white/5">
                            <div className="space-y-6 pt-2">
                                {[
                                    { label: 'Open', value: quotes?.open, icon: Clock },
                                    { label: 'High', value: quotes?.high, icon: TrendingUp },
                                    { label: 'Low', value: quotes?.low, icon: TrendingDown },
                                    { label: 'Volume', value: quotes?.vtt, icon: Activity }
                                ].map((m, i) => (
                                    <div key={i} className="flex justify-between items-center group/metric">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 rounded-lg bg-white/[0.02] text-gray-600 group-hover/metric:text-brand transition-colors">
                                                <m.icon size={14} />
                                            </div>
                                            <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">{m.label}</span>
                                        </div>
                                        <span className="text-sm font-mono font-black text-white tracking-tighter">{m.value || '--'}</span>
                                    </div>
                                ))}
                            </div>
                        </Card>
                    </div>
                </div>

                {/* Execution Cockpit */}
                <div className="xl:col-span-4 space-y-8">
                    <OrderForm
                        symbol={symbol!}
                        onOrderPlaced={() => navigate('/order-book')}
                    />

                    <Card title="Contract Intelligence" className="border-white/5">
                        <div className="space-y-4">
                            <div className="p-4 bg-obsidian-900 border border-white/[0.03] rounded-2xl flex items-center gap-4">
                                <div className="w-10 h-10 rounded-xl bg-brand/10 border border-brand/20 flex items-center justify-center text-brand">
                                    <Zap size={20} />
                                </div>
                                <div>
                                    <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest">Router Channel</p>
                                    <p className="text-xs font-display font-black text-white">LOW LATENCY ALPHA</p>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="p-4 bg-white/[0.01] border border-white/[0.03] rounded-2xl">
                                    <p className="text-[9px] text-gray-600 font-bold uppercase tracking-widest mb-1">Tick Size</p>
                                    <p className="text-sm font-mono font-black text-white">0.05</p>
                                </div>
                                <div className="p-4 bg-white/[0.01] border border-white/[0.03] rounded-2xl">
                                    <p className="text-[9px] text-gray-600 font-bold uppercase tracking-widest mb-1">Lot Size</p>
                                    <p className="text-sm font-mono font-black text-white">{scrip?.lotSize || 1}</p>
                                </div>
                            </div>
                        </div>
                    </Card>

                    <div className="p-8 bg-gradient-to-br from-obsidian-900 to-obsidian-950 border border-brand/20 rounded-3xl shadow-[0_0_50px_rgba(99,102,241,0.1)] relative overflow-hidden group">
                        <div className="relative z-10 flex flex-col items-center text-center space-y-4">
                            <div className="w-12 h-12 rounded-full bg-brand/20 border border-brand/50 flex items-center justify-center text-brand animate-pulse">
                                <Activity size={24} />
                            </div>
                            <div>
                                <h4 className="text-white font-display font-black text-lg tracking-tight">ALGO SIGNAL ACTIVE</h4>
                                <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest mt-1">Institutional Flow Detected</p>
                            </div>
                            <Button variant="glass" size="sm" className="w-full border-brand/30 hover:bg-brand/10">ENABLE AUTOPILOT</Button>
                        </div>
                        <div className="absolute top-[-20px] left-[-20px] w-40 h-40 bg-brand/10 blur-[60px] rounded-full pointer-events-none group-hover:scale-150 transition-transform duration-1000" />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default InstrumentPage;
