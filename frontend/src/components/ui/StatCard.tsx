import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface StatCardProps {
    label: string;
    value: React.ReactNode;
    trend?: 'up' | 'down' | 'neutral';
    trendValue?: string;
    loading?: boolean;
}

export const StatCard: React.FC<StatCardProps> = ({ label, value, trend, trendValue, loading }) => {
    const [prevValue, setPrevValue] = useState(value);
    const [flash, setFlash] = useState(false);

    useEffect(() => {
        if (value !== prevValue) {
            setFlash(true);
            const timer = setTimeout(() => setFlash(false), 500);
            setPrevValue(value);
            return () => clearTimeout(timer);
        }
    }, [value, prevValue]);

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            whileHover={{ y: -4 }}
            className="glass-card p-6 relative overflow-hidden group/stat border-white/[0.03]"
        >
            <div className="flex justify-between items-start mb-3 relative z-10">
                <span className="text-[10px] font-display font-black text-gray-500 uppercase tracking-[0.25em]">{label}</span>
                {trend && (
                    <motion.div
                        initial={{ opacity: 0, x: 10 }}
                        animate={{ opacity: 1, x: 0 }}
                        className={`
                            flex items-center gap-1.5 px-3 py-1 rounded-lg text-[10px] font-black tracking-tight border
                            ${trend === 'up' ? 'text-trading-profit bg-trading-profit/10 border-trading-profit/20' :
                                trend === 'down' ? 'text-trading-loss bg-trading-loss/10 border-trading-loss/20' :
                                    'text-gray-500 bg-white/5 border-white/10'}
                        `}
                    >
                        {trend === 'up' ? <TrendingUp size={10} /> : trend === 'down' ? <TrendingDown size={10} /> : <Minus size={10} />}
                        {trendValue}
                    </motion.div>
                )}
            </div>

            <div className="mt-1 relative z-10">
                {loading ? (
                    <div className="h-9 w-32 bg-white/5 animate-pulse rounded-xl" />
                ) : (
                    <motion.div
                        key={value?.toString()}
                        initial={{ opacity: 0.8, x: -5 }}
                        animate={{ opacity: 1, x: 0 }}
                        className={`
                            text-3xl font-mono font-black tracking-tighter text-white transition-colors duration-500
                            ${flash && trend === 'up' ? 'text-trading-profit' : flash && trend === 'down' ? 'text-trading-loss' : 'text-white'}
                            ${trend === 'up' ? 'neon-glow-profit-sm' : trend === 'down' ? 'neon-glow-loss-sm' : ''}
                        `}
                    >
                        {value}
                    </motion.div>
                )}
            </div>

            {/* Glowing Accent Layer */}
            <AnimatePresence>
                <motion.div
                    initial={{ opacity: 0, scale: 0.5 }}
                    animate={{ opacity: flash ? 0.3 : 0.1, scale: 1 }}
                    className={`
                        absolute -right-6 -bottom-6 w-32 h-32 blur-[50px] pointer-events-none transition-all duration-1000
                        group-hover/stat:opacity-40 group-hover/stat:scale-150
                        ${trend === 'up' ? 'bg-trading-profit' : trend === 'down' ? 'bg-trading-loss' : 'bg-brand'}
                    `}
                />
            </AnimatePresence>

            {/* Top Flare Line */}
            <div className={`absolute top-0 left-0 right-0 h-[2px] opacity-[0.1] ${trend === 'up' ? 'bg-trading-profit' : trend === 'down' ? 'bg-trading-loss' : 'bg-brand'}`} />
        </motion.div>
    );
};
