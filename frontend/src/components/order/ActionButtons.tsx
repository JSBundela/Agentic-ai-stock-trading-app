import React from 'react';
import { Edit2, XCircle } from 'lucide-react';
import type { Order } from '../../types/order';

interface ActionButtonsProps {
    order: Order;
    onModify: (order: Order) => void;
    onCancel: (order: Order) => void;
}

export const ActionButtons: React.FC<ActionButtonsProps> = ({ order, onModify, onCancel }) => {
    // Only allow modification/cancellation for specific statuses
    const isModifiable = ['OPEN', 'AMO', 'PENDING', 'TRIGGER PENDING'].includes(order.ordSt.toUpperCase());

    if (!isModifiable) {
        return <div className="w-16"></div>; // Spacer
    }

    return (
        <div className="flex gap-2">
            <button
                onClick={() => onModify(order)}
                className="p-1 hover:bg-blue-900/30 rounded text-blue-400 transition-colors"
                title="Modify Order"
            >
                <Edit2 size={16} />
            </button>
            <button
                onClick={() => onCancel(order)}
                className="p-1 hover:bg-red-900/30 rounded text-red-400 transition-colors"
                title="Cancel Order"
            >
                <XCircle size={16} />
            </button>
        </div>
    );
};
