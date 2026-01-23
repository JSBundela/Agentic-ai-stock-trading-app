// WebSocket service for REAL-TIME market data from backend
// Connects to backend FastAPI WebSocket at ws://localhost:8000/ws/market-data
// Backend relays live data from Kotak Neo WebSocket
//
// STEP 2: Enhanced with comprehensive logging for field verification

interface QuoteData {
    symbol: string;
    ltp: number;
    timestamp: number;
    open?: number;
    high?: number;
    low?: number;
    close?: number;
    volume?: number;
    change?: number;
    per_change?: number;
}

type QuoteCallback = (quote: QuoteData) => void;

class WebSocketService {
    private ws: WebSocket | null = null;
    private subscriptions: Map<string, Set<QuoteCallback>> = new Map();
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 3000; // ms
    private reconnectTimeout: number | null = null;
    private connected = false;
    private connectingPromise: Promise<void> | null = null;
    private tickCount: Map<string, number> = new Map(); // Track ticks per symbol

    constructor() {
        // Auto-connect on initialization
    }

    async connect(): Promise<void> {
        if (this.connected && this.ws?.readyState === WebSocket.OPEN) {
            return Promise.resolve();
        }

        if (this.connectingPromise) {
            return this.connectingPromise;
        }

        this.connectingPromise = new Promise((resolve, reject) => {
            try {
                const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
                // Active router is at /ws/market-data as per router.py prefix
                const wsUrl = apiUrl.replace('http', 'ws') + '/ws/market-data';

                console.log(`Connecting to WebSocket: ${wsUrl}`);

                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => {
                    console.log('✅ WebSocket connected to backend');
                    this.connected = true;
                    this.reconnectAttempts = 0;
                    this.connectingPromise = null;

                    // Resubscribe to all symbols
                    this.resubscribeAll();

                    resolve();
                };

                this.ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);

                        // Handle status messages
                        if (data.status) {
                            console.log(`WebSocket status: ${data.status}`, data.symbols);
                            return;
                        }

                        // Handle tick data with COMPREHENSIVE LOGGING
                        if (data.symbol) {
                            const tickNum = (this.tickCount.get(data.symbol) || 0) + 1;
                            this.tickCount.set(data.symbol, tickNum);

                            console.group(`🔴 WebSocket LIVE Tick #${tickNum} - ${data.symbol}`);
                            console.log('RAW TICK PAYLOAD:', JSON.stringify(data, null, 2));
                            console.log('---');

                            // REQUIRED fields
                            console.log('Symbol:', data.symbol);
                            console.log('LTP:', data.ltp);
                            console.log('Timestamp:', data.timestamp, new Date(data.timestamp * 1000).toLocaleTimeString());

                            // OPTIONAL fields - verify which are present
                            console.group('📊 Additional Fields Present:');
                            if (data.open !== undefined) console.log('✅ Open:', data.open);
                            else console.log('❌ Open: NOT PROVIDED');

                            if (data.high !== undefined) console.log('✅ High:', data.high);
                            else console.log('❌ High: NOT PROVIDED');

                            if (data.low !== undefined) console.log('✅ Low:', data.low);
                            else console.log('❌ Low: NOT PROVIDED');

                            if (data.close !== undefined) console.log('✅ Close:', data.close);
                            else console.log('❌ Close: NOT PROVIDED');

                            if (data.volume !== undefined) console.log('✅ Volume:', data.volume);
                            else console.log('❌ Volume: NOT PROVIDED');

                            if (data.change !== undefined) console.log('✅ Change:', data.change);
                            else console.log('❌ Change: NOT PROVIDED');

                            if (data.per_change !== undefined) console.log('✅ % Change:', data.per_change);
                            else console.log('❌ % Change: NOT PROVIDED');
                            console.groupEnd();

                            console.log('✅ LIVE UPDATE CONFIRMED');
                            console.groupEnd();

                            // Handle ticks inside symbol block
                            this.handleQuoteUpdate(data);
                        }

                        // Handle Scrip Master readiness error (might not have symbol)
                        if (data.type === 'error' && data.code === 'SCRIP_NOT_READY') {
                            console.warn('Scrip Master not ready. Retrying subscription in 5s...');
                            setTimeout(() => {
                                this.resubscribeAll();
                            }, 5000);
                        }

                    } catch (error) {
                        console.error('Error parsing WebSocket message:', error);
                    }
                };

                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    this.connectingPromise = null;
                    reject(error);
                };

                this.ws.onclose = () => {
                    console.log('WebSocket disconnected');
                    this.connected = false;
                    this.connectingPromise = null;
                    this.handleReconnect();
                };

            } catch (error) {
                console.error('WebSocket connection error:', error);
                reject(error);
            }
        });
    }

    private resubscribeAll() {
        if (!this.connected || !this.ws || this.subscriptions.size === 0) {
            return;
        }

        const symbols = Array.from(this.subscriptions.keys());

        if (symbols.length > 0) {
            this.ws.send(JSON.stringify({
                type: 'subscribe',
                symbols
            }));

            console.log(`Resubscribed to ${symbols.length} symbols:`, symbols);
        }
    }

    private handleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * this.reconnectAttempts;

        console.log(`Reconnecting in ${delay / 1000}s (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

        this.reconnectTimeout = window.setTimeout(() => {
            this.connect().catch(err => console.error('Reconnection failed:', err));
        }, delay);
    }

    subscribeQuotes(symbol: string, callback: QuoteCallback): () => void {
        // Add callback to subscriptions
        if (!this.subscriptions.has(symbol)) {
            this.subscriptions.set(symbol, new Set());
            this.tickCount.set(symbol, 0); // Reset tick counter

            // Subscribe on backend if connected
            if (this.connected && this.ws) {
                this.ws.send(JSON.stringify({
                    type: 'subscribe',
                    symbols: [symbol]
                }));
                console.log(`📡 Subscribed to LIVE quotes for ${symbol}`);
            }
        }

        this.subscriptions.get(symbol)!.add(callback);

        // Return unsubscribe function
        return () => {
            const callbacks = this.subscriptions.get(symbol);
            if (callbacks) {
                callbacks.delete(callback);

                // If no more callbacks for this symbol, unsubscribe from backend
                if (callbacks.size === 0) {
                    this.subscriptions.delete(symbol);
                    this.tickCount.delete(symbol);

                    if (this.connected && this.ws) {
                        this.ws.send(JSON.stringify({
                            type: 'unsubscribe',
                            symbols: [symbol]
                        }));
                        console.log(`📡 Unsubscribed from quotes for ${symbol}`);
                    }
                }
            }
        };
    }

    private handleQuoteUpdate(data: QuoteData) {
        const callbacks = this.subscriptions.get(data.symbol);

        if (callbacks) {
            callbacks.forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in quote callback for ${data.symbol}:`, error);
                }
            });
        }
    }

    disconnect() {
        this.connected = false;
        this.connectingPromise = null;

        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
            this.reconnectTimeout = null;
        }

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        this.tickCount.clear();
        console.log('WebSocket disconnected');
    }
}

export const wsService = new WebSocketService();
