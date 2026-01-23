import React from 'react';
import type { Holding } from '../../types/portfolio';
import { Skeleton } from '../Skeleton';
import { formatCurrency } from '../../utils/formatters';
import { parseSymbol } from '../../utils/symbolDecoder';

interface HoldingsTableProps {
    holdings: Holding[];
    loading: boolean;
}

export const HoldingsTable: React.FC<HoldingsTableProps> = ({ holdings, loading }) => {
    if (loading) {
        return <Skeleton height="200px" className="bg-[#171A21] mt-4" />;
    }

    if (holdings.length === 0) {
        return (
            <div className="text-center py-12 text-gray-500 bg-[#171A21] border border-gray-800 rounded-lg">
                No holdings found
            </div>
        );
    }

    return (
        <div className="overflow-x-auto rounded-lg border border-gray-800 bg-[#171A21] mt-4">
            <table className="w-full text-sm text-left">
                <thead className="bg-[#1e222d] text-gray-400 uppercase text-xs">
                    <tr>
                        <th className="px-4 py-3 font-medium">Symbol</th>
                        <th className="px-4 py-3 font-medium text-right">Qty</th>
                        <th className="px-4 py-3 font-medium text-right">Avg Cost</th>
                        <th className="px-4 py-3 font-medium text-right">LTP</th>
                        <th className="px-4 py-3 font-medium text-right">Cur Value</th>
                        <th className="px-4 py-3 font-medium text-right">P&L</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                    {holdings.map((holding, idx) => {
                        const qty = parseInt(holding.holdQty || '0');
                        const avg = parseFloat(holding.avgPrc || '0');
                        const ltp = parseFloat(holding.ltp || '0');
                        const curVal = qty * ltp;
                        const costVal = qty * avg;
                        const pnl = curVal - costVal;
                        const pnlPercent = costVal > 0 ? (pnl / costVal) * 100 : 0;
                        const isProfit = pnl >= 0;

                        return (
                            <tr key={idx} className="hover:bg-[#1e222d]/50 transition-colors">
                                <td className="px-4 py-3">
                                    <div className="text-white font-medium">{parseSymbol(holding.trdSym).displayName}</div>
                                    <div className="text-[10px] text-gray-500 font-mono">{holding.trdSym}</div>
                                </td>
                                <td className="px-4 py-3 text-right text-white">
                                    {qty}
                                </td>
                                <td className="px-4 py-3 text-right font-mono text-gray-300">
                                    {formatCurrency(avg)}
                                </td>
                                <td className="px-4 py-3 text-right font-mono text-white">
                                    {formatCurrency(ltp)}
                                </td>
                                <td className="px-4 py-3 text-right font-mono text-white">
                                    {formatCurrency(curVal)}
                                </td>
                                <td className="px-4 py-3 text-right">
                                    <div className={`font-mono font-medium ${isProfit ? 'text-green-400' : 'text-red-400'}`}>
                                        {formatCurrency(pnl)}
                                    </div>
                                    <div className={`text-[10px] ${isProfit ? 'text-green-500' : 'text-red-500'}`}>
                                        {pnlPercent > 0 ? '+' : ''}{pnlPercent.toFixed(2)}%
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
