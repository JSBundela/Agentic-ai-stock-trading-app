import React from 'react';
import type { Order } from '../../types/order';
import { StatusBadge } from './StatusBadge';
import { ActionButtons } from './ActionButtons';
import { Skeleton } from '../Skeleton';
import { parseSymbol } from '../../utils/symbolDecoder';

interface OrderTableProps {
    orders: Order[];
    loading: boolean;
    onModify: (order: Order) => void;
    onCancel: (order: Order) => void;
}

export const OrderTable: React.FC<OrderTableProps> = ({ orders, loading, onModify, onCancel }) => {
    if (loading && orders.length === 0) {
        // Skeleton Loader
        return (
            <div className="space-y-2 mt-4">
                {[...Array(5)].map((_, i) => (
                    <Skeleton key={i} width="100%" height="48px" className="bg-[#171A21]" />
                ))}
            </div>
        );
    }

    if (orders.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                <p>No orders found in this category.</p>
            </div>
        );
    }

    return (
        <div className="overflow-x-auto rounded-lg border border-gray-800 bg-[#171A21] mt-4">
            <table className="w-full text-sm text-left">
                <thead className="bg-[#1e222d] text-gray-400 uppercase text-xs">
                    <tr>
                        <th className="px-4 py-3 font-medium">Time / ID</th>
                        <th className="px-4 py-3 font-medium">Symbol</th>
                        <th className="px-4 py-3 font-medium">Side/Type</th>
                        <th className="px-4 py-3 font-medium text-right">Qty</th>
                        <th className="px-4 py-3 font-medium text-right">Price</th>
                        <th className="px-4 py-3 font-medium text-center">Status</th>
                        <th className="px-4 py-3 font-medium text-right">Action</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                    {orders.map((order) => (
                        <tr key={order.nOrdNo} className="hover:bg-[#1e222d]/50 transition-colors">
                            {/* Time / ID */}
                            <td className="px-4 py-3">
                                <div className="text-gray-300 font-mono text-xs">{order.ordDtTm?.split(' ')[1] || order.ordDtTm}</div>
                                <div className="text-gray-600 text-[10px] font-mono mt-0.5" title={order.nOrdNo}>
                                    {order.nOrdNo.slice(-6)}
                                </div>
                            </td>

                            {/* Symbol */}
                            <td className="px-4 py-3">
                                <div className="text-white font-medium">{parseSymbol(order.trdSym).displayName}</div>
                                <div className="flex gap-2">
                                    <span className="text-[10px] text-gray-500 bg-gray-900 px-1 rounded">{order.exSeg?.toUpperCase()}</span>
                                    <span className="text-[10px] text-gray-500 bg-gray-900 px-1 rounded">{order.prod}</span>
                                </div>
                            </td>

                            {/* Side / Type */}
                            <td className="px-4 py-3">
                                <div className={`font-medium ${order.trnsTp === 'B' ? 'text-green-400' : 'text-red-400'}`}>
                                    {order.trnsTp === 'B' ? 'BUY' : 'SELL'}
                                </div>
                                <div className="text-[10px] text-gray-500">
                                    {order.prcTp}
                                    {order.ordGenTp === 'AMO' && <span className="ml-1 text-yellow-500">AMO</span>}
                                </div>
                            </td>

                            {/* Qty */}
                            <td className="px-4 py-3 text-right">
                                <div className="text-gray-300">
                                    {order.fldQty || 0} <span className="text-gray-600">/ {order.qty}</span>
                                </div>
                            </td>

                            {/* Price */}
                            <td className="px-4 py-3 text-right font-mono">
                                <div className="text-white">
                                    {order.avgPrc && parseFloat(order.avgPrc) > 0 ? order.avgPrc : order.prc}
                                </div>
                                <div className="text-[10px] text-gray-500">
                                    {parseFloat(order.prc) === 0 ? 'MKT' : 'LMT'}
                                </div>
                            </td>

                            {/* Status */}
                            <td className="px-4 py-3 text-center">
                                <StatusBadge status={order.ordSt} />
                                {/* Rejection Reason Tooltip or Text */}
                            </td>

                            {/* Actions */}
                            <td className="px-4 py-3 text-right flex justify-end">
                                <ActionButtons
                                    order={order}
                                    onModify={onModify}
                                    onCancel={onCancel}
                                />
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};
