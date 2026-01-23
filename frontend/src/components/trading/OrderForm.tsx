import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { portfolioService } from '../../services/portfolioService';
import { orderService } from '../../services/orderService';
import { wsService } from '../../services/websocket';
import { formatCurrency } from '../../utils/formatters';
import { ShieldCheck, Zap, Info, ArrowDownLeft, ArrowUpRight } from 'lucide-react';

interface OrderFormProps {
    symbol: string;
    onOrderPlaced?: () => void;
}

export const OrderForm: React.FC<OrderFormProps> = ({ symbol, onOrderPlaced }) => {
    const [transactionType, setTransactionType] = useState<'BUY' | 'SELL'>('BUY');
    const [productType, setProductType] = useState('MIS');
    const [orderType, setOrderType] = useState('LIMIT');
    const [quantity, setQuantity] = useState(1);
    const [price, setPrice] = useState(0);
    const [loading, setLoading] = useState(false);
    const [funds, setFunds] = useState('0.00');
    const [ltp, setLtp] = useState(0);

    useEffect(() => {
        const unsubscribe = wsService.subscribeQuotes(symbol, (data) => {
            if (data.ltp) {
                setLtp(data.ltp);
                if (price === 0) setPrice(data.ltp);
            }
        });

        portfolioService.getLimits().then(l => setFunds(l.netCash || l.cashBal || '0'));

        return () => unsubscribe();
    }, [symbol]);

    const handlePlaceOrder = async () => {
        setLoading(true);
        try {
            await orderService.placeOrder({
                trading_symbol: symbol,
                transaction_type: transactionType,
                order_type: orderType,
                product_type: productType,
                quantity,
                price: orderType === 'MARKET' ? 0 : price,
            });
            onOrderPlaced?.();
        } catch (error) {
            console.error('Order failed', error);
        } finally {
            setLoading(false);
        }
    };

    const isBuy = transactionType === 'BUY';

    return (
        <Card title="Order Cockpit" noPadding className="shadow-[0_0_50px_rgba(0,0,0,0.5)] border-white/5 top-20 sticky">
            {/* Action Selector */}
            <div className="flex bg-obsidian-900/50 p-1.5 border-b border-glass-border">
                <button
                    onClick={() => setTransactionType('BUY')}
                    className={`
                        flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-[11px] font-display font-black uppercase tracking-[0.2em] transition-all duration-300
                        ${isBuy ? 'bg-trading-profit text-obsidian-950 shadow-[0_0_20px_rgba(0,255,157,0.4)]' : 'text-gray-500 hover:text-gray-300'}
                    `}
                >
                    <ArrowUpRight size={14} className={isBuy ? 'animate-pulse' : ''} />
                    Buy Mode
                </button>
                <button
                    onClick={() => setTransactionType('SELL')}
                    className={`
                        flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-[11px] font-display font-black uppercase tracking-[0.2em] transition-all duration-300
                        ${!isBuy ? 'bg-trading-loss text-white shadow-[0_0_20px_rgba(255,61,113,0.4)]' : 'text-gray-500 hover:text-gray-300'}
                    `}
                >
                    <ArrowDownLeft size={14} className={!isBuy ? 'animate-pulse' : ''} />
                    Sell Mode
                </button>
            </div>

            <div className="p-6 space-y-6">
                {/* Real-time Ticker */}
                <div className="flex justify-between items-center pb-4 border-b border-white/[0.03]">
                    <div className="space-y-1">
                        <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Mark Price</p>
                        <p className="text-2xl font-mono font-black text-white tracking-tighter">
                            {formatCurrency(ltp)}
                        </p>
                    </div>
                    <div className="text-right space-y-1">
                        <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Available Funds</p>
                        <p className="text-sm font-mono font-bold text-brand">{formatCurrency(funds)}</p>
                    </div>
                </div>

                {/* Grid Inputs */}
                <div className="grid grid-cols-2 gap-5">
                    <div className="space-y-2">
                        <label className="text-[10px] text-gray-500 font-bold uppercase tracking-widest ml-1">Product</label>
                        <select
                            value={productType}
                            onChange={(e) => setProductType(e.target.value)}
                            className="w-full bg-white/[0.03] border border-glass-border rounded-xl p-3 text-xs font-bold text-white outline-none focus:border-brand/50 hover:bg-white/[0.05] transition-all"
                        >
                            <option value="MIS">INTRADAY (MIS)</option>
                            <option value="CNC">INVESTMENT (CNC)</option>
                            <option value="NRML">CARRYOVER (NRML)</option>
                        </select>
                    </div>
                    <div className="space-y-2">
                        <label className="text-[10px] text-gray-500 font-bold uppercase tracking-widest ml-1">Type</label>
                        <select
                            value={orderType}
                            onChange={(e) => setOrderType(e.target.value)}
                            className="w-full bg-white/[0.03] border border-glass-border rounded-xl p-3 text-xs font-bold text-white outline-none focus:border-brand/50 hover:bg-white/[0.05] transition-all"
                        >
                            <option value="LIMIT">LIMIT</option>
                            <option value="MARKET">MARKET</option>
                        </select>
                    </div>
                    <div className="space-y-2">
                        <label className="text-[10px] text-gray-500 font-bold uppercase tracking-widest ml-1">Quantity</label>
                        <input
                            type="number"
                            value={quantity}
                            onChange={(e) => setQuantity(Math.max(1, Number(e.target.value)))}
                            className="w-full bg-white/[0.03] border border-glass-border rounded-xl p-3 text-sm font-mono font-bold text-white outline-none focus:border-brand shadow-inner"
                        />
                    </div>
                    <div className="space-y-2">
                        <label className="text-[10px] text-gray-500 font-bold uppercase tracking-widest ml-1">Price</label>
                        <div className="relative">
                            <input
                                type="number"
                                disabled={orderType === 'MARKET'}
                                value={orderType === 'MARKET' ? '' : price}
                                onChange={(e) => setPrice(Number(e.target.value))}
                                placeholder="MARKET"
                                className="w-full bg-white/[0.03] border border-glass-border rounded-xl p-3 text-sm font-mono font-bold text-white outline-none focus:border-brand disabled:opacity-30 shadow-inner"
                            />
                        </div>
                    </div>
                </div>

                {/* Margin Calculator */}
                <div className="bg-white/[0.02] border border-white/[0.05] rounded-2xl p-4 flex justify-between items-center group/margin">
                    <div>
                        <p className="text-[10px] text-gray-600 font-bold uppercase tracking-widest mb-1 group-hover/margin:text-gray-400 transition-colors">Est. Margin Needed</p>
                        <p className="text-xl font-mono font-black text-white tracking-tighter">
                            {formatCurrency(quantity * (price || ltp))}
                        </p>
                    </div>
                    <div className="w-12 h-12 rounded-xl bg-brand/10 border border-brand/20 flex items-center justify-center text-brand">
                        <ShieldCheck size={24} />
                    </div>
                </div>

                {/* Execution Button */}
                <div className="pt-2 space-y-4">
                    <Button
                        variant={isBuy ? 'primary' : 'danger'}
                        className={`
                            w-full py-5 text-sm font-display font-black tracking-[0.3em] uppercase rounded-2xl relative overflow-hidden group/exec
                            ${isBuy ? 'shadow-[0_0_30px_rgba(99,102,241,0.3)]' : 'shadow-[0_0_30px_rgba(255,61,113,0.3)]'}
                        `}
                        onClick={handlePlaceOrder}
                        isLoading={loading}
                    >
                        <div className="absolute inset-0 bg-white/20 translate-y-full group-hover/exec:translate-y-0 transition-transform duration-500" />
                        <span className="relative z-10 flex items-center gap-3">
                            {isBuy ? <Zap size={16} fill="white" /> : <ShieldCheck size={16} fill="white" />}
                            EXECUTE {transactionType}
                        </span>
                    </Button>
                    <p className="text-[9px] text-gray-600 text-center uppercase tracking-[0.25em] flex items-center justify-center gap-2 opacity-60">
                        <Info size={10} /> Certified Kotak Neo Router active
                    </p>
                </div>
            </div>
        </Card>
    );
};
