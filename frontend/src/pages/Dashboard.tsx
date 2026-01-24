import React from 'react';
import { motion } from 'framer-motion';
import { Card } from '../components/ui/Card';
import { StatCard } from '../components/ui/StatCard';
import { Button } from '../components/ui/Button';
import { Table, TableRow, TableCell } from '../components/ui/Table';
import { Badge } from '../components/ui/Badge';
// import { portfolioService } from '../services/portfolioService'; // Removed
// import { orderService } from '../services/orderService'; // Removed
import { useDashboardData } from '../hooks/useDashboardData';
import { formatCurrency } from '../utils/formatters';
import { Activity, ArrowUpRight, ShieldCheck, Zap, Layers } from 'lucide-react';
import { Link } from 'react-router-dom';
import { marketService } from '../services/marketService';
import { wsService } from '../services/websocket';
import { parseSymbol } from '../utils/symbolDecoder';

const containerVariants: any = {
    hidden: { opacity: 0 },
    show: {
        opacity: 1,
        transition: {
            staggerChildren: 0.1
        }
    }
};

const itemVariants: any = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" } }
};

const Dashboard: React.FC = () => {
    const { data, orders, loading } = useDashboardData();
    const [indices, setIndices] = React.useState({
        nifty: { price: 0, change: 0, pChange: 0 },
        sensex: { price: 0, change: 0, pChange: 0 }
    });

    React.useEffect(() => {
        let unsubNifty: (() => void) | undefined;
        let unsubSensex: (() => void) | undefined;

        const connectAndSubscribe = async () => {
            try {
                const tokens = ['nse_cm|Nifty 50', 'bse_cm|SENSEX'];
                const data = await marketService.getQuotes(tokens);

                if (Array.isArray(data) && data.length > 0) {
                    const niftyData = data.find((i: any) =>
                        i.exchange_token === 'Nifty 50' ||
                        i.display_symbol === 'NIFTY 50' ||
                        i.instrumentName === 'Nifty 50'
                    );
                    const sensexData = data.find((i: any) =>
                        i.exchange_token === 'SENSEX' ||
                        i.display_symbol === 'SENSEX' ||
                        i.instrumentName === 'SENSEX'
                    );

                    if (niftyData) {
                        setIndices(prev => ({
                            ...prev, nifty: {
                                price: parseFloat(niftyData.ltp),
                                change: parseFloat(niftyData.chn || niftyData.change || 0),
                                pChange: parseFloat(niftyData.pc || niftyData.pChange || 0)
                            }
                        }));

                        const tok = niftyData.instrumentToken || niftyData.exchange_token;
                        if (tok) unsubNifty = wsService.subscribeQuotes(`nse_cm|${tok}`, (tick) => {
                            setIndices(prev => ({
                                ...prev, nifty: {
                                    price: tick.ltp,
                                    change: tick.change || prev.nifty.change,
                                    pChange: tick.per_change || prev.nifty.pChange
                                }
                            }));
                        });
                    }

                    if (sensexData) {
                        setIndices(prev => ({
                            ...prev, sensex: {
                                price: parseFloat(sensexData.ltp),
                                change: parseFloat(sensexData.chn || sensexData.change || 0),
                                pChange: parseFloat(sensexData.pc || sensexData.pChange || 0)
                            }
                        }));

                        const tok = sensexData.instrumentToken || sensexData.exchange_token;
                        if (tok) unsubSensex = wsService.subscribeQuotes(`bse_cm|${tok}`, (tick) => {
                            setIndices(prev => ({
                                ...prev, sensex: {
                                    price: tick.ltp,
                                    change: tick.change || prev.sensex.change,
                                    pChange: tick.per_change || prev.sensex.pChange
                                }
                            }));
                        });
                    }
                }
            } catch (error) { console.error('Dashboard Index Error', error); }
        };

        connectAndSubscribe();
        return () => { if (unsubNifty) unsubNifty(); if (unsubSensex) unsubSensex(); };
    }, []);

    // DIAGNOSTIC LOGGING: Track data flow from API → UI
    React.useEffect(() => {
        if (data?.limits) {
            console.log('[DASHBOARD] ═══════════════════════════════════');
            console.log('[DASHBOARD] Raw data object:', data);
            console.log('[DASHBOARD] Limits object:', data.limits);
            console.log('[DASHBOARD] Data Flow Trace:', {
                'API Response (normalized)': data.limits,
                'Available Funds Field (netCash)': data.limits.netCash,
                'Used Margin Field (marginUsed)': data.limits.marginUsed,
                'Collateral Field (collateralValue)': data.limits.collateralValue,
                'Parsed Available Funds': parseFloat(data.limits.netCash),
                'Parsed Used Margin': parseFloat(data.limits.marginUsed),
                'Final Display Value (Available)': `₹${parseFloat(data.limits.netCash).toFixed(2)}`,
                'Final Display Value (Margin)': `₹${parseFloat(data.limits.marginUsed).toFixed(2)}`
            });
            console.log('[DASHBOARD] ═══════════════════════════════════');
        }
    }, [data]);

    const mtm = parseFloat(data?.positions?.totalMtm) || 0;
    const availableFunds = parseFloat(data?.limits?.netCash) || 0;

    // Calculate portfolio value from holdings (NOT from limits)
    const portfolioValue = (data?.holdings?.data || []).reduce((total: number, holding: any) => {
        const mktVal = parseFloat(holding.mktValue || holding.marketValue || 0);
        return total + mktVal;
    }, 0);

    // DEBUG: Log portfolio calculation
    React.useEffect(() => {
        console.log('[PORTFOLIO DEBUG] Holdings data:', data?.holdings);
        console.log('[PORTFOLIO DEBUG] Calculated portfolio value:', portfolioValue);
    }, [data?.holdings, portfolioValue]);

    return (
        <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="space-y-8"
        >
            {/* HUD: Primary KPI Strip */}
            <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6" {...({} as any)}>
                <StatCard
                    label="Available Funds"
                    value={formatCurrency(availableFunds)}
                    trend="neutral"
                    trendValue="Margin"
                    loading={loading}
                />
                <StatCard
                    label="Active P&L"
                    value={formatCurrency(mtm)}
                    trend={mtm >= 0 ? 'up' : 'down'}
                    trendValue={mtm >= 0 ? '+2.4%' : '-1.2%'}
                    loading={loading}
                />
                <StatCard
                    label="Margin from Shares"
                    value={formatCurrency(parseFloat(data?.limits?.collateralValue) || 0)}
                    trend="neutral"
                    trendValue="Collateral"
                    loading={loading}
                />
                <StatCard
                    label="Used Margin"
                    value={formatCurrency(parseFloat(data?.limits?.marginUsed) || 0)}
                    trend="down"
                    trendValue="Utilized"
                    loading={loading}
                />
            </motion.div>

            <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
                {/* Main Execution Monitor */}
                <motion.div variants={itemVariants} className="xl:col-span-8 space-y-8" {...({} as any)}>
                    <Card
                        title="Live Execution Monitor"
                        noPadding
                        actions={
                            <Link to="/order-book">
                                <Button variant="ghost" size="sm" className="text-[9px]">Full History</Button>
                            </Link>
                        }
                    >
                        <Table headers={['Time', 'Instrument', 'Type', 'Status', 'Price']}>
                            {orders.map((order, i) => (
                                <TableRow key={i}>
                                    <TableCell className="text-gray-500 font-mono text-[10px]">{order.ordTime || order.ordDtTm || '--:--'}</TableCell>
                                    <TableCell>
                                        <div className="flex flex-col">
                                            <span className="font-display font-black text-white tracking-tight uppercase">
                                                {parseSymbol(order.tsym || order.trdSym || '').companyName || order.tsym || order.trdSym || '--'}
                                            </span>
                                            <span className="text-[9px] text-gray-500 font-bold tracking-widest uppercase">{order.exch || order.exSeg || 'NSE'}</span>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        {(order.trnsTp || order.trantype) ? (
                                            (() => {
                                                const type = (order.trnsTp || order.trantype).toUpperCase();
                                                const normalizedType = type === 'B' ? 'BUY' : type === 'S' ? 'SELL' : type;
                                                return (
                                                    <Badge variant={normalizedType === 'BUY' ? 'success' : 'danger'}>
                                                        {normalizedType}
                                                    </Badge>
                                                );
                                            })()
                                        ) : (
                                            <span className="text-[10px] text-gray-600">-</span>
                                        )}
                                    </TableCell>
                                    <TableCell>
                                        {(order.ordSt || order.status) ? (
                                            <span className={`text-[10px] font-bold uppercase tracking-widest ${(order.ordSt || order.status) === 'complete' || (order.ordSt || order.status) === 'traded' ? 'text-trading-profit' :
                                                (order.ordSt || order.status) === 'rejected' ? 'text-trading-loss' : 'text-gray-400'
                                                }`}>
                                                {order.ordSt || order.status}
                                            </span>
                                        ) : (
                                            <span className="text-[10px] text-gray-600">-</span>
                                        )}
                                    </TableCell>
                                    <TableCell className="font-mono text-white text-right">{formatCurrency(order.prc)}</TableCell>
                                </TableRow>
                            ))}
                            {orders.length === 0 && (
                                <tr>
                                    <td colSpan={5} className="py-20 text-center">
                                        <Activity size={32} className="mx-auto text-gray-700 mb-4 animate-pulse" />
                                        <p className="text-[10px] text-gray-500 font-bold uppercase tracking-[0.3em]">Awaiting Order Flow</p>
                                    </td>
                                </tr>
                            )}
                        </Table>
                    </Card>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Live Index Cards */}
                        <Card title="NIFTY 50" className="bg-gradient-to-br from-brand/5 to-transparent">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h4 className="text-2xl font-display font-black text-white">{formatCurrency(indices.nifty.price)}</h4>
                                    <div className={`flex items-center gap-2 mt-1 ${indices.nifty.change >= 0 ? 'text-trading-profit' : 'text-trading-loss'}`}>
                                        <span className="text-xs font-bold">{indices.nifty.change >= 0 ? '+' : ''}{indices.nifty.change.toFixed(2)}</span>
                                        <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 bg-white/5 rounded">
                                            {indices.nifty.pChange.toFixed(2)}%
                                        </span>
                                    </div>
                                </div>
                                <Activity className={indices.nifty.change >= 0 ? 'text-trading-profit' : 'text-trading-loss'} size={32} />
                            </div>
                        </Card>

                        <Card title="SENSEX" className="bg-gradient-to-br from-brand/5 to-transparent">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h4 className="text-2xl font-display font-black text-white">{formatCurrency(indices.sensex.price)}</h4>
                                    <div className={`flex items-center gap-2 mt-1 ${indices.sensex.change >= 0 ? 'text-trading-profit' : 'text-trading-loss'}`}>
                                        <span className="text-xs font-bold">{indices.sensex.change >= 0 ? '+' : ''}{indices.sensex.change.toFixed(2)}</span>
                                        <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 bg-white/5 rounded">
                                            {indices.sensex.pChange.toFixed(2)}%
                                        </span>
                                    </div>
                                </div>
                                <Layers className={indices.sensex.change >= 0 ? 'text-trading-profit' : 'text-trading-loss'} size={32} />
                            </div>
                        </Card>
                    </div>
                </motion.div>

                {/* Sidebar Intelligence */}
                <motion.div variants={itemVariants} className="xl:col-span-4 space-y-8" {...({} as any)}>
                    <Card title="Portfolio Summary">
                        <div className="space-y-4">
                            <div className="flex justify-between items-center pb-4 border-b border-glass-border">
                                <span className="text-[10px] font-bold uppercase tracking-widest text-gray-500">Portfolio Value</span>
                                <span className="text-xl font-display font-black text-white">{formatCurrency(portfolioValue)}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-[10px] font-bold uppercase tracking-widest text-gray-500">Holdings Count</span>
                                <span className="text-sm font-mono text-white">{(data?.holdings?.data || []).length}</span>
                            </div>
                            <div className="flex justify-between items-center pb-4 border-b border-glass-border">
                                <span className="text-[10px] font-bold uppercase tracking-widest text-gray-500">Positions Count</span>
                                <span className="text-sm font-mono text-white">{(data?.positions?.data || []).length}</span>
                            </div>
                        </div>
                    </Card>

                    <Card title="Top Exposure">
                        <div className="space-y-6">
                            {(data?.positions?.data || []).slice(0, 3).map((pos: any, i: number) => (
                                <div key={i} className="flex justify-between items-center group/pos">
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-xl bg-obsidian-700 flex items-center justify-center border border-glass-border group-hover/pos:border-brand/50 transition-colors">
                                            <Layers size={18} className="text-gray-400" />
                                        </div>
                                        <div>
                                            <p className="text-xs font-display font-black text-white uppercase tracking-tight">{pos.tsym}</p>
                                            <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest">Qty: {pos.netQty}</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className={`text-sm font-mono font-black ${parseFloat(pos.urmtom) >= 0 ? 'text-trading-profit neon-glow-profit' : 'text-trading-loss neon-glow-loss'}`}>
                                            {formatCurrency(pos.urmtom)}
                                        </p>
                                        <div className="h-1 w-20 bg-gray-800 rounded-full mt-1 overflow-hidden">
                                            <div
                                                className={`h-full ${parseFloat(pos.urmtom) >= 0 ? 'bg-trading-profit' : 'bg-trading-loss'}`}
                                                style={{ width: `${Math.min(Math.abs(parseFloat(pos.urmtom) / 1000) * 100, 100)}%` }}
                                            />
                                        </div>
                                    </div>
                                </div>
                            ))}
                            {!(data?.positions?.data || []).length && (
                                <div className="flex flex-col items-center py-10 opacity-50">
                                    <Layers size={32} className="text-gray-700 mb-2" />
                                    <p className="text-[10px] text-gray-600 font-bold uppercase tracking-widest text-center">No Active Exposure</p>
                                </div>
                            )}
                        </div>
                    </Card>

                    <motion.div
                        whileHover={{ scale: 1.02 }}
                        className="p-8 bg-brand rounded-3xl shadow-[0_0_50px_rgba(99,102,241,0.3)] border border-white/20 relative overflow-hidden group cursor-pointer"
                    >
                        <div className="relative z-10">
                            <h3 className="text-white font-display font-black text-xl mb-1 tracking-tighter">PREMIUM INSIGHTS</h3>
                            <p className="text-indigo-100 text-[10px] font-bold uppercase tracking-widest mb-6 opacity-80">Market Volatility High</p>
                            <Button variant="secondary" size="sm" className="bg-white text-brand border-none shadow-xl hover:bg-indigo-50">UPGRADE NOW</Button>
                        </div>
                        <Activity className="absolute bottom-[-20px] right-[-20px] text-white/10 w-40 h-40 group-hover:rotate-12 transition-transform duration-1000" />
                    </motion.div>
                </motion.div>
            </div>
        </motion.div>
    );
};

export default Dashboard;
