import React from 'react';

interface BadgeProps {
    children: React.ReactNode;
    variant?: 'info' | 'success' | 'danger' | 'warning' | 'neutral';
    className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'neutral', className = '' }) => {
    const variants = {
        info: 'bg-brand/10 text-brand border-brand/20 shadow-[0_0_8px_rgba(99,102,241,0.2)]',
        success: 'bg-trading-profit/10 text-trading-profit border-trading-profit/20 shadow-[0_0_8px_rgba(0,255,157,0.2)]',
        danger: 'bg-trading-loss/10 text-trading-loss border-trading-loss/20 shadow-[0_0_8px_rgba(255,61,113,0.2)]',
        warning: 'bg-amber-500/10 text-amber-500 border-amber-500/20 shadow-[0_0_8px_rgba(245,158,11,0.2)]',
        neutral: 'bg-white/5 text-gray-500 border-white/10',
    };

    return (
        <span className={`
            px-2.5 py-0.5 rounded-full text-[9px] font-display font-black uppercase tracking-widest border
            ${variants[variant]} ${className}
        `}>
            {children}
        </span>
    );
};
