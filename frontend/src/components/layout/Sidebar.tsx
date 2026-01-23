import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
    LayoutDashboard,
    MousePointer2,
    BookOpen,
    Briefcase,
    Wallet,
    LogOut,
    CircleStop
} from 'lucide-react';

const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Orders', path: '/order-entry', icon: MousePointer2 },
    { label: 'Book', path: '/order-book', icon: BookOpen },
    { label: 'Portfolio', path: '/portfolio', icon: Briefcase },
    { label: 'Funds', path: '/funds', icon: Wallet },
];

import { useAuth } from '../../context/AuthContext';

export const Sidebar: React.FC = () => {
    const location = useLocation();
    const { logout } = useAuth();

    return (
        <div className="w-64 h-full bg-obsidian-900/50 backdrop-blur-2xl border-r border-glass-border flex flex-col pt-8 pb-6 px-4">
            <div className="flex items-center gap-3 px-4 mb-10 overflow-hidden">
                <div className="p-2 bg-brand rounded-xl shadow-[0_0_20px_rgba(99,102,241,0.5)]">
                    <CircleStop className="text-white fill-white" size={20} />
                </div>
                <div>
                    <h1 className="text-lg font-display font-black text-white tracking-tighter leading-none">NEO <span className="text-brand">PRO</span></h1>
                    <p className="text-[9px] text-gray-500 font-bold uppercase tracking-[0.2em] mt-1">Terminal v3.1</p>
                </div>
            </div>

            <nav className="flex-1 flex flex-col gap-1.5">
                {navItems.map((item) => {
                    const isActive = location.pathname === item.path;
                    const Icon = item.icon;
                    return (
                        <Link
                            key={item.path}
                            to={item.path}
                            className={`
                                group flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 relative overflow-hidden
                                ${isActive ? 'bg-brand/10 text-white shadow-[inset_0_0_20px_rgba(99,102,241,0.05)]' : 'text-gray-500 hover:text-gray-300 hover:bg-white/[0.02]'}
                            `}
                        >
                            {isActive && <div className="absolute left-0 top-3 bottom-3 w-1 bg-brand rounded-full shadow-[0_0_10px_#6366F1]" />}
                            <Icon size={18} className={isActive ? 'text-brand drop-shadow-[0_0_8px_#6366F1]' : ''} />
                            <span className="text-[12px] font-bold tracking-tight">{item.label}</span>
                        </Link>
                    );
                })}
            </nav>

            <div className="mt-auto space-y-4">
                <div className="bg-glass-surface rounded-2xl p-4 border border-glass-border">
                    <p className="text-[9px] text-gray-500 font-bold uppercase tracking-widest mb-1">Live Connection</p>
                    <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-trading-profit animate-pulse shadow-[0_0_8px_#00FF9D]" />
                        <span className="text-xs font-mono font-bold text-white">NSE/BSE ACTIVE</span>
                    </div>
                </div>

                <button
                    onClick={() => logout()}
                    className="flex items-center gap-3 px-4 py-3 w-full text-gray-500 hover:text-trading-loss transition-colors group"
                >
                    <LogOut size={18} className="group-hover:translate-x-1 transition-transform" />
                    <span className="text-[12px] font-bold tracking-tight">Sign Out</span>
                </button>
            </div>
        </div>
    );
};
