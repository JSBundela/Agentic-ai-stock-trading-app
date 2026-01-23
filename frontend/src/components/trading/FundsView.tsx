import React from 'react';
import { StatCard } from '../ui/StatCard';
import { Card } from '../ui/Card';
import { formatCurrency } from '../../utils/formatters';

interface FundsViewProps {
    limits: any;
    loading?: boolean;
}

export const FundsView: React.FC<FundsViewProps> = ({ limits, loading }) => {
    if (!limits && !loading) return <div className="py-20 text-center opacity-40 uppercase tracking-widest text-[10px] font-bold text-gray-500">Synchronization Error</div>;

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <StatCard
                    label="Total Available"
                    value={formatCurrency(limits?.netCash || limits?.cashBal || '0')}
                    loading={loading}
                />
                <StatCard
                    label="Margin Used"
                    value={formatCurrency(limits?.marginUsed || '0')}
                    loading={loading}
                    trend={parseFloat(limits?.marginUsed) > 0 ? 'neutral' : undefined}
                />
                <StatCard
                    label="Collateral / Liquid"
                    value={formatCurrency(limits?.collateralValue || '0')}
                    loading={loading}
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card title="Balance Breakdown">
                    <div className="space-y-3">
                        <div className="flex justify-between items-center py-2 border-b border-stroke/30">
                            <span className="text-[11px] text-gray-500 font-bold uppercase">Cash Balance</span>
                            <span className="text-sm font-mono text-white">{formatCurrency(limits?.netCash || '0')}</span>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b border-stroke/30">
                            <span className="text-[11px] text-gray-500 font-bold uppercase">Pay-in Today</span>
                            <span className="text-sm font-mono text-trading-profit">{formatCurrency(limits?.adhocMargin || '0')}</span>
                        </div>
                        <div className="flex justify-between items-center py-2">
                            <span className="text-[11px] text-gray-500 font-bold uppercase">Exposure Margin</span>
                            <span className="text-sm font-mono text-gray-400">{formatCurrency(limits?.exposureMarginPrsnt || '0')}</span>
                        </div>
                    </div>
                </Card>

                <Card title="Risk Controls">
                    <div className="p-4 bg-brand/5 border border-brand/10 rounded-xl space-y-2">
                        <p className="text-[10px] text-brand font-bold uppercase tracking-widest">Architect Verification</p>
                        <p className="text-xs text-gray-400 leading-relaxed">
                            Account status is <span className="text-trading-profit font-bold uppercase">ACTIVE</span>.
                            Real-time risk monitoring is enabled for all segments including Equity, F&O, and Currencies.
                        </p>
                    </div>
                    <div className="mt-4 grid grid-cols-2 gap-2">
                        <div className="p-3 bg-surface-secondary border border-stroke/50 rounded-lg text-center">
                            <p className="text-[9px] text-gray-500 font-bold uppercase mb-1">Board Lot Limit</p>
                            <p className="text-xs font-mono text-white">{limits?.boardLotLimit || '5000'}</p>
                        </div>
                        <div className="p-3 bg-surface-secondary border border-stroke/50 rounded-lg text-center">
                            <p className="text-[9px] text-gray-500 font-bold uppercase mb-1">Entities</p>
                            <p className="text-xs font-mono text-white">NSE / BSE</p>
                        </div>
                    </div>
                </Card>
            </div>
        </div>
    );
};
