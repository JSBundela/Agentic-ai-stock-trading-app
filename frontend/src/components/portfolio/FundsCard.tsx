import React from 'react';
import type { Limits } from '../../types/portfolio';
import { Skeleton } from '../Skeleton';
import { formatCurrency } from '../../utils/formatters';

interface FundsCardProps {
    limits: Limits | null;
    loading: boolean;
}

export const FundsCard: React.FC<FundsCardProps> = ({ limits, loading }) => {
    if (loading) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                {[...Array(3)].map((_, i) => (
                    <Skeleton key={i} height="100px" className="bg-[#171A21]" />
                ))}
            </div>
        );
    }

    if (!limits) return null;

    // Mapping fields based on observation or standard keys
    // If backend returns Test Data: NotionalCash, MarginUsed, Net
    // If Kotak Real Data: might be netCash, marginUsed, etc.
    // Mapped from Kotak Neo API response
    // Interface Limits uses normalized names: netCash -> Net, collateralValue -> CollateralValue
    const availableFunds = limits.netCash || '0';
    const marginPower = limits.netCash || '0';
    const marginUsed = limits.marginUsed || '0';
    const marginFromShares = limits.collateralValue || '0';

    const cards = [
        { label: 'Available Funds', value: availableFunds, color: 'text-white' },
        { label: 'Margin Power', value: marginPower, color: 'text-blue-400' },
        { label: 'Margin Used', value: marginUsed, color: 'text-yellow-400' },
        { label: 'Margin from Shares', value: marginFromShares, color: 'text-purple-400' }
    ];

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {cards.map((card, idx) => (
                <div key={idx} className="bg-[#171A21] border border-gray-800 p-4 rounded-lg">
                    <p className="text-gray-500 text-sm mb-1">{card.label}</p>
                    <p className={`text-2xl font-bold font-mono ${card.color}`}>
                        {formatCurrency(card.value)}
                    </p>
                </div>
            ))}
        </div>
    );
};
