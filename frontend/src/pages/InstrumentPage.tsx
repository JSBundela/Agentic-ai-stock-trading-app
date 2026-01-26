import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { scripService } from '../services/scripService';
import { wsService } from '../services/websocket';
import { marketService } from '../services/marketService';

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
                console.log(`[DEBUG] Searching for scrip: ${symbol}`);
                const searchRes = await scripService.search(symbol);
                console.log(`[DEBUG] Search results for ${symbol}:`, searchRes);

                const foundScrip = searchRes.data?.find((s: any) => s.tradingSymbol === symbol);

                if (foundScrip) {
                    console.log(`[DEBUG] Found scrip match:`, foundScrip);
                    setScrip(foundScrip);
                } else {
                    console.warn(`[DEBUG] No exact scrip match for ${symbol}`);
                }
            } catch (error) {
                console.error('Failed to load instrument', error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        return () => {
            // Cleanup if needed
        };
    }, [symbol]);

    // Separate effect for Quote Subscription + Snapshot
    useEffect(() => {
        if (!symbol || !scrip) return;

        // 1. Fetch Snapshot (for Market Closed / Initial State)
        const fetchSnapshot = async () => {
            try {
                const token = `${scrip.exchangeSegment}|${scrip.instrumentToken}`;
                console.log(`[DEBUG] Fetching snapshot for token: ${token}`);

                const quotesData = await marketService.getQuotes([token]);
                console.log(`[DEBUG] Snapshot response:`, quotesData);

                if (quotesData && quotesData.length > 0) {
                    const quote = quotesData[0];
                    if (quote.error) {
                        console.warn(`[DEBUG] Snapshot API returned error:`, quote.error);
                        return;
                    }

                    console.log(`[DEBUG] Setting quotes state from snapshot:`, quote);
                    setQuotes((prev: any) => ({

                        ...prev,
                        ltp: parseFloat(quote.ltp || quote.lastPrice || 0),
                        change: parseFloat(quote.chn || quote.change || 0),
                        pchange: parseFloat(quote.pc || quote.pChange || quote.per_change || 0),
                        open: parseFloat(quote.ohlc?.open || quote.open || 0),
                        high: parseFloat(quote.ohlc?.high || quote.high || 0),
                        low: parseFloat(quote.ohlc?.low || quote.low || 0),
                        vtt: parseFloat(quote.vtt || quote.volume || quote.last_volume || 0)
                    }));
                } else {
                    console.warn(`[DEBUG] Snapshot response empty or invalid`);
                }
            } catch (error) {
                console.error('Snapshot fetch error:', error);
            }
        };

        fetchSnapshot();

        // 2. Subscribe to Live Ticks
        const unsubscribe = wsService.subscribeQuotes(symbol, (data) => {
            setQuotes((prev: any) => ({ ...prev, ...data }));
        });

        return () => unsubscribe();
    }, [symbol, scrip]);

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
                            <div className="flex items-center gap-3 mb-2">
                                <h1 className="text-4xl font-display font-black text-white tracking-tight">{scrip?.description || scrip?.companyName || symbol}</h1>
                                <div className="px-2 py-0.5 rounded-lg bg-brand/10 border border-brand/20 text-[9px] font-black text-brand tracking-widest uppercase">
                                    {scrip?.exchangeSegment}
                                </div>
                            </div>
                            <p className="text-xs text-gray-500 font-mono tracking-wider">{symbol}</p>
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
                        initialLtp={quotes?.ltp}
                    />


                </div>
            </div>
        </div>
    );
};

export default InstrumentPage;
