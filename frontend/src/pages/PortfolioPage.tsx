import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { StatCard } from '../components/ui/StatCard';
import { Table, TableRow, TableCell } from '../components/ui/Table';
import { Button } from '../components/ui/Button';
import { portfolioService } from '../services/portfolioService';
import { formatCurrency } from '../utils/formatters';
import { Activity, Briefcase, Calculator, Wallet, Layers } from 'lucide-react';

const PortfolioPage: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'POSITIONS' | 'HOLDINGS' | 'FUNDS'>('POSITIONS');
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    const fetchData = async () => {
        try {
            const [positions, holdings, limits] = await Promise.all([
                portfolioService.getPositions(),
                portfolioService.getHoldings(),
                portfolioService.getLimits()
            ]);
            setData({ positions, holdings, limits });
        } catch (error) {
            console.error('Failed to fetch portfolio', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, []);

    const mtm = parseFloat(data?.positions?.totalMtm) || 0;
    const dayGain = parseFloat(data?.holdings?.totalDayGain) || 0;

    return (
        <div className="space-y-8 animate-in fade-in zoom-in-95 duration-700">
            {/* HUD: Intelligence Bar */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    label="Portfolio Value"
                    value={formatCurrency(parseFloat(data?.limits?.netCash) + (parseFloat(data?.holdings?.totalMarketValue) || 0))}
                    loading={loading}
                />
                <StatCard
                    label="Unrealized P&L"
                    value={formatCurrency(mtm)}
                    trend={mtm >= 0 ? 'up' : 'down'}
                    trendValue={mtm >= 0 ? '+5.2%' : '-2.1%'}
                    loading={loading}
                />
                <StatCard
                    label="Day Change"
                    value={formatCurrency(dayGain)}
                    trend={dayGain >= 0 ? 'up' : 'down'}
                    trendValue="Equity"
                    loading={loading}
                />
                <StatCard
                    label="Exposure Count"
                    value={(data?.positions?.positions?.length || 0) + (data?.holdings?.holdings?.length || 0)}
                    trend="neutral"
                    trendValue="Active"
                    loading={loading}
                />
            </div>

            {/* Navigation Tabs */}
            <div className="flex bg-obsidian-900/50 p-1.5 rounded-3xl border border-white/5 w-fit">
                {[
                    { id: 'POSITIONS', label: 'ACTIVES', icon: Activity },
                    { id: 'HOLDINGS', label: 'EQUITY', icon: Briefcase },
                    { id: 'FUNDS', label: 'CAPITAL', icon: Wallet }
                ].map((tab) => {
                    const Icon = tab.icon;
                    return (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id as any)}
                            className={`
                                flex items-center gap-3 px-8 py-3.5 rounded-2xl text-[11px] font-display font-black uppercase tracking-[0.2em] transition-all duration-500
                                ${activeTab === tab.id ? 'bg-brand text-white shadow-[0_0_30px_rgba(99,102,241,0.3)]' : 'text-gray-500 hover:text-gray-300'}
                            `}
                        >
                            <Icon size={14} className={activeTab === tab.id ? 'animate-pulse' : ''} />
                            {tab.label}
                        </button>
                    );
                })}
            </div>

            {/* Main Data Perspective */}
            <Card noPadding className="border-white/5 shadow-2xl relative">
                {activeTab === 'POSITIONS' && (
                    <Table headers={['Instrument', 'Qty', 'Avg Price', 'LTP', 'PnL', 'Actions']}>
                        {(data?.positions?.positions || []).map((pos: any, i: number) => {
                            const isProfit = parseFloat(pos.urmtom) >= 0;
                            return (
                                <TableRow key={i}>
                                    <TableCell>
                                        <div className="flex items-center gap-4">
                                            <div className="w-10 h-10 rounded-xl bg-obsidian-800 border border-white/5 flex items-center justify-center text-gray-500">
                                                <Layers size={18} />
                                            </div>
                                            <div className="flex flex-col">
                                                <span className="font-display font-black text-white tracking-tight uppercase">{pos.tsym}</span>
                                                <span className="text-[9px] text-gray-600 font-bold uppercase tracking-widest">{pos.exch}</span>
                                            </div>
                                        </div>
                                    </TableCell>
                                    <TableCell className="font-mono text-white font-bold">{pos.netQty}</TableCell>
                                    <TableCell className="font-mono text-gray-400">{formatCurrency(pos.buyAvg)}</TableCell>
                                    <TableCell className="font-mono text-white font-black">{formatCurrency(pos.ltp)}</TableCell>
                                    <TableCell>
                                        <span className={`font-mono font-black text-sm ${isProfit ? 'text-trading-profit neon-glow-profit' : 'text-trading-loss neon-glow-loss'}`}>
                                            {formatCurrency(pos.urmtom)}
                                        </span>
                                    </TableCell>
                                    <TableCell>
                                        <Button variant="ghost" size="sm" className="text-trading-loss border border-trading-loss/20 h-8 px-4 text-[10px]">SQUARE OFF</Button>
                                    </TableCell>
                                </TableRow>
                            );
                        })}
                        {!data?.positions?.positions?.length && (
                            <tr><td colSpan={6} className="py-40 text-center"><Activity size={48} className="mx-auto text-gray-800 animate-pulse mb-6" /><p className="text-[10px] text-gray-600 font-bold uppercase tracking-[0.3em]">No Dynamic Exposures</p></td></tr>
                        )}
                    </Table>
                )}

                {activeTab === 'HOLDINGS' && (
                    <Table headers={['Instrument', 'Quantity', 'Avg Cost', 'Mkt Value', 'Day Gain', 'Total Gain']}>
                        {(data?.holdings?.holdings || []).map((hold: any, i: number) => {
                            const isProfit = parseFloat(hold.pnl) >= 0;
                            return (
                                <TableRow key={i}>
                                    <TableCell className="font-display font-black text-white uppercase tracking-tight">{hold.tsym}</TableCell>
                                    <TableCell className="font-mono text-white">{hold.qty}</TableCell>
                                    <TableCell className="font-mono text-gray-400">{formatCurrency(hold.avgPrc)}</TableCell>
                                    <TableCell className="font-mono text-white font-bold">{formatCurrency(hold.mktVal)}</TableCell>
                                    <TableCell className={`font-mono font-bold ${parseFloat(hold.dayPnl) >= 0 ? 'text-trading-profit' : 'text-trading-loss'}`}>
                                        {formatCurrency(hold.dayPnl)}
                                    </TableCell>
                                    <TableCell className={`font-mono font-black ${isProfit ? 'text-trading-profit neon-glow-profit' : 'text-trading-loss neon-glow-loss'}`}>
                                        {formatCurrency(hold.pnl)}
                                    </TableCell>
                                </TableRow>
                            );
                        })}
                        {!data?.holdings?.holdings?.length && (
                            <tr><td colSpan={6} className="py-40 text-center"><Briefcase size={48} className="mx-auto text-gray-800 opacity-50 mb-6" /><p className="text-[10px] text-gray-600 font-bold uppercase tracking-[0.3em]">Vault is Empty</p></td></tr>
                        )}
                    </Table>
                )}

                {activeTab === 'FUNDS' && (
                    <div className="p-10 grid grid-cols-1 md:grid-cols-2 gap-10">
                        <div className="space-y-8">
                            <div className="space-y-2">
                                <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest flex items-center gap-2"><Wallet size={12} className="text-brand" /> Primary Capital</p>
                                <h2 className="text-4xl font-mono font-black text-white tracking-tighter">{formatCurrency(data?.limits?.netCash)}</h2>
                            </div>
                            <div className="grid grid-cols-2 gap-6">
                                <div className="p-5 glass-card">
                                    <p className="text-[9px] text-gray-500 font-bold uppercase mb-1">Exposure Used</p>
                                    <p className="text-xl font-mono font-black text-white">{formatCurrency(data?.limits?.marginUsed)}</p>
                                </div>
                                <div className="p-5 glass-card">
                                    <p className="text-[9px] text-gray-500 font-bold uppercase mb-1">Free Limit</p>
                                    <p className="text-xl font-mono font-black text-trading-profit">{formatCurrency(data?.limits?.netCash)}</p>
                                </div>
                            </div>
                        </div>
                        <div className="space-y-6">
                            <Card title="Allocation Radar" className="bg-white/5 border-none">
                                <div className="space-y-4 pt-2">
                                    <div className="flex justify-between text-[11px] font-bold">
                                        <span className="text-gray-500 uppercase tracking-widest">Equity Usage</span>
                                        <span className="text-white font-mono">15%</span>
                                    </div>
                                    <div className="h-1.5 w-full bg-obsidian-900 rounded-full overflow-hidden">
                                        <div className="h-full bg-brand w-[15%] shadow-[0_0_10px_#6366F1]" />
                                    </div>
                                    <div className="flex justify-between text-[11px] font-bold pt-2">
                                        <span className="text-gray-500 uppercase tracking-widest">Derivatives</span>
                                        <span className="text-white font-mono">0%</span>
                                    </div>
                                    <div className="h-1.5 w-full bg-obsidian-900 rounded-full overflow-hidden">
                                        <div className="h-full bg-trading-loss w-[0%]" />
                                    </div>
                                </div>
                            </Card>
                            <Button variant="primary" className="w-full py-4"><Calculator size={16} className="mr-2" /> ADD CAPITAL</Button>
                        </div>
                    </div>
                )}
            </Card>
        </div>
    );
};

export default PortfolioPage;
