import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Table, TableRow, TableCell } from '../components/ui/Table';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { orderService } from '../services/orderService';
import { formatCurrency } from '../utils/formatters';
import { RefreshCcw, Search, XCircle, AlertCircle, CheckCircle2, Clock } from 'lucide-react';

const OrderBook: React.FC = () => {
    const [orders, setOrders] = useState<any[]>([]);
    const [filter, setFilter] = useState('ALL');
    const [loading, setLoading] = useState(true);

    const fetchOrders = async () => {
        try {
            const response = await orderService.getOrderBook();
            setOrders(response.data || []);
        } catch (error) {
            console.error('Failed to fetch orders', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchOrders();
        const interval = setInterval(fetchOrders, 5000);
        return () => clearInterval(interval);
    }, []);

    const filteredOrders = orders.filter(o => {
        if (filter === 'ALL') return true;
        if (filter === 'OPEN') return o.status === 'open' || o.status === 'pending';
        if (filter === 'EXECUTED') return o.status === 'complete';
        if (filter === 'FAILED') return o.status === 'rejected' || o.status === 'cancelled';
        return true;
    });

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'complete': return <CheckCircle2 size={12} className="text-trading-profit" />;
            case 'rejected': return <XCircle size={12} className="text-trading-loss" />;
            case 'open': return <Clock size={12} className="text-brand animate-pulse" />;
            default: return <AlertCircle size={12} className="text-gray-500" />;
        }
    };

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
            {/* Control Bar */}
            <div className="flex flex-col md:flex-row justify-between items-center gap-6">
                <div className="flex gap-2 bg-obsidian-900/50 p-1 rounded-2xl border border-white/5">
                    {['ALL', 'OPEN', 'EXECUTED', 'FAILED'].map((f) => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={`
                                px-6 py-2 rounded-xl text-[10px] font-display font-black uppercase tracking-widest transition-all duration-300
                                ${filter === f ? 'bg-brand text-white shadow-[0_0_20px_rgba(99,102,241,0.4)]' : 'text-gray-500 hover:text-gray-300'}
                            `}
                        >
                            {f}
                        </button>
                    ))}
                </div>

                <div className="flex gap-3">
                    <div className="relative group">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-brand" size={14} />
                        <input
                            type="text"
                            placeholder="FILTER BY SYMBOL..."
                            className="bg-obsidian-900 border border-white/5 rounded-xl py-2 pl-10 pr-4 text-[10px] font-bold outline-none focus:border-brand/50 transition-all"
                        />
                    </div>
                    <Button variant="glass" size="icon" onClick={() => { setLoading(true); fetchOrders(); }}>
                        <RefreshCcw size={16} className={loading ? 'animate-spin' : ''} />
                    </Button>
                </div>
            </div>

            <Card noPadding className="border-white/5 overflow-hidden shadow-2xl">
                <Table headers={['Time', 'Instrument', 'Type', 'Product', 'Qty / Filled', 'Price', 'Status', 'Actions']}>
                    {filteredOrders.map((order, i) => (
                        <TableRow key={i}>
                            <TableCell className="text-gray-500 font-mono text-[10px]">{order.ordTime || '--:--'}</TableCell>
                            <TableCell>
                                <div className="flex flex-col group/tsym">
                                    <span className="font-display font-black text-white tracking-tight uppercase group-hover/tsym:text-brand transition-colors">{order.tsym}</span>
                                    <span className="text-[9px] text-gray-600 font-bold tracking-widest uppercase">{order.exch}</span>
                                </div>
                            </TableCell>
                            <TableCell>
                                <Badge variant={order.trantype === 'BUY' ? 'success' : 'danger'}>
                                    {order.trantype}
                                </Badge>
                            </TableCell>
                            <TableCell className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">{order.prdtype}</TableCell>
                            <TableCell className="font-mono text-white">
                                {order.qty} <span className="text-gray-600">/</span> {order.fillqty || 0}
                            </TableCell>
                            <TableCell className="font-mono text-white font-bold">{formatCurrency(order.prc)}</TableCell>
                            <TableCell>
                                <div className="flex items-center gap-2">
                                    {getStatusIcon(order.status)}
                                    <span className={`text-[10px] font-display font-black uppercase tracking-widest ${order.status === 'complete' ? 'text-trading-profit neon-glow-profit' :
                                        order.status === 'rejected' ? 'text-trading-loss neon-glow-loss' : 'text-gray-500'
                                        }`}>
                                        {order.status}
                                    </span>
                                </div>
                            </TableCell>
                            <TableCell>
                                <div className="flex gap-2">
                                    {(order.status === 'open' || order.status === 'pending') && (
                                        <>
                                            <Button variant="ghost" size="sm" className="px-2 py-1 text-brand hover:bg-brand/10 border border-brand/20">EDIT</Button>
                                            <Button variant="ghost" size="sm" className="px-2 py-1 text-trading-loss hover:bg-trading-loss/10 border border-trading-loss/20">EXIT</Button>
                                        </>
                                    )}
                                </div>
                            </TableCell>
                        </TableRow>
                    ))}
                    {filteredOrders.length === 0 && !loading && (
                        <tr>
                            <td colSpan={8} className="py-32 text-center">
                                <Clock size={48} className="mx-auto text-gray-800 mb-6 opacity-50" />
                                <h4 className="text-xl font-display font-black text-gray-700 tracking-tighter uppercase mb-2">Monitor Empty</h4>
                                <p className="text-[10px] text-gray-600 font-bold uppercase tracking-[0.3em]">No orders match your filter profile</p>
                            </td>
                        </tr>
                    )}
                </Table>
            </Card>

            {/* Statistics HUD Footprint */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 opacity-80">
                <Card title="Flow Rate" className="py-4">
                    <div className="flex items-end gap-2">
                        <span className="text-2xl font-mono font-black text-white">{filteredOrders.length}</span>
                        <span className="text-[10px] text-gray-500 font-bold uppercase mb-1.5 whitespace-nowrap tracking-widest">Active Records</span>
                    </div>
                </Card>
                <Card title="Network Integrity" className="py-4">
                    <div className="flex items-center gap-3">
                        <div className="w-2 h-2 rounded-full bg-trading-profit animate-pulse shadow-[0_0_8px_#00FF9D]" />
                        <span className="text-xs font-mono font-bold text-white uppercase tracking-tighter">ROUTER 01: SYNCED</span>
                    </div>
                </Card>
                <Card title="Terminal State" className="py-4">
                    <p className="text-[10px] text-gray-500 font-bold uppercase tracking-[0.2em]">Operational · High Precision</p>
                </Card>
            </div>
        </div>
    );
};

export default OrderBook;
