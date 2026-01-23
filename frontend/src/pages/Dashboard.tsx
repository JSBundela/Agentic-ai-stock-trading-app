import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Card } from '../components/ui/Card';
import { StatCard } from '../components/ui/StatCard';
import { Button } from '../components/ui/Button';
import { Table, TableRow, TableCell } from '../components/ui/Table';
import { Badge } from '../components/ui/Badge';
import { portfolioService } from '../services/portfolioService';
import { orderService } from '../services/orderService';
import { formatCurrency } from '../utils/formatters';
import { Activity, ArrowUpRight, ShieldCheck, Zap, Layers } from 'lucide-react';
import { Link } from 'react-router-dom';

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
    const [data, setData] = useState<any>(null);
    const [orders, setOrders] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                const [limits, positions, orderBook] = await Promise.all([
                    portfolioService.getLimits(),
                    portfolioService.getPositions(),
                    orderService.getOrderBook(1)
                ]);
                setData({ limits, positions });
                setOrders((orderBook.data || []).slice(0, 6));
            } catch (error) {
                console.error('Dashboard load failed', error);
            } finally {
                setLoading(false);
            }
        };

        fetchDashboardData();
        const interval = setInterval(fetchDashboardData, 10000);
        return () => clearInterval(interval);
    }, []);

    const mtm = parseFloat(data?.positions?.totalMtm) || 0;
    const availableFunds = parseFloat(data?.limits?.netCash) || 0;

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
                    label="Open Positions"
                    value={data?.positions?.positions?.length || 0}
                    trend="neutral"
                    trendValue="Active"
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
                        <Table headers={['Time', 'Instrument', 'Type', 'Status', 'LTP']}>
                            {orders.map((order, i) => (
                                <TableRow key={i}>
                                    <TableCell className="text-gray-500 font-mono text-[10px]">{order.ordTime || '--:--'}</TableCell>
                                    <TableCell>
                                        <div className="flex flex-col">
                                            <span className="font-display font-black text-white tracking-tight uppercase">{order.tsym}</span>
                                            <span className="text-[9px] text-gray-500 font-bold tracking-widest uppercase">{order.exch}</span>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <Badge variant={order.trantype === 'BUY' ? 'success' : 'danger'}>
                                            {order.trantype}
                                        </Badge>
                                    </TableCell>
                                    <TableCell>
                                        <span className={`text-[10px] font-bold uppercase tracking-widest ${order.status === 'complete' ? 'text-trading-profit' :
                                            order.status === 'rejected' ? 'text-trading-loss' : 'text-gray-400'
                                            }`}>
                                            {order.status}
                                        </span>
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
                        <Card title="Market Day Breadth" className="bg-gradient-to-br from-brand/5 to-transparent">
                            <div className="flex items-center gap-6">
                                <div className="p-4 bg-trading-profit/10 rounded-2xl border border-trading-profit/20">
                                    <ArrowUpRight className="text-trading-profit" size={24} />
                                </div>
                                <div>
                                    <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Trend Analysis</p>
                                    <h4 className="text-lg font-display font-black text-white">BULLISH SENTIMENT</h4>
                                </div>
                            </div>
                        </Card>
                        <Card title="Quick Actions">
                            <div className="grid grid-cols-2 gap-3">
                                <Button variant="primary" size="sm" className="w-full"><Zap size={14} className="mr-1" /> BUY</Button>
                                <Button variant="danger" size="sm" className="w-full"><ShieldCheck size={14} className="mr-1" /> SELL</Button>
                            </div>
                        </Card>
                    </div>
                </motion.div>

                {/* Sidebar Intelligence */}
                <motion.div variants={itemVariants} className="xl:col-span-4 space-y-8" {...({} as any)}>
                    <Card title="Top Exposure">
                        <div className="space-y-6">
                            {(data?.positions?.positions || []).slice(0, 3).map((pos: any, i: number) => (
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
                            {!data?.positions?.positions?.length && (
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
