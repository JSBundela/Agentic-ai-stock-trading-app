import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { orderService } from '../../services/orderService';
import { X } from 'lucide-react';

interface ModifyOrderDialogProps {
    order: any;
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
}

export const ModifyOrderDialog: React.FC<ModifyOrderDialogProps> = ({ order, isOpen, onClose, onSuccess }) => {
    const [price, setPrice] = useState<string>('0');
    const [quantity, setQuantity] = useState<string>('0');
    const [orderType, setOrderType] = useState<string>('LIMIT');
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (order) {
            setPrice(order.prc || '0');
            setQuantity(order.qty || '0');
            setOrderType(order.prcTp || 'LIMIT');
        }
    }, [order]);

    if (!isOpen || !order) return null;

    const handleModify = async () => {
        setLoading(true);
        try {
            await orderService.modifyOrder({
                order_id: order.nOrdNo || order.orderId,
                price: parseFloat(price),
                quantity: parseInt(quantity),
                order_type: orderType
            });
            alert('✅ Order modified successfully!');
            onSuccess();
            onClose();
        } catch (error: any) {
            console.error('Modify failed', error);
            alert(`❌ Modify failed: ${error.response?.data?.detail || error.message}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
            <Card title="Modify Order" className="w-full max-w-md shadow-2xl relative border-white/10" noPadding>
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
                >
                    <X size={20} />
                </button>

                <div className="p-6 space-y-6">
                    <div className="space-y-1">
                        <p className="text-xs font-bold text-brand uppercase tracking-widest">{order.tsym}</p>
                        <p className="text-[10px] text-gray-500 font-mono">Order ID: {order.nOrdNo}</p>
                    </div>

                    <div className="space-y-4">
                        <div className="space-y-2">
                            <label className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Order Type</label>
                            <div className="flex bg-white/[0.05] p-1 rounded-lg">
                                {['LIMIT', 'MARKET'].map((type) => (
                                    <button
                                        key={type}
                                        onClick={() => setOrderType(type)}
                                        className={`flex-1 py-2 text-[10px] font-bold rounded-md transition-all ${orderType === type
                                            ? 'bg-brand text-white shadow-lg'
                                            : 'text-gray-500 hover:text-gray-300'
                                            }`}
                                    >
                                        {type}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Quantity</label>
                                <input
                                    type="number"
                                    value={quantity}
                                    onChange={(e) => setQuantity(e.target.value)}
                                    className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm font-mono font-bold text-white outline-none focus:border-brand"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Price</label>
                                <input
                                    type="number"
                                    value={price}
                                    onChange={(e) => setPrice(e.target.value)}
                                    disabled={orderType === 'MARKET'}
                                    className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm font-mono font-bold text-white outline-none focus:border-brand disabled:opacity-50"
                                />
                            </div>
                        </div>
                    </div>

                    <div className="pt-4">
                        <Button
                            variant="primary"
                            className="w-full py-4 text-xs font-black tracking-widest uppercase"
                            onClick={handleModify}
                            isLoading={loading}
                        >
                            Confirm Modification
                        </Button>
                    </div>
                </div>
            </Card>
        </div>
    );
};
