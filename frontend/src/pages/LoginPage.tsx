import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { authAPI } from '../api/auth';
import { ShieldCheck, Zap, CircleStop, Lock, Smartphone } from 'lucide-react';

const LoginPage: React.FC = () => {
    const navigate = useNavigate();
    const [step, setStep] = useState<'TOTP' | 'MPIN'>('TOTP');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // Auth Form State
    const [formData, setFormData] = useState({
        totp: '',
        mpin: ''
    });

    const { login: syncLogin } = useAuth();

    const handleTOTPVerify = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const response = await authAPI.totpLogin({
                totp: formData.totp
            });
            // Initial view session stored for transition
            if (response.access_token) {
                localStorage.setItem('access_token', response.access_token);
                if (response.sid) localStorage.setItem('sid', response.sid);
            }
            setStep('MPIN');
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || 'Authentication Failed');
        } finally {
            setLoading(false);
        }
    };

    const handleMPINVerify = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const response = await authAPI.validateMPIN({
                mpin: formData.mpin
            });

            // Sync with global Auth State
            syncLogin(response.access_token, response.sid);
            if (response.baseUrl) localStorage.setItem('baseUrl', response.baseUrl);

            navigate('/dashboard');
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || 'Validation Failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-obsidian-950 flex flex-col items-center justify-center p-6 relative overflow-hidden font-sans text-gray-300">
            {/* Ambient Background Grid & Glows */}
            <div className="absolute inset-0 opacity-[0.03] pointer-events-none"
                style={{ backgroundImage: 'radial-gradient(#6366F1 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
            <div className="absolute top-1/4 left-1/4 w-[600px] h-[600px] bg-brand/10 blur-[150px] rounded-full animate-pulse-slow" />
            <div className="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] bg-trading-profit/5 blur-[150px] rounded-full animate-pulse-slow" />

            <div className="w-full max-w-md relative z-10 space-y-12">
                {/* Branding Reset */}
                <div className="flex flex-col items-center space-y-6 text-center">
                    <div className="w-20 h-20 bg-brand rounded-[2.5rem] shadow-[0_0_50px_rgba(99,102,241,0.5)] flex items-center justify-center relative group">
                        <CircleStop className="text-white fill-white group-hover:scale-110 transition-transform duration-500" size={32} />
                        <div className="absolute -inset-2 bg-brand/20 blur-xl rounded-full animate-ping" />
                    </div>
                    <div>
                        <h1 className="text-5xl font-display font-black text-white tracking-tighter mb-2">NEO <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand to-indigo-400">PRO</span></h1>
                        <p className="text-[10px] text-gray-500 font-bold uppercase tracking-[0.5em]">Execution-Grade Terminal</p>
                    </div>
                </div>

                <Card noPadding className="border-white/5 bg-obsidian-900/40 backdrop-blur-3xl shadow-[0_50px_100px_rgba(0,0,0,0.6)] rounded-[2.5rem] overflow-hidden">
                    <div className="p-10 space-y-8">
                        {error && (
                            <div className="bg-trading-loss/10 border border-trading-loss/20 p-4 rounded-2xl flex items-center gap-3 animate-in fade-in slide-in-from-top-2">
                                <ShieldCheck size={18} className="text-trading-loss" />
                                <p className="text-[10px] text-trading-loss font-bold uppercase tracking-wider">{error}</p>
                            </div>
                        )}

                        <form onSubmit={step === 'TOTP' ? handleTOTPVerify : handleMPINVerify} className="space-y-6">
                            {step === 'TOTP' ? (
                                <div className="space-y-2">
                                    <div className="flex justify-between items-center ml-1">
                                        <label className="text-[10px] text-gray-500 font-bold uppercase tracking-[0.2em]">Authenticator Code</label>
                                        <Smartphone size={12} className="text-gray-700" />
                                    </div>
                                    <input
                                        type="text"
                                        required
                                        maxLength={6}
                                        placeholder="000000"
                                        value={formData.totp}
                                        onChange={(e) => setFormData({ ...formData, totp: e.target.value })}
                                        className="w-full bg-white/[0.03] border border-glass-border rounded-2xl py-4 px-6 text-2xl font-mono font-black tracking-[0.5em] text-center text-brand outline-none focus:border-brand shadow-inner placeholder:text-gray-800"
                                    />
                                    <p className="text-[9px] text-gray-600 text-center uppercase tracking-widest pt-2">Enter the code from your Authenticator App</p>
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    <div className="flex justify-between items-center ml-1">
                                        <label className="text-[10px] text-gray-500 font-bold uppercase tracking-[0.2em]">Security MPIN</label>
                                        <Lock size={12} className="text-gray-700" />
                                    </div>
                                    <input
                                        type="password"
                                        required
                                        maxLength={6}
                                        placeholder="••••••"
                                        value={formData.mpin}
                                        onChange={(e) => setFormData({ ...formData, mpin: e.target.value })}
                                        className="w-full bg-white/[0.03] border border-glass-border rounded-2xl py-4 px-6 text-2xl font-mono font-black tracking-[0.5em] text-center text-white outline-none focus:border-brand shadow-inner placeholder:text-gray-800"
                                    />
                                    <p className="text-[9px] text-gray-600 text-center uppercase tracking-widest pt-2">Authorizing session with secure vault</p>
                                </div>
                            )}

                            <Button
                                variant="primary"
                                type="submit"
                                className="w-full py-5 rounded-2xl text-[12px] font-black tracking-[0.3em] uppercase group/btn"
                                isLoading={loading}
                            >
                                <span className="relative z-10 flex items-center justify-center gap-2">
                                    {step === 'TOTP' ? 'VERIFY TOTP' : 'START TRADING'}
                                    <Zap size={14} className="group-hover/btn:translate-x-1 group-hover/btn:text-trading-profit transition-all duration-300" />
                                </span>
                            </Button>
                        </form>
                    </div>

                    <div className="bg-obsidian-950/40 p-6 border-t border-white/5 text-center">
                        <p className="text-[9px] text-gray-600 font-bold uppercase tracking-widest flex items-center justify-center gap-2">
                            <ShieldCheck size={10} /> AES-256 Encrypted Session Router
                        </p>
                    </div>
                </Card>

                {/* Footnote Hub */}
                <div className="flex justify-between items-center px-6">
                    <p className="text-[9px] text-gray-700 font-bold uppercase tracking-widest">v3.1.2 Build Final</p>
                    <div className="flex gap-6">
                        <button className="text-[9px] text-gray-700 font-bold uppercase tracking-widest hover:text-brand transition-colors">Emergency Protocol</button>
                        <button className="text-[9px] text-gray-700 font-bold uppercase tracking-widest hover:text-brand transition-colors">Terminal Manual</button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
