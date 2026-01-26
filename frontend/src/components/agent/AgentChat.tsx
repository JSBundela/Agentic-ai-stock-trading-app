import React, { useState, useRef, useEffect } from 'react';
import { Bot, Send, X, Sparkles, Zap, Maximize2, Minimize2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../api/client';

import MiniIndexChart from '../MiniIndexChart';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: number;
    intent?: string;
    widget?: {
        type: 'chart';
        data: { time: string; value: number }[];
        symbol: string;
        period: string;
    } | null;
}

export const AgentChat: React.FC = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [isExpanded, setIsExpanded] = useState(false);
    const [query, setQuery] = useState('');
    const [messages, setMessages] = useState<Message[]>([
        {
            id: 'welcome',
            role: 'assistant',
            content: "Hello! I'm your Trading Assistant. Ask me to navigate, explain markets, or analyze trends.",
            timestamp: Date.now()
        }
    ]);
    const [isTyping, setIsTyping] = useState(false);
    const navigate = useNavigate();
    const chatEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isOpen]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        const userMsg: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: query,
            timestamp: Date.now()
        };

        setMessages(prev => [...prev, userMsg]);
        setQuery('');
        setIsTyping(true);

        try {
            const res = await apiClient.post('/agent/chat', { query: userMsg.content });
            const data = res.data;
            const responseContent = data.response.content;
            const orchestration = data.orchestration;

            // Handle Actions from MCP Tool Calls
            let chartWidget = null;
            if (data.mcp_tool_calls && Array.isArray(data.mcp_tool_calls)) {
                // 1. Check for Navigation
                const navCall = data.mcp_tool_calls.find((t: any) => t.tool === 'navigateTo' && t.result.success);
                if (navCall && navCall.args?.route) {
                    console.info(`[Agent] Navigating to ${navCall.args.route}`);
                    navigate(navCall.args.route);
                }

                // 2. Check for Chart Widget
                const chartCall = data.mcp_tool_calls.find((t: any) => t.tool === 'generateChart' && t.result.success);
                if (chartCall) {
                    chartWidget = {
                        type: 'chart',
                        data: chartCall.result.data,
                        symbol: chartCall.result.symbol,
                        period: chartCall.result.period
                    };
                }
            }

            const botMsg: Message = {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: typeof responseContent === 'string' ? responseContent : JSON.stringify(responseContent),
                timestamp: Date.now(),
                intent: orchestration?.agent,
                widget: chartWidget as any
            };

            setMessages(prev => [...prev, botMsg]);

        } catch (error) {
            setMessages(prev => [...prev, {
                id: Date.now().toString(),
                role: 'assistant',
                content: "I'm having trouble connecting to the AI brain right now.",
                timestamp: Date.now()
            }]);
        } finally {
            setIsTyping(false);
        }
    };

    return (
        <>
            {/* Floating Toggle Button */}
            <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsOpen(true)}
                className={`fixed bottom-6 right-6 z-40 w-14 h-14 rounded-full bg-brand shadow-[0_0_30px_rgba(99,102,241,0.5)] border border-white/20 flex items-center justify-center text-white transition-all ${isOpen ? 'scale-0 opacity-0' : 'scale-100 opacity-100'}`}
            >
                <Bot size={28} />
                <span className="absolute top-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-obsidian-950 animate-pulse" />
            </motion.button>

            {/* Chat Window */}
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{
                            opacity: 1,
                            scale: 1,
                            y: 0,
                            width: isExpanded ? 800 : 380,
                            height: isExpanded ? 800 : 600
                        }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        className={`fixed bottom-6 right-6 z-50 bg-obsidian-900/95 backdrop-blur-xl border border-glass-border rounded-3xl shadow-2xl flex flex-col overflow-hidden transition-all duration-300 ${isExpanded ? 'max-w-[90vw] max-h-[90vh]' : 'max-h-[80vh]'}`}
                    >
                        {/* Header */}
                        <div className="p-4 border-b border-glass-border flex justify-between items-center bg-white/5">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-brand to-purple-600 flex items-center justify-center shadow-lg">
                                    <Sparkles size={20} className="text-white" />
                                </div>
                                <div>
                                    <h3 className="font-display font-black text-white text-sm tracking-wide">AI ASSISTANT</h3>
                                    <p className="text-[9px] font-bold text-brand uppercase tracking-widest flex items-center gap-1">
                                        <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" /> Online
                                    </p>
                                </div>
                            </div>
                            <div className="flex items-center gap-1">
                                <button
                                    onClick={() => setIsExpanded(!isExpanded)}
                                    className="p-2 hover:bg-white/10 rounded-full transition-colors text-gray-400 hover:text-white"
                                >
                                    {isExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
                                </button>
                                <button
                                    onClick={() => setIsOpen(false)}
                                    className="p-2 hover:bg-white/10 rounded-full transition-colors text-gray-400 hover:text-white"
                                >
                                    <X size={18} />
                                </button>
                            </div>
                        </div>

                        {/* Messages Area */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
                            {messages.map((msg) => (
                                <motion.div
                                    key={msg.id}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                                >
                                    <div className={`max-w-[85%] p-3.5 rounded-2xl ${msg.role === 'user'
                                        ? 'bg-brand text-white rounded-tr-sm'
                                        : 'bg-glass-surface border border-glass-border text-gray-200 rounded-tl-sm'
                                        }`}>
                                        {msg.intent && (
                                            <span className="text-[9px] font-bold uppercase tracking-widest text-brand mb-1 block opacity-80">
                                                {msg.intent.replace('_', ' ')}
                                            </span>
                                        )}
                                        <p className="text-xs leading-relaxed font-medium">{msg.content}</p>

                                        {/* Chart Widget Rendering */}
                                        {msg.widget && msg.widget.type === 'chart' && (
                                            <div className="mt-3 w-64 h-40 bg-black/20 rounded-lg p-2 border border-white/5">
                                                <MiniIndexChart
                                                    staticData={msg.widget.data}
                                                    tradingSymbol={msg.widget.symbol}
                                                    indexName={msg.widget.symbol}
                                                    color={msg.widget.data[msg.widget.data.length - 1]?.value >= msg.widget.data[0]?.value ? '#10b981' : '#ef4444'}
                                                />
                                            </div>
                                        )}
                                    </div>
                                </motion.div>
                            ))}
                            {isTyping && (
                                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-1 p-2">
                                    <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
                                    <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
                                    <span className="w-1.5 h-1.5 bg-gray-500 rounded-full animate-bounce" />
                                </motion.div>
                            )}
                            <div ref={chatEndRef} />
                        </div>

                        {/* Input Area */}
                        <form onSubmit={handleSubmit} className="p-3 border-t border-glass-border bg-black/20">
                            <div className="relative flex items-center">
                                <input
                                    type="text"
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    placeholder="Ask to navigate, explain, or analyze..."
                                    className="w-full bg-glass-surface border border-glass-border rounded-xl py-3 pl-4 pr-12 text-xs font-bold text-white outline-none focus:border-brand/50 placeholder:text-gray-600 focus:bg-white/5 transition-all"
                                />
                                <button
                                    type="submit"
                                    disabled={!query.trim() || isTyping}
                                    className="absolute right-2 p-1.5 bg-brand rounded-lg text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-brand-hover transition-colors shadow-lg"
                                >
                                    {isTyping ? <Zap size={16} className="animate-pulse" /> : <Send size={16} />}
                                </button>
                            </div>
                        </form>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
};
