import React, { useState, useEffect } from 'react';
import { wsService } from '../services/websocket';
import { portfolioAPI } from '../api/portfolio';
import { ordersAPI } from '../api/orders';
import { parseSymbol } from '../utils/symbolDecoder';
import {
    X,
    ArrowUpRight,
    ArrowDownRight,
    Clock,
    ChevronDown,
    ChevronUp,
    ArrowRight,
    ShieldCheck,
    Zap
} from 'lucide-react';

interface OrderEntryProps {
    symbol: string;
    scrip?: any;
    onOrderPlaced?: () => void;
    onClose?: () => void;
    onExchangeToggle?: (exchange: 'NSE' | 'BSE') => void;
}

type MainTab = "Invest" | "Intraday";
type OrderType = "LIMIT" | "MARKET" | "SL-LMT" | "SL-MKT";
type ProductType = "CNC" | "MIS" | "NRML" | "BO" | "CO" | "MTF";

export const OrderEntryForm: React.FC<OrderEntryProps> = ({ symbol, scrip, onOrderPlaced, onClose, onExchangeToggle }) => {
    const [tick, setTick] = useState<any>(null);
    const [availableFunds, setAvailableFunds] = useState<number>(0);
    const [marginAvailable, setMarginAvailable] = useState<number>(0);
    const [mainTab, setMainTab] = useState<MainTab>("Intraday");
    const [transactionType, setTransactionType] = useState<"BUY" | "SELL">("BUY");
    const [productType, setProductType] = useState<ProductType>("MIS");
    const [showAdvanced, setShowAdvanced] = useState(false);
    const [orderType, setOrderType] = useState<OrderType>("LIMIT");
    const [quantity, setQuantity] = useState<number>(1);
    const [price, setPrice] = useState<number>(0);
    const [triggerPrice, setTriggerPrice] = useState<number>(0);
    const [disclosedQty, setDisclosedQty] = useState<number>(0);
    const [validity, setValidity] = useState<"GFD" | "IOC">("GFD");
    const [amoEnabled, setAmoEnabled] = useState<boolean>(false);

    // BO Details
    const [slSpread, setSlSpread] = useState<number>(0);
    const [tgSpread, setTgSpread] = useState<number>(0);
    const [trailingSl, setTrailingSl] = useState<boolean>(false);
    const [tslValue, setTslValue] = useState<number>(0);

    const parsed = parseSymbol(symbol, scrip);
    const selectedExchange = parsed.exchange as "NSE" | "BSE";

    useEffect(() => {
        if (mainTab === "Invest") {
            setProductType(parsed.isDerivative ? "NRML" : "CNC");
        } else {
            setProductType("MIS");
        }
    }, [mainTab, parsed.isDerivative]);

    useEffect(() => {
        const unsubscribe = wsService.subscribeQuotes(symbol, (data) => {
            setTick(data);
            if (price === 0 && data.ltp) setPrice(data.ltp);
            // Default AMO if market is closed, but allow manual override
            if ((data as any).isAmo && !amoEnabled) setAmoEnabled(true);
        });

        portfolioAPI.getLimits().then((res) => {
            // Same resilient parsing logic as Dashboard
            const data = (res.data && Array.isArray(res.data)) ? res.data[0] : (res.data || res);

            // Per user requirements and API docs (kotak_api_documentation.md lines 1217-1222):
            // Available Funds = Net (net available margin/cash)
            // Margin Power = Net (same value)
            const net = data.Net || "0";
            setAvailableFunds(parseFloat(net));
            setMarginAvailable(parseFloat(net));
        }).catch(err => console.error("Margin fetch error:", err));

        return () => unsubscribe();
    }, [symbol]);

    const handlePlaceOrder = async () => {
        try {
            const orderData: any = {
                trading_symbol: symbol,
                transaction_type: transactionType,
                order_type: orderType,
                product_type: productType,
                quantity,
                price: orderType.includes("MARKET") ? 0 : price,
                trigger_price: orderType.startsWith("SL") ? triggerPrice : 0,
                validity: validity,
                disclosed_quantity: disclosedQty,
                amo: amoEnabled
            };

            if (productType === "BO") {
                orderData.sl_spread = slSpread;
                orderData.tg_spread = tgSpread;
                if (trailingSl) orderData.trailing_sl = tslValue;
            }

            await ordersAPI.placeOrder(orderData);
            alert("Order placed successfully!");
            if (onOrderPlaced) onOrderPlaced();
        } catch (error: any) {
            alert(`Order failed: ${error.response?.data?.detail || error.message}`);
        }
    };

    const priceChange = tick?.ltp && tick?.close ? tick.ltp - tick.close : 0;
    const pricePercent = tick?.close ? (priceChange / tick.close) * 100 : 0;

    return (
        <div className="bg-[#181818] text-white rounded-xl border border-[#282828] shadow-2xl w-full max-w-lg overflow-hidden flex flex-col font-sans">
            {/* Synced Header */}
            <div className="p-8 pb-4 bg-[#1c1c1c] border-b border-[#282828]">
                <div className="flex justify-between items-start mb-6">
                    <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-xl ${transactionType === 'BUY' ? 'bg-blue-600/10' : 'bg-red-600/10'} border border-white/5`}>
                            {transactionType === 'BUY' ? <ShieldCheck className="text-blue-500" size={24} /> : <Zap className="text-red-500" size={24} />}
                        </div>
                        <div>
                            {/* Display company name as primary, trading symbol as secondary */}
                            {parsed.companyName ? (
                                <>
                                    <h2 className="text-xl font-bold tracking-wide leading-tight mb-1">
                                        {parsed.companyName}
                                    </h2>
                                    <div className="text-xs text-gray-500 font-semibold uppercase tracking-wider flex items-center gap-2">
                                        {parsed.baseSymbol} · {selectedExchange}
                                        {amoEnabled && (
                                            <div className="bg-amber-500/10 text-amber-500 px-2 py-0.5 rounded-md text-[9px] font-black border border-amber-500/20 flex items-center gap-1">
                                                <Clock size={10} /> AMO
                                            </div>
                                        )}
                                    </div>
                                </>
                            ) : (
                                <>
                                    <h2 className="text-2xl font-black tracking-widest uppercase leading-none mb-1">
                                        {parsed.baseSymbol}
                                    </h2>
                                    {amoEnabled && (
                                        <div className="bg-amber-500/10 text-amber-500 px-2 py-0.5 rounded-md text-[9px] font-black border border-amber-500/20 flex items-center gap-1 w-fit mt-1">
                                            <Clock size={10} /> AMO
                                        </div>
                                    )}
                                </>
                            )}
                            <div className="flex gap-4 items-center pl-0.5 mt-2">
                                <label className="flex items-center gap-2 cursor-pointer group">
                                    <div className={`w-3.5 h-3.5 rounded-full border flex items-center justify-center transition-all ${selectedExchange === 'NSE' ? 'border-blue-500 bg-blue-500/20' : 'border-[#333]'}`}>
                                        {selectedExchange === 'NSE' && <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />}
                                    </div>
                                    <input
                                        type="radio"
                                        className="hidden"
                                        name="exchange"
                                        checked={selectedExchange === 'NSE'}
                                        onChange={() => onExchangeToggle && onExchangeToggle('NSE')}
                                    />
                                    <span className={`text-[10px] font-black tracking-widest ${selectedExchange === 'NSE' ? 'text-blue-400' : 'text-gray-500'}`}>NSE</span>
                                </label>
                                <label className="flex items-center gap-2 cursor-pointer group">
                                    <div className={`w-3.5 h-3.5 rounded-full border flex items-center justify-center transition-all ${selectedExchange === 'BSE' ? 'border-amber-500 bg-amber-500/20' : 'border-[#333]'}`}>
                                        {selectedExchange === 'BSE' && <div className="w-1.5 h-1.5 rounded-full bg-amber-500" />}
                                    </div>
                                    <input
                                        type="radio"
                                        className="hidden"
                                        name="exchange"
                                        checked={selectedExchange === 'BSE'}
                                        onChange={() => onExchangeToggle && onExchangeToggle('BSE')}
                                    />
                                    <span className={`text-[10px] font-black tracking-widest ${selectedExchange === 'BSE' ? 'text-amber-400' : 'text-gray-500'}`}>BSE</span>
                                </label>
                            </div>
                        </div>
                    </div>
                    <div className="text-right flex flex-col items-end gap-2">
                        <button onClick={onClose} className="p-1.5 hover:bg-white/5 rounded-full transition-colors">
                            <X size={18} className="text-gray-500" />
                        </button>
                        <div className="text-3xl font-mono font-black tracking-tighter tabular-nums leading-none">
                            {tick?.ltp ? tick.ltp.toFixed(2) : "0.00"}
                        </div>
                        <div className={`text-[11px] font-black flex items-center justify-end uppercase tracking-tighter ${priceChange >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                            {priceChange >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
                            {Math.abs(priceChange).toFixed(2)} ({Math.abs(pricePercent).toFixed(2)}%)
                        </div>
                    </div>
                </div>

                {/* Synced Tabs */}
                <div className="flex bg-[#111] p-1 rounded-xl border border-[#282828]">
                    <button
                        onClick={() => setMainTab("Invest")}
                        className={`flex-1 py-3 rounded-lg text-[10px] font-black uppercase tracking-[0.2em] transition-all duration-300 ${mainTab === 'Invest' ? 'bg-[#282828] text-white' : 'text-gray-500 hover:text-gray-300'}`}
                    >
                        Invest
                    </button>
                    <button
                        onClick={() => setMainTab("Intraday")}
                        className={`flex-1 py-3 rounded-lg text-[10px] font-black uppercase tracking-[0.2em] transition-all duration-300 ${mainTab === 'Intraday' ? 'bg-[#282828] text-white' : 'text-gray-500 hover:text-gray-300'}`}
                    >
                        Intraday
                    </button>
                </div>

                {/* Transaction Choice */}
                <div className="grid grid-cols-2 gap-4 mt-6">
                    <button
                        onClick={() => setTransactionType("BUY")}
                        className={`py-3.5 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] border transition-all duration-300 ${transactionType === 'BUY' ? 'bg-blue-600/10 border-blue-500/50 text-blue-500' : 'bg-transparent border-[#282828] text-gray-500'}`}
                    >
                        BUY
                    </button>
                    <button
                        onClick={() => setTransactionType("SELL")}
                        className={`py-3.5 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] border transition-all duration-300 ${transactionType === 'SELL' ? 'bg-red-600/10 border-red-500/50 text-red-500' : 'bg-transparent border-[#282828] text-gray-500'}`}
                    >
                        SELL
                    </button>
                </div>
            </div>

            <div className="p-8 flex-1 overflow-y-auto space-y-10 custom-scrollbar pb-10">
                {/* Inputs */}
                <div className="grid grid-cols-2 gap-8">
                    <div className="space-y-3">
                        <label className="text-[10px] text-gray-500 font-black uppercase tracking-widest ml-1">Quantity</label>
                        <div className="relative">
                            <input
                                type="number"
                                value={quantity}
                                onChange={(e) => setQuantity(parseInt(e.target.value) || 0)}
                                className="w-full bg-[#111] border border-[#282828] rounded-xl p-5 text-xl font-black outline-none font-mono focus:border-blue-500/50 transition-all"
                            />
                            {parsed.isDerivative && (
                                <p className="absolute -bottom-6 left-1 text-[9px] text-blue-500 font-black uppercase tracking-widest">{quantity * parsed.lotSize} Shares (LOT: {parsed.lotSize})</p>
                            )}
                        </div>
                    </div>
                    <div className="space-y-3">
                        <label className="text-[10px] text-gray-500 font-black uppercase tracking-widest ml-1">Price</label>
                        <div className="relative">
                            <input
                                type="number"
                                step="0.05"
                                disabled={orderType.includes("MARKET")}
                                value={orderType.includes("MARKET") ? "" : price}
                                placeholder={orderType.includes("MARKET") ? "MARKET" : "0.00"}
                                onChange={(e) => setPrice(parseFloat(e.target.value) || 0)}
                                className="w-full bg-[#111] border border-[#282828] rounded-xl p-5 text-xl font-black outline-none font-mono focus:border-blue-500/50 transition-all disabled:opacity-30"
                            />
                        </div>
                    </div>
                </div>

                {/* AMO Button & Order Type */}
                <div className="space-y-6 pt-2">
                    <h3 className="text-[10px] text-gray-500 font-black uppercase tracking-widest ml-1">Order Type</h3>
                    <div className="flex flex-wrap gap-2">
                        <button
                            onClick={() => setAmoEnabled(!amoEnabled)}
                            className={`px-6 py-2.5 text-[10px] font-black uppercase tracking-widest rounded-xl border transition-all ${amoEnabled ? 'bg-amber-500/10 border-amber-500 text-amber-500 shadow-lg shadow-amber-500/10' : 'bg-transparent border-[#282828] text-gray-500 hover:border-[#333]'}`}
                        >
                            AMO {amoEnabled ? 'ON' : 'OFF'}
                        </button>
                        {["Limit", "Market", "SL-LMT", "SL-MKT"].map((type) => {
                            const val = type.toUpperCase() as OrderType;
                            const isSelected = orderType === val;
                            return (
                                <button
                                    key={type}
                                    onClick={() => setOrderType(val)}
                                    className={`px-6 py-2.5 text-[10px] font-black uppercase tracking-widest rounded-xl border transition-all ${isSelected ? 'bg-[#282828] border-[#444] text-white shadow-lg' : 'bg-transparent border-[#282828] text-gray-500 hover:border-[#333]'}`}
                                >
                                    {type}
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Trigger for SL */}
                {orderType.startsWith("SL") && (
                    <div className="space-y-3 animate-in fade-in slide-in-from-top-4">
                        <label className="text-[10px] text-gray-500 font-black uppercase tracking-widest ml-1">Trigger Price</label>
                        <input
                            type="number"
                            step="0.05"
                            value={triggerPrice}
                            onChange={(e) => setTriggerPrice(parseFloat(e.target.value) || 0)}
                            className="w-full bg-[#111] border border-[#282828] rounded-xl p-5 text-xl font-black outline-none font-mono focus:border-blue-500/50"
                        />
                    </div>
                )}

                {/* Product Type */}
                <div className="space-y-6 pt-2">
                    <h3 className="text-[10px] text-gray-500 font-black uppercase tracking-widest ml-1">Product Type</h3>
                    <div className="flex flex-wrap gap-2">
                        {(mainTab === "Invest" ? ["CNC", "NRML", "MTF"] : ["MIS", "CO", "BO"]).map((type) => {
                            const isSelected = productType === type;
                            const label = type === 'CNC' ? 'CASH' : type === 'MTF' ? 'PAY LATER' : type;
                            return (
                                <button
                                    key={type}
                                    onClick={() => setProductType(type as ProductType)}
                                    className={`px-6 py-2.5 text-[10px] font-black uppercase tracking-widest rounded-xl border transition-all ${isSelected ? 'bg-[#282828] border-[#444] text-white shadow-lg' : 'bg-transparent border-[#282828] text-gray-500 hover:border-[#333]'}`}
                                >
                                    {label}
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Bracket Order Fields */}
                {productType === "BO" && (
                    <div className="grid grid-cols-2 gap-4 p-6 rounded-2xl bg-[#111] border border-[#282828] animate-in zoom-in-95">
                        <div className="space-y-2">
                            <label className="text-[10px] text-gray-500 font-black uppercase tracking-widest ml-1">SL Spread</label>
                            <input
                                type="number"
                                step="0.05"
                                value={slSpread}
                                onChange={(e) => setSlSpread(parseFloat(e.target.value) || 0)}
                                className="w-full bg-[#0a0a0a] border border-[#282828] rounded-xl p-4 text-lg font-black outline-none font-mono"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-[10px] text-gray-500 font-black uppercase tracking-widest ml-1">Target</label>
                            <input
                                type="number"
                                step="0.05"
                                value={tgSpread}
                                onChange={(e) => setTgSpread(parseFloat(e.target.value) || 0)}
                                className="w-full bg-[#0a0a0a] border border-[#282828] rounded-xl p-4 text-lg font-black outline-none font-mono"
                            />
                        </div>
                        <div className="col-span-2 flex items-center justify-between bg-[#181818] p-4 rounded-xl border border-[#282828] mt-2">
                            <div className="flex items-center gap-3">
                                <input
                                    type="checkbox"
                                    checked={trailingSl}
                                    onChange={(e) => setTrailingSl(e.target.checked)}
                                    className="w-4 h-4 rounded border-[#282828] bg-[#111] text-blue-600 focus:ring-0 cursor-pointer"
                                />
                                <span className="text-[10px] text-gray-400 font-black uppercase tracking-widest">Trailing Stop</span>
                            </div>
                            {trailingSl && (
                                <input
                                    type="number"
                                    placeholder="Step"
                                    value={tslValue || ""}
                                    onChange={(e) => setTslValue(parseFloat(e.target.value) || 0)}
                                    className="w-20 bg-[#111] border border-[#282828] rounded-lg p-2 text-center text-xs font-black font-mono outline-none"
                                />
                            )}
                        </div>
                    </div>
                )}

                {/* Advanced Accordion */}
                <div className="pt-4 border-t border-[#282828]">
                    <button
                        onClick={() => setShowAdvanced(!showAdvanced)}
                        className="flex items-center justify-between w-full py-2 group"
                    >
                        <span className="text-[10px] font-black text-gray-500 uppercase tracking-widest group-hover:text-gray-300 transition-colors">Advanced Parameters</span>
                        {showAdvanced ? <ChevronUp size={20} className="text-gray-600" /> : <ChevronDown size={20} className="text-gray-600" />}
                    </button>

                    {showAdvanced && (
                        <div className="space-y-8 pt-6 animate-in slide-in-from-top-6 duration-300 pb-4">
                            <div className="space-y-4">
                                <label className="text-[10px] text-gray-500 font-black uppercase tracking-widest ml-1">Order Validity</label>
                                <div className="grid grid-cols-2 gap-4">
                                    {["GFD", "IOC"].map((v) => (
                                        <button
                                            key={v}
                                            onClick={() => setValidity(v as any)}
                                            className={`p-4 rounded-xl border transition-all text-left ${validity === v ? 'bg-[#282828] border-[#444]' : 'bg-[#111] border-[#282828]'}`}
                                        >
                                            <p className="text-xs font-black tracking-widest uppercase mb-1">{v === 'GFD' ? 'DAY' : v}</p>
                                            <p className="text-[9px] text-gray-600 font-bold uppercase">{v === 'GFD' ? 'Market Day' : 'Instant Only'}</p>
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div className="space-y-3">
                                <label className="text-[10px] text-gray-500 font-black uppercase tracking-widest ml-1">Disclosed Qty</label>
                                <input
                                    type="number"
                                    value={disclosedQty || ""}
                                    placeholder="0"
                                    onChange={(e) => setDisclosedQty(parseInt(e.target.value) || 0)}
                                    className="w-full bg-[#111] border border-[#282828] rounded-xl p-4 text-sm font-black outline-none font-mono"
                                />
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Bottom Bar: Master Action */}
            <div className="p-8 bg-[#1c1c1c] border-t border-[#282828]">
                <div className="flex justify-between items-center mb-8">
                    <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2">
                            <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest">Available Funds</span>
                            <span className="text-xs font-black font-mono">₹{availableFunds.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-[9px] text-gray-500 font-black uppercase tracking-widest">Margin Power</span>
                            <span className="text-xs font-black font-mono">₹{marginAvailable.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                        </div>
                    </div>
                    <div>
                        <span className="text-[10px] text-gray-500 font-black uppercase tracking-widest mr-2">Est Required</span>
                        <span className="text-sm font-black font-mono">
                            ₹{(quantity * (orderType.includes("MARKET") ? (tick?.ltp || 0) : price)).toLocaleString(undefined, { maximumFractionDigits: 2 })}
                        </span>
                    </div>
                </div>

                <button
                    onClick={handlePlaceOrder}
                    className={`w-full group py-5 rounded-xl font-black text-[11px] tracking-[0.4em] uppercase transition-all duration-300 flex items-center justify-center gap-4 ${transactionType === "BUY" ? 'bg-blue-600 hover:bg-blue-500 shadow-xl' : 'bg-red-600 hover:bg-red-500 shadow-xl'}`}
                >
                    PLACE {transactionType} ORDER
                    <ArrowRight size={18} strokeWidth={3} className="group-hover:translate-x-1 transition-transform" />
                </button>
            </div>

            <style>{`
                .custom-scrollbar::-webkit-scrollbar { width: 4px; }
                .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
                .custom-scrollbar::-webkit-scrollbar-thumb { background: #282828; border-radius: 10px; }
            `}</style>
        </div >
    );
};
