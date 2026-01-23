import React from 'react';

interface TableProps {
    headers: string[];
    children: React.ReactNode;
}

export const Table: React.FC<TableProps> = ({ headers, children }) => {
    return (
        <div className="w-full overflow-x-auto">
            <table className="w-full text-left border-collapse">
                <thead>
                    <tr className="border-b border-glass-border bg-white/[0.01]">
                        {headers.map((h, i) => (
                            <th key={i} className="px-5 py-3 text-[9px] font-display font-black text-gray-500 uppercase tracking-[0.2em] whitespace-nowrap">
                                {h}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.03]">
                    {children}
                </tbody>
            </table>
        </div>
    );
};

export const TableRow: React.FC<{ children: React.ReactNode, onClick?: () => void }> = ({ children, onClick }) => {
    return (
        <tr
            onClick={onClick}
            className={`
                group transition-all duration-200 hover:bg-brand/[0.03] relative
                ${onClick ? 'cursor-pointer' : ''}
            `}
        >
            {children}
            {/* Row Hover Glow */}
            <td className="absolute inset-y-px left-0 w-0.5 bg-brand opacity-0 group-hover:opacity-100 transition-opacity" />
        </tr>
    );
};

export const TableCell: React.FC<{ children: React.ReactNode, className?: string }> = ({ children, className = '' }) => {
    return (
        <td className={`px-5 py-3.5 text-xs font-medium whitespace-nowrap ${className}`}>
            {children}
        </td>
    );
};
