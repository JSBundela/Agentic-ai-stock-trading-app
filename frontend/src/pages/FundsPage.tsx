import React, { useEffect, useState } from 'react';
import { portfolioService } from '../services/portfolioService';
import { Card } from '../components/ui/Card';
import { formatCurrency } from '../utils/formatters';
import { Wallet, TrendingUp, Shield, DollarSign, RefreshCcw } from 'lucide-react';

interface LimitsData {
    netCash: string;
    marginUsed: string;
    collateralValue: string;
}

const FundsPage: React.FC = () => {
    const [limits, setLimits] = useState<LimitsData | null>(null);
    const [loading, setLoading] = useState(true);

    const fetchLimits = async () => {
        setLoading(true);
        try {
            const response = await portfolioService.getLimits();
            setLimits({
                netCash: response.netCash,
                marginUsed: response.marginUsed,
                collateralValue: response.collateralValue
            });
        } catch (error) {
            console.error('[FUNDS PAGE] Failed to fetch limits:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLimits();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-brand"></div>
            </div>
        );
    }

    const availableFunds = parseFloat(limits?.netCash || '0');
    const marginPower = parseFloat(limits?.netCash || '0'); // Same as Available Funds per API docs
    const usedMargin = parseFloat(limits?.marginUsed || '0');
    const marginFromShares = parseFloat(limits?.collateralValue || '0');

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-black text-white tracking-tight">Funds & Margins</h1>
                    <p className="text-sm text-gray-500 mt-1">Real-time account limits from Kotak API</p>
                </div>
                <button
                    onClick={fetchLimits}
                    className="flex items-center gap-2 px-4 py-2 bg-brand/10 text-brand border border-brand/20 rounded-xl hover:bg-brand/20 transition-all"
                >
                    <RefreshCcw size={16} className={loading ? 'animate-spin' : ''} />
                    <span className="text-sm font-bold">Refresh</span>
                </button>
            </div>

            {/* Main Funds Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Available Funds */}
                <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20">
                    <div className="flex items-start justify-between mb-4">
                        <div className="p-3 bg-blue-500/10 rounded-xl border border-blue-500/20">
                            <Wallet className="text-blue-500" size={24} />
                        </div>
                    </div>
                    <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">Available Funds</p>
                    <p className="text-3xl font-black text-white mb-1">{formatCurrency(availableFunds)}</p>
                </Card>

                {/* Margin Power */}
                <Card className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 border-purple-500/20">
                    <div className="flex items-start justify-between mb-4">
                        <div className="p-3 bg-purple-500/10 rounded-xl border border-purple-500/20">
                            <TrendingUp className="text-purple-500" size={24} />
                        </div>
                    </div>
                    <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">Margin Power</p>
                    <p className="text-3xl font-black text-white mb-1">{formatCurrency(marginPower)}</p>
                </Card>

                {/* Used Margin */}
                <Card className="bg-gradient-to-br from-red-500/10 to-red-600/5 border-red-500/20">
                    <div className="flex items-start justify-between mb-4">
                        <div className="p-3 bg-red-500/10 rounded-xl border border-red-500/20">
                            <DollarSign className="text-red-500" size={24} />
                        </div>
                    </div>
                    <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">Used Margin</p>
                    <p className="text-3xl font-black text-white mb-1">{formatCurrency(usedMargin)}</p>
                </Card>

                {/* Margin from Shares */}
                <Card className="bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/20">
                    <div className="flex items-start justify-between mb-4">
                        <div className="p-3 bg-green-500/10 rounded-xl border border-green-500/20">
                            <Shield className="text-green-500" size={24} />
                        </div>
                    </div>
                    <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">Margin from Shares</p>
                    <p className="text-3xl font-black text-white mb-1">{formatCurrency(marginFromShares)}</p>
                </Card>
            </div>

            {/* API Mapping Reference */}
            <Card title="API Field Mapping Reference" className="bg-obsidian-900/50 border-white/5">
                <div className="space-y-3">
                    <div className="flex justify-between items-center py-2 border-b border-white/5">
                        <span className="text-sm font-bold text-gray-400">UI Display</span>
                        <span className="text-sm font-bold text-gray-400">Kotak API Field</span>
                    </div>
                    <div className="flex justify-between items-center py-2">
                        <span className="text-sm text-white">Available Funds</span>
                        <code className="text-xs bg-obsidian-800 px-2 py-1 rounded text-brand font-mono">Net</code>
                    </div>
                    <div className="flex justify-between items-center py-2">
                        <span className="text-sm text-white">Margin Power</span>
                        <code className="text-xs bg-obsidian-800 px-2 py-1 rounded text-brand font-mono">Net</code>
                    </div>
                    <div className="flex justify-between items-center py-2">
                        <span className="text-sm text-white">Used Margin</span>
                        <code className="text-xs bg-obsidian-800 px-2 py-1 rounded text-brand font-mono">MarginUsed</code>
                    </div>
                    <div className="flex justify-between items-center py-2">
                        <span className="text-sm text-white">Margin from Shares</span>
                        <code className="text-xs bg-obsidian-800 px-2 py-1 rounded text-brand font-mono">CollateralValue</code>
                    </div>
                </div>
            </Card>
        </div>
    );
};

export default FundsPage;
