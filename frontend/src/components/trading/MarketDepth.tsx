import React from 'react';
import { formatCurrency } from '../../utils/formatters';

interface MarketDepthProps {
    bids: any[];
    asks: any[];
}

export const MarketDepth: React.FC<MarketDepthProps> = ({ bids, asks }) => {
    const maxVolume = Math.max(
        ...bids.map(b => parseFloat(b.qty) || 0),
        ...asks.map(a => parseFloat(a.qty) || 0),
        1
    );

    return (
        <div className="grid grid-cols-2 gap-px bg-white/[0.03] border border-glass-border overflow-hidden rounded-2xl shadow-xl">
            {/* Bids Column */}
            <div className="bg-obsidian-900/30 p-2 space-y-px">
                <div className="flex justify-between px-3 py-2 mb-1 border-b border-white/[0.03]">
                    <span className="text-[9px] font-display font-black text-gray-500 uppercase tracking-widest">Qty</span>
                    <span className="text-[9px] font-display font-black text-gray-500 uppercase tracking-widest">Bid Price</span>
                </div>
                {bids.map((bid, i) => {
                    const width = (parseFloat(bid.qty) / maxVolume) * 100;
                    return (
                        <div key={i} className="relative group/bid h-9 flex items-center px-3 overflow-hidden">
                            <div
                                className="absolute right-0 top-1 bottom-1 bg-trading-profit/10 border-r border-trading-profit/30 transition-all duration-700"
                                style={{ width: `${width}%` }}
                            />
                            <div className="relative z-10 w-full flex justify-between items-center">
                                <span className="text-[10px] font-mono font-bold text-gray-400">{bid.qty}</span>
                                <span className="text-xs font-mono font-black text-trading-profit neon-glow-profit">
                                    {formatCurrency(bid.price)}
                                </span>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Asks Column */}
            <div className="bg-obsidian-900/30 p-2 space-y-px">
                <div className="flex justify-between px-3 py-2 mb-1 border-b border-white/[0.03]">
                    <span className="text-[9px] font-display font-black text-gray-500 uppercase tracking-widest">Ask Price</span>
                    <span className="text-[9px] font-display font-black text-gray-500 uppercase tracking-widest">Qty</span>
                </div>
                {asks.map((ask, i) => {
                    const width = (parseFloat(ask.qty) / maxVolume) * 100;
                    return (
                        <div key={i} className="relative group/ask h-9 flex items-center px-3 overflow-hidden">
                            <div
                                className="absolute left-0 top-1 bottom-1 bg-trading-loss/10 border-l border-trading-loss/30 transition-all duration-700"
                                style={{ width: `${width}%` }}
                            />
                            <div className="relative z-10 w-full flex justify-between items-center">
                                <span className="text-xs font-mono font-black text-trading-loss neon-glow-loss">
                                    {formatCurrency(ask.price)}
                                </span>
                                <span className="text-[10px] font-mono font-bold text-gray-400">{ask.qty}</span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
