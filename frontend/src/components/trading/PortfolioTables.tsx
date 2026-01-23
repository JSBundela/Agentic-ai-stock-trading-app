import React from 'react';
import { parseSymbol } from '../../utils/symbolDecoder';
import { formatCurrency } from '../../utils/formatters';

interface PositionProps {
    positions: any[];
    loading?: boolean;
}

export const PositionsTable: React.FC<PositionProps> = ({ positions, loading }) => {
    if (loading && positions.length === 0) return <div className="h-64 animate-pulse bg-surface-card/50 rounded-xl" />;

    if (positions.length === 0) {
        return (
            <div className="py-20 text-center opacity-40">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-gray-500">No Open Exposure</p>
            </div>
        );
    }

    return (
        <div className="overflow-x-auto">
            <table className="w-full text-left border-separate border-spacing-0">
                <thead>
                    <tr className="bg-surface-secondary/30">
                        <th className="px-4 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-stroke">Instrument</th>
                        <th className="px-4 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-stroke text-right">Net Qty</th>
                        <th className="px-4 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-stroke text-right">Avg Price</th>
                        <th className="px-4 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-stroke text-right">LTP</th>
                        <th className="px-4 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-stroke text-right">P&L</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-stroke/30">
                    {positions.map((pos, idx) => {
                        const mtm = parseFloat(pos.urmtom || '0');
                        const qty = parseInt(pos.netQty || '0');
                        return (
                            <tr key={idx} className="hover:bg-surface-hover/50 transition-colors group">
                                <td className="px-4 py-3">
                                    <div className="flex flex-col">
                                        <span className="text-sm font-bold text-white uppercase group-hover:text-brand transition-colors">{parseSymbol(pos.trdSym).displayName}</span>
                                        <span className="text-[9px] font-mono text-gray-600 uppercase">{pos.trdSym} · {pos.prod}</span>
                                    </div>
                                </td>
                                <td className={`px-4 py-3 text-right font-mono text-sm font-bold ${qty > 0 ? 'text-trading-profit' : qty < 0 ? 'text-trading-loss' : 'text-gray-500'}`}>
                                    {qty}
                                </td>
                                <td className="px-4 py-3 text-right font-mono text-[11px] text-gray-400">
                                    {formatCurrency(pos.buyAvg)}
                                </td>
                                <td className="px-4 py-3 text-right font-mono text-[11px] text-white">
                                    {formatCurrency(pos.ltp)}
                                </td>
                                <td className={`px-4 py-3 text-right font-mono text-xs font-bold ${mtm >= 0 ? 'text-trading-profit' : 'text-trading-loss'}`}>
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

interface HoldingsProps {
    holdings: any[];
    loading?: boolean;
}

export const HoldingsTable: React.FC<HoldingsProps> = ({ holdings, loading }) => {
    if (loading && holdings.length === 0) return <div className="h-64 animate-pulse bg-surface-card/50 rounded-xl" />;

    if (holdings.length === 0) {
        return (
            <div className="py-20 text-center opacity-40">
                <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-gray-500">Portfolio Empty</p>
            </div>
        );
    }

    return (
        <div className="overflow-x-auto">
            <table className="w-full text-left border-separate border-spacing-0">
                <thead>
                    <tr className="bg-surface-secondary/30">
                        <th className="px-4 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-stroke">Asset</th>
                        <th className="px-4 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-stroke text-right">Qty</th>
                        <th className="px-4 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-stroke text-right">Market Value</th>
                        <th className="px-4 py-3 text-[10px] font-bold text-gray-500 uppercase tracking-widest border-b border-stroke text-right">Unrealized P&L</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-stroke/30">
                    {holdings.map((hold, idx) => {
                        const mtm = parseFloat(hold.unrealisedGainLoss || '0');
                        return (
                            <tr key={idx} className="hover:bg-surface-hover/50 transition-colors group">
                                <td className="px-4 py-3">
                                    <div className="flex flex-col">
                                        <span className="text-sm font-bold text-white uppercase group-hover:text-brand transition-colors">{hold.displaySymbol || hold.symbol}</span>
                                        <span className="text-[9px] font-mono text-gray-600 uppercase">{hold.instrumentName}</span>
                                    </div>
                                </td>
                                <td className="px-4 py-3 text-right font-mono text-sm font-bold text-gray-200">
                                    {hold.quantity}
                                </td>
                                <td className="px-4 py-3 text-right font-mono text-[11px] text-gray-400">
                                    {formatCurrency(hold.mktValue)}
                                </td>
                                <td className={`px-4 py-3 text-right font-mono text-xs font-bold ${mtm >= 0 ? 'text-trading-profit' : 'text-trading-loss'}`}>
                                    {formatCurrency(mtm)}
                                    <span className="block text-[9px] opacity-70">
                                        {((mtm / (parseFloat(hold.holdingCost) || 1)) * 100).toFixed(2)}%
                                    </span>
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};
