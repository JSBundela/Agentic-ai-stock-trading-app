import React from 'react';

interface StatusBadgeProps {
    status: string;
}

const getStatusColor = (status: string) => {
    switch (status.toUpperCase()) {
        case 'TRADED':
        case 'COMPLETE':
        case 'EXECUTED':
            return 'bg-green-900/40 text-green-400 border-green-800';
        case 'OPEN':
        case 'PENDING':
        case 'TRIGGER PENDING':
        case 'AMO':
            return 'bg-blue-900/40 text-blue-400 border-blue-800';
        case 'REJECTED':
            return 'bg-red-900/40 text-red-400 border-red-800';
        case 'CANCELLED':
            return 'bg-gray-800 text-gray-400 border-gray-700';
        default:
            return 'bg-gray-900 text-gray-400 border-gray-800';
    }
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status }) => {
    const colorClass = getStatusColor(status);

    return (
        <span className={`px-2 py-0.5 text-xs font-medium rounded border ${colorClass}`}>
            {status.toUpperCase()}
        </span>
    );
};
