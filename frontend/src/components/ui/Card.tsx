import React from 'react';
import { motion } from 'framer-motion';

interface CardProps {
    title?: string;
    children: React.ReactNode;
    className?: string;
    actions?: React.ReactNode;
    noPadding?: boolean;
}

export const Card: React.FC<CardProps> = ({ title, children, className = '', actions, noPadding }) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ y: -2, scale: 1.005 }}
            transition={{ duration: 0.4, ease: "circOut" }}
            className={`glass-card overflow-hidden group/card relative ${className}`}
        >
            {(title || actions) && (
                <div className="px-6 py-4 border-b border-glass-border flex justify-between items-center bg-white/[0.02]">
                    {title && <h3 className="text-[11px] font-display font-bold text-gray-400 uppercase tracking-[0.22em]">{title}</h3>}
                    <div className="flex gap-2">{actions}</div>
                </div>
            )}
            <div className={noPadding ? '' : 'p-6'}>
                {children}
            </div>

            {/* V3 Glass Highlight - Top Flare */}
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent pointer-events-none" />

            {/* Ambient Background Glow on Hover */}
            <div className="absolute -inset-px bg-gradient-to-br from-brand/5 to-transparent pointer-events-none opacity-0 group-hover/card:opacity-100 transition-opacity duration-700" />
        </motion.div>
    );
};
