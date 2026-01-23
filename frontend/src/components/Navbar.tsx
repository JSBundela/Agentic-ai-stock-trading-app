import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { User, LogOut } from 'lucide-react';

const Navbar: React.FC = () => {
    const location = useLocation();
    const { user, logout } = useAuth();
    const isActive = (path: string) => location.pathname === path;

    return (
        <nav className="bg-dark-card border-b border-dark-border">
            <div className="container mx-auto px-4">
                <div className="flex items-center justify-between h-16">
                    <div className="flex items-center space-x-8">
                        <h1 className="text-xl font-bold text-white">Kotak Neo Trading</h1>
                        <div className="hidden md:flex space-x-4">
                            <Link
                                to="/dashboard"
                                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive('/dashboard')
                                    ? 'bg-blue-500 text-white'
                                    : 'text-gray-300 hover:bg-dark-border hover:text-white'
                                    }`}
                            >
                                Dashboard
                            </Link>
                            <Link
                                to="/order-entry"
                                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive('/order-entry')
                                    ? 'bg-blue-500 text-white'
                                    : 'text-gray-300 hover:bg-dark-border hover:text-white'
                                    }`}
                            >
                                Place Order
                            </Link>
                            <Link
                                to="/order-book"
                                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive('/order-book')
                                    ? 'bg-blue-500 text-white'
                                    : 'text-gray-300 hover:bg-dark-border hover:text-white'
                                    }`}
                            >
                                Order Book
                            </Link>
                            <Link
                                to="/portfolio"
                                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${isActive('/portfolio')
                                    ? 'bg-blue-500 text-white'
                                    : 'text-gray-300 hover:bg-dark-border hover:text-white'
                                    }`}
                            >
                                Portfolio
                            </Link>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        {user && (
                            <div className="hidden md:flex items-center gap-2 text-gray-300 text-sm">
                                <User size={16} />
                                <span>{user.id}</span>
                            </div>
                        )}
                        <button
                            onClick={() => logout()}
                            className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-red-400 hover:text-red-300 hover:bg-red-400/10 rounded-md transition-all"
                        >
                            <LogOut size={16} />
                            <span>Logout</span>
                        </button>
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
