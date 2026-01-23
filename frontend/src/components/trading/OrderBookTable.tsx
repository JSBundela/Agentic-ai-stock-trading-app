import React from 'react';
import { parseSymbol } from '../../utils/symbolDecoder';
import { Badge } from '../ui/Badge';
import { Edit2, XCircle, MoreVertical } from 'lucide-react';
import { formatCurrency } from '../../utils/formatters';

interface Order {
    nOrdNo: string;
    trdSym: string;
    ordSt: string;
    qty: string;
    prc: string;
    avgPrc: string;
    trnsTp: string;
    exSeg: string;
    ordDtTm?: string;
    rejRsn?: string;
    prod?: string;
}

interface OrderBookTableProps {
    orders: Order[];
    loading?: boolean;
    onModify?: (order: Order) => void;
    onCancel?: (order: Order) => void;
}

export const OrderBookTable: React.FC<OrderBookTableProps> = ({ orders, loading, onModify, onCancel }) => {
    if (loading && orders.length === 0) {
        return (
            <div className="space-y-3 py-4">
                {[...Array(6)].map((_, i) => (
                    <div key={i} className="h-12 bg-surface-card/40 animate-pulse rounded-lg border border-stroke/50" />
                ))}
            </div>
        );
    }

    if (orders.length === 0) {
        return (
            <div className="py-20 text-center space-y-2 opacity-50">
                <p className="text-sm font-bold uppercase tracking-widest text-gray-500">No Orders Synchronized</p>
                <p className="text-xs text-gray-600 italic">Orders for the current day will appear here</p>
            </div>
        );
    }

    const getStatusVariant = (status: string) => {
        const s = status.toLowerCase();
        if (['complete', 'traded', 'executed'].includes(s)) return 'success';
        if (['rejected', 'cancelled'].includes(s)) return 'danger';
        if (['open', 'pending', 'amo', 'trigger pending'].includes(s)) return 'warning';
        return 'neutral';
    };

    return (
        <div className="overflow-x-auto">
            <table className="w-full text-left border-separate border-spacing-0">
                <thead>
                    <tr className="bg-surface-secondary/50">
                        <th className="px-4 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-stroke rounded-tl-lg">Time / ID</th>
                        <th className="px-4 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-stroke">Instrument</th>
                        <th className="px-4 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-stroke text-center">Side</th>
                        <th className="px-4 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-stroke text-right">Qty</th>
                        <th className="px-4 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-stroke text-right">Avg / Lmt</th>
                        <th className="px-4 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-stroke text-center">Status</th>
                        <th className="px-4 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-stroke text-right rounded-tr-lg">Action</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-stroke/30">
                    {orders.map((order) => {
                        const parsed = parseSymbol(order.trdSym);
                        const isModifiable = ['open', 'pending', 'amo', 'trigger pending'].includes(order.ordSt.toLowerCase());

                        return (
                            <tr key={order.nOrdNo} className="hover:bg-surface-hover/50 transition-colors group">
                                <td className="px-4 py-3">
                                    <div className="text-[11px] font-mono leading-none text-white">
                                        {order.ordDtTm?.split(' ')[1] || '00:00:00'}
                                    </div>
                                    <div className="text-[9px] font-mono text-gray-600 mt-1 uppercase">#{order.nOrdNo.slice(-6)}</div>
                                </td>
                                <td className="px-4 py-3">
                                    <div className="flex flex-col">
                                        <span className="text-sm font-bold text-white uppercase tracking-tight leading-none group-hover:text-brand transition-colors">
                                            {parsed.displayName}
                                        </span>
                                        <div className="flex gap-1 mt-1">
                                            <span className="text-[9px] font-bold text-gray-600 uppercase border border-stroke/50 px-1 rounded">{order.exSeg}</span>
                                            <span className="text-[9px] font-bold text-gray-600 uppercase border border-stroke/50 px-1 rounded">{order.prod}</span>
                                        </div>
                                    </div>
                                </td>
                                <td className="px-4 py-3 text-center">
                                    <span className={`text-[10px] font-black uppercase tracking-widest ${order.trnsTp === 'B' ? 'text-trading-profit' : 'text-trading-loss'}`}>
                                        {order.trnsTp === 'B' ? 'BUY' : 'SELL'}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-right">
                                    <div className="text-[11px] font-mono font-bold text-white">
                                        {order.qty}
                                    </div>
                                    <div className="text-[9px] text-gray-600 uppercase font-bold">Total</div>
                                </td>
                                <td className="px-4 py-3 text-right">
                                    <div className="text-[11px] font-mono font-bold text-white">
                                        {parseFloat(order.avgPrc) > 0 ? formatCurrency(order.avgPrc) : formatCurrency(order.prc)}
                                    </div>
                                    <div className="text-[9px] text-gray-600 uppercase font-bold">
                                        {parseFloat(order.prc) === 0 ? 'Market' : 'Limit'}
                                    </div>
                                </td>
                                <td className="px-4 py-3 text-center">
                                    <div className="flex flex-col items-center gap-1 group/status">
                                        <Badge variant={getStatusVariant(order.ordSt)}>
                                            {order.ordSt}
                                        </Badge>
                                        {order.rejRsn && (
                                            <div className="hidden group-hover/status:block absolute bg-surface-card border border-stroke p-2 rounded-lg text-[9px] text-red-400 max-w-xs z-50 shadow-2xl mt-6">
                                                {order.rejRsn}
                                            </div>
                                        )}
                                    </div>
                                </td>
                                <td className="px-4 py-3 text-right">
                                    <div className="flex justify-end gap-1">
                                        {isModifiable && (
                                            <>
                                                <button
                                                    onClick={() => onModify?.(order)}
                                                    className="p-1.5 hover:bg-brand/10 text-gray-600 hover:text-brand transition-all rounded"
                                                >
                                                    <Edit2 size={14} />
                                                </button>
                                                <button
                                                    onClick={() => onCancel?.(order)}
                                                    className="p-1.5 hover:bg-trading-loss/10 text-gray-600 hover:text-trading-loss transition-all rounded"
                                                >
                                                    <XCircle size={14} />
                                                </button>
                                            </>
                                        )}
                                        <button className="p-1.5 hover:bg-surface-secondary text-gray-700 transition-all rounded">
                                            <MoreVertical size={14} />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};
