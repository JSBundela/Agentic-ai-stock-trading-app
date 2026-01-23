import React from 'react';
import type { Position } from '../../types/portfolio';
import { Skeleton } from '../Skeleton';
import { formatCurrency } from '../../utils/formatters';
import { parseSymbol } from '../../utils/symbolDecoder';

interface PositionsTableProps {
    positions: Position[];
    loading: boolean;
}

export const PositionsTable: React.FC<PositionsTableProps> = ({ positions, loading }) => {
    if (loading) {
        return <Skeleton height="200px" className="bg-[#171A21] mt-4" />;
    }

    if (positions.length === 0) {
        return (
            <div className="text-center py-12 text-gray-500 bg-[#171A21] border border-gray-800 rounded-lg">
                No open positions
            </div>
        );
    }

    return (
        <div className="overflow-x-auto rounded-lg border border-gray-800 bg-[#171A21] mt-4">
            <table className="w-full text-sm text-left">
                <thead className="bg-[#1e222d] text-gray-400 uppercase text-xs">
                    <tr>
                        <th className="px-4 py-3 font-medium">Symbol</th>
                        <th className="px-4 py-3 font-medium">Product</th>
                        <th className="px-4 py-3 font-medium text-right">Net Qty</th>
                        <th className="px-4 py-3 font-medium text-right">Avg Price</th>
                        <th className="px-4 py-3 font-medium text-right">LTP</th>
                        <th className="px-4 py-3 font-medium text-right">P&L</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                    {positions.map((pos, idx) => {
                        const mtm = parseFloat(pos.urmtom || '0');
                        const isProfit = mtm >= 0;
                        const netQty = parseInt(pos.netQty || '0');

                        return (
                            <tr key={idx} className="hover:bg-[#1e222d]/50 transition-colors">
                                <td className="px-4 py-3">
                                    <div className="text-white font-medium">{parseSymbol(pos.trdSym).displayName}</div>
                                    <div className="text-[10px] text-gray-500 font-mono">{pos.trdSym}</div>
                                </td>
                                <td className="px-4 py-3 text-gray-400">{pos.prod}</td>
                                <td className={`px-4 py-3 text-right font-medium ${netQty > 0 ? 'text-green-400' : netQty < 0 ? 'text-red-400' : 'text-gray-400'}`}>
                                    {netQty}
                                </td>
                                <td className="px-4 py-3 text-right font-mono text-gray-300">
                                    {formatCurrency(pos.buyAvg)}
                                </td>
                                <td className="px-4 py-3 text-right font-mono text-white">
                                    {formatCurrency(pos.ltp)}
                                </td>
                                <td className={`px-4 py-3 text-right font-mono font-medium ${isProfit ? 'text-green-400' : 'text-red-400'}`}>
                                    {formatCurrency(mtm)}
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};
