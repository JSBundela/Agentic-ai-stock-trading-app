/**
 * Utility functions for formatting
 */

export const formatCurrency = (value: number | string): string => {
    const num = typeof value === 'string' ? parseFloat(value) : value;
    return `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

export const formatNumber = (value: number | string): string => {
    const num = typeof value === 'string' ? parseFloat(value) : value;
    return num.toLocaleString('en-IN');
};

export const getStatusColor = (status: string): string => {
    const statusUpper = status.toUpperCase();

    if (statusUpper.includes('OPEN') || statusUpper.includes('PENDING')) {
        return 'text-green-500 bg-green-500/10';
    }
    if (statusUpper.includes('AMO') || statusUpper.includes('AFTER MARKET')) {
        return 'text-yellow-500 bg-yellow-500/10';
    }
    if (statusUpper.includes('COMPLETE') || statusUpper.includes('EXEC')) {
        return 'text-blue-500 bg-blue-500/10';
    }
    if (statusUpper.includes('REJECT')) {
        return 'text-red-500 bg-red-500/10';
    }
    if (statusUpper.includes('CANCEL')) {
        return 'text-gray-500 bg-gray-500/10';
    }

    return 'text-gray-400 bg-gray-400/10';
};

export const getStatusBadge = (status: string): string => {
    const statusUpper = status.toUpperCase();

    if (statusUpper.includes('AMO')) return 'AMO';
    if (statusUpper.includes('OPEN')) return 'OPEN';
    if (statusUpper.includes('PENDING')) return 'PENDING';
    if (statusUpper.includes('EXEC') || statusUpper.includes('COMPLETE')) return 'EXECUTED';
    if (statusUpper.includes('REJECT')) return 'REJECTED';
    if (statusUpper.includes('CANCEL')) return 'CANCELLED';

    return status;
};
