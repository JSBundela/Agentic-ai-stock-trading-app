import React from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';

const MotionButton = motion.button as any;

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success' | 'glass';
    size?: 'sm' | 'md' | 'lg' | 'icon';
    isLoading?: boolean;
    leftIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
    children,
    variant = 'glass',
    size = 'md',
    isLoading,
    leftIcon,
    className = '',
    ...props
}) => {
    const variants = {
        primary: 'bg-brand text-white shadow-[0_0_20px_rgba(99,102,241,0.4)] border-none',
        secondary: 'bg-obsidian-700 text-gray-300 border-glass-border',
        ghost: 'bg-transparent text-gray-400 border-none hover:bg-glass-hover',
        danger: 'bg-trading-loss/20 text-trading-loss border-trading-loss/30 shadow-[0_0_15px_rgba(255,61,113,0.2)]',
        success: 'bg-trading-profit/20 text-trading-profit border-trading-profit/30 shadow-[0_0_15px_rgba(0,255,157,0.2)]',
        glass: 'glass-button',
    };

    const sizes = {
        sm: 'px-4 py-2 text-[10px]',
        md: 'px-6 py-3 text-[11px]',
        lg: 'px-8 py-4 text-[12px]',
        icon: 'p-3',
    };

    return (
        <MotionButton
            whileHover={{ scale: 1.02, y: -1 }}
            whileTap={{ scale: 0.98, y: 0 }}
            className={`
                flex items-center justify-center gap-2 rounded-xl transition-all font-display font-black uppercase tracking-widest
                disabled:opacity-40 disabled:pointer-events-none relative overflow-hidden group
                ${variants[variant]} 
                ${sizes[size]} 
                ${className}
            `}
            disabled={isLoading}
            {...(props as any)}
        >
            {/* Glossy Overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

            {isLoading ? <Loader2 size={16} className="animate-spin" /> : leftIcon}
            <span className="relative z-10">{children}</span>
        </MotionButton>
    );
};
