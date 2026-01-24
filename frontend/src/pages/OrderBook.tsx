import React, { useState } from 'react';
import { Card } from '../components/ui/Card';
import { Table, TableRow, TableCell } from '../components/ui/Table';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useOrderBookData } from '../hooks/useOrderBookData';
import { formatCurrency } from '../utils/formatters';
import { parseSymbol } from '../utils/symbolDecoder';
import { RefreshCcw, Search, XCircle, AlertCircle, CheckCircle2, Clock } from 'lucide-react';
import { orderService } from '../services/orderService';
import { ModifyOrderDialog } from '../components/trading/ModifyOrderDialog';

const OrderBook: React.FC = () => {
    const [filter, setFilter] = useState('ALL');
    const [selectedOrder, setSelectedOrder] = useState<any>(null);
    const [isModifyOpen, setIsModifyOpen] = useState(false);
    const { orders, loading, refresh } = useOrderBookData();

    const filteredOrders = orders.filter(o => {
        const s = o.status?.toLowerCase() || '';
        if (filter === 'ALL') return true;
        if (filter === 'OPEN') return !['complete', 'rejected', 'cancelled', 'filled'].some(k => s.includes(k));
        if (filter === 'EXECUTED') return ['complete', 'filled'].some(k => s.includes(k));
        if (filter === 'FAILED') return ['rejected', 'cancelled'].some(k => s.includes(k));
        return true;
    }).sort((a, b) => {
        const timeA = a.ordTime || a.ordDtTm || '';
        const timeB = b.ordTime || b.ordDtTm || '';
        return timeB.localeCompare(timeA);
    });

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'complete': return <CheckCircle2 size={12} className="text-trading-profit" />;
            case 'rejected': return <XCircle size={12} className="text-trading-loss" />;
            case 'open': return <Clock size={12} className="text-brand animate-pulse" />;
            default: return <AlertCircle size={12} className="text-gray-500" />;
        }
    };

    const handleCancelOrder = async (order: any, displayName: string) => {
        const orderNo = order.nOrdNo || order.orderId;
        if (!orderNo) {
            alert('Order ID not found');
            return;
        }

        if (!confirm(`Cancel order?\n\n${displayName}\nQty: ${order.qty}\nPrice: ₹${order.prc}`)) {
            return;
        }

        try {
            await orderService.cancelOrder(orderNo);
            alert('✅ Order cancelled successfully!');
            refresh();
        } catch (error: any) {
            console.error('[CANCEL ERROR]:', error);
            alert(`❌ Cancel failed: ${error.response?.data?.detail || error.message}`);
        }
    };

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
            <ModifyOrderDialog
                isOpen={isModifyOpen}
                order={selectedOrder}
                onClose={() => setIsModifyOpen(false)}
                onSuccess={refresh}
            />

            <div className="flex flex-col md:flex-row justify-between items-center gap-6">
                <div className="flex gap-2 bg-obsidian-900/50 p-1 rounded-2xl border border-white/5">
                    {['ALL', 'OPEN', 'EXECUTED', 'FAILED'].map((f) => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={`px-6 py-2 rounded-xl text-[10px] font-display font-black uppercase tracking-widest transition-all duration-300 ${filter === f ? 'bg-brand text-white shadow-[0_0_20px_rgba(99,102,241,0.4)]' : 'text-gray-500 hover:text-gray-300'
                                }`}
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
                    <Button variant="glass" size="icon" onClick={refresh}>
                        <RefreshCcw size={16} className={loading ? 'animate-spin' : ''} />
                    </Button>
                </div>
            </div>

            <Card noPadding className="border-white/5 overflow-hidden shadow-2xl">
                <Table headers={['Time', 'Instrument', 'Type', 'Product', 'Qty / Filled', 'Price', 'Status', 'Actions']}>
                    {filteredOrders.map((order, i) => {
                        const parsed = parseSymbol(order.tsym);
                        const displayName = parsed.description || parsed.companyName || parsed.displayName;

                        return (
                            <TableRow key={i}>
                                <TableCell className="text-gray-500 font-mono text-[10px]">{order.ordTime || '--:--'}</TableCell>
                                <TableCell>
                                    <div className="flex flex-col group/tsym">
                                        <div className="flex items-center gap-2">
                                            <div className="flex flex-col">
                                                <span className="font-display font-black text-white tracking-tight group-hover/tsym:text-brand transition-colors text-base">
                                                    {displayName}
                                                </span>
                                                <span className="text-[10px] text-gray-500 font-mono tracking-wide mt-0.5">
                                                    {parsed.displayName}
                                                </span>
                                            </div>
                                            {order.ordGenTp === 'AMO' && (
                                                <span className="bg-amber-500/10 text-amber-500 px-1.5 py-0.5 rounded text-[8px] font-black border border-amber-500/20">AMO</span>
                                            )}
                                        </div>
                                    </div>
                                </TableCell>
                                <TableCell>
                                    {(() => {
                                        const type = (order.trnsTp || order.trantype || '').toUpperCase();
                                        if (!type) return <span className="text-[10px] text-gray-600">-</span>;
                                        const normalizedType = type === 'B' ? 'BUY' : type === 'S' ? 'SELL' : type;
                                        return (
                                            <Badge variant={normalizedType === 'BUY' ? 'success' : 'danger'}>
                                                {normalizedType}
                                            </Badge>
                                        );
                                    })()}
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
                                        {!['complete', 'rejected', 'cancel', 'filled', 'wait', 'exec'].some(k => order.status?.toLowerCase().includes(k)) && (
                                            <>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    className="px-2 py-1 text-brand hover:bg-brand/10 border border-brand/20"
                                                    onClick={() => {
                                                        setSelectedOrder(order);
                                                        setIsModifyOpen(true);
                                                    }}
                                                >
                                                    MODIFY
                                                </Button>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    className="px-2 py-1 text-trading-loss hover:bg-trading-loss/10 border border-trading-loss/20"
                                                    onClick={() => handleCancelOrder(order, displayName)}
                                                >
                                                    CANCEL
                                                </Button>
                                            </>
                                        )}
                                    </div>
                                </TableCell>
                            </TableRow>
                        );
                    })}
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
