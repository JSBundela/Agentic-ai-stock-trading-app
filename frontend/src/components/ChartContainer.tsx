import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, type ISeriesApi, type CandlestickData } from 'lightweight-charts';
import { wsService } from '../services/websocket';

interface ChartProps {
    symbol: string;
    height?: number;
}

// Backend proxy for historical data (bypasses CORS)
async function fetchYahooFinanceData(symbol: string): Promise<CandlestickData[]> {
    try {
        // Call backend proxy instead of Yahoo Finance directly
        const response = await fetch(`http://localhost:8000/historical/${symbol}`);

        if (!response.ok) {
            console.warn(`Backend historical API returned ${response.status}`);
            return [];
        }

        const data = await response.json();
        const candles = data.candles || [];

        if (candles.length === 0) {
            console.warn('No historical data available from backend');
            return [];
        }

        console.log(`Loaded ${candles.length} historical candles via backend proxy`);
        return candles;
    } catch (error) {
        console.error('Failed to fetch historical data from backend:', error);
        return [];
    }
}

export const ChartContainer: React.FC<ChartProps> = ({ symbol, height = 400 }) => {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const seriesRef = useRef<ISeriesApi<'Candlestick'>>(null);
    const lastCandleRef = useRef<CandlestickData | null>(null);
    const [loading, setLoading] = useState(true);
    const [dataLoaded, setDataLoaded] = useState(false);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: '#1a1a1a' },
                textColor: '#d1d4dc',
            },
            grid: {
                vertLines: { color: 'rgba(42, 46, 57, 0.5)' },
                horzLines: { color: 'rgba(42, 46, 57, 0.5)' },
            },
            rightPriceScale: {
                borderColor: 'rgba(197, 203, 206, 0.8)',
                autoScale: true,
            },
            timeScale: {
                borderColor: 'rgba(197, 203, 206, 0.8)',
                timeVisible: true,
                secondsVisible: false,
            },
            width: chartContainerRef.current.clientWidth,
            height: height,
        });

        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        });

        seriesRef.current = candlestickSeries;

        // STEP 1: Fetch and render historical data FIRST
        (async () => {
            setLoading(true);
            const historicalCandles = await fetchYahooFinanceData(symbol);

            if (historicalCandles.length > 0) {
                candlestickSeries.setData(historicalCandles);
                lastCandleRef.current = historicalCandles[historicalCandles.length - 1];
                console.log(`Loaded ${historicalCandles.length} historical candles for ${symbol}`);
                setDataLoaded(true);
            } else {
                console.warn('No historical data available, chart will show only WebSocket ticks');
            }

            setLoading(false);

            // STEP 2: AFTER chart is rendered, attach WebSocket for live updates
            const unsubscribe = wsService.subscribeQuotes(symbol, (tick) => {
                if (!seriesRef.current || !tick.ltp) return;

                const time = tick.timestamp;
                const ltp = tick.ltp;

                // Append WebSocket ticks to existing chart data
                const currentCandle = lastCandleRef.current;
                const minuteTimestamp = Math.floor(time / 60) * 60;

                if (currentCandle && currentCandle.time === minuteTimestamp) {
                    // Update current candle
                    const updatedCandle = {
                        ...currentCandle,
                        high: Math.max(currentCandle.high, ltp),
                        low: Math.min(currentCandle.low, ltp),
                        close: ltp,
                    };
                    seriesRef.current.update(updatedCandle);
                    lastCandleRef.current = updatedCandle;
                } else {
                    // New candle
                    const newCandle = {
                        time: minuteTimestamp as any,
                        open: ltp,
                        high: ltp,
                        low: ltp,
                        close: ltp,
                    };
                    seriesRef.current.update(newCandle);
                    lastCandleRef.current = newCandle;
                }
            });

            // Cleanup WebSocket on unmount
            return () => {
                unsubscribe();
            };
        })();

        const handleResize = () => {
            if (chartContainerRef.current) {
                chart.applyOptions({ width: chartContainerRef.current.clientWidth });
            }
        };

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
        };
    }, [symbol, height]);

    return (
        <div style={{ position: 'relative', width: '100%' }}>
            <div ref={chartContainerRef} />
            {loading && (
                <div style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    color: '#aaa',
                    fontSize: 14,
                }}>
                    Loading historical data...
                </div>
            )}
            <div style={{
                position: 'absolute',
                top: 10,
                left: 10,
                background: 'rgba(0,0,0,0.5)',
                padding: '4px 8px',
                borderRadius: 4,
                fontSize: 12,
                color: dataLoaded ? '#4ade80' : '#aaa',
                pointerEvents: 'none'
            }}>
                {dataLoaded ? `📊 ${symbol} • Historical + Live` : `Live Market Data • ${symbol}`}
            </div>
        </div>
    );
};
