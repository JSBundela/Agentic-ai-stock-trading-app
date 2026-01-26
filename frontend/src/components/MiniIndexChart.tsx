import React, { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';
import type { IChartApi, ISeriesApi, LineData } from 'lightweight-charts';

interface MiniIndexChartProps {
    indexName: string;
    tradingSymbol: string;
    color: string;
    staticData?: { time: string; value: number }[];
}

const MiniIndexChart: React.FC<MiniIndexChartProps> = ({ indexName, tradingSymbol, color, staticData }) => {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const seriesRef = useRef<ISeriesApi<'Line'> | null>(null);
    const [currentValue, setCurrentValue] = useState<string>('--');
    const [percentChange, setPercentChange] = useState<number>(0);
    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        // Create chart
        const chart = createChart(chartContainerRef.current, {
            width: chartContainerRef.current.clientWidth,
            height: 120,
            layout: {
                background: { color: 'transparent' },
                textColor: '#888',
            },
            grid: {
                vertLines: { visible: false },
                horzLines: { visible: false },
            },
            rightPriceScale: {
                visible: false,
            },
            timeScale: {
                visible: staticData ? true : false,
            },
            crosshair: {
                vertLine: { visible: false },
                horzLine: { visible: false },
            },
        });

        const series = chart.addLineSeries({
            color: color,
            lineWidth: 2,
            priceLineVisible: false,
            lastValueVisible: false,
        });

        chartRef.current = chart;
        seriesRef.current = series;

        if (staticData) {
            // Static Mode: Use data from agent
            const formattedData = staticData.map(d => ({
                time: d.time,
                value: d.value
            }));
            series.setData(formattedData as any);
            if (formattedData.length > 0) {
                setCurrentValue(formattedData[formattedData.length - 1].value.toFixed(2));
                const open = formattedData[0].value;
                const close = formattedData[formattedData.length - 1].value;
                setPercentChange(((close - open) / open) * 100);
            }
            chart.timeScale().fitContent();
        } else {
            // Live Mode: Connect to WebSocket
            // Live Mode: Connect to WebSocket
            const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const wsUrl = apiUrl.replace(/^http/, 'ws').replace(/\/$/, '');
            const ws = new WebSocket(`${wsUrl}/ws/market/${tradingSymbol}`);
            wsRef.current = ws;

            const dataPoints: LineData[] = [];
            let openPrice = 0;

            ws.onmessage = (event) => {
                try {
                    const tick = JSON.parse(event.data);
                    if (tick.ltp) {
                        const time = Math.floor(Date.now() / 1000) as any;
                        dataPoints.push({ time, value: tick.ltp });

                        if (dataPoints.length > 50) {
                            dataPoints.shift();
                        }

                        series.setData(dataPoints);
                        setCurrentValue(tick.ltp.toFixed(2));

                        if (!openPrice && tick.open) {
                            openPrice = tick.open;
                        }

                        if (openPrice) {
                            const change = ((tick.ltp - openPrice) / openPrice) * 100;
                            setPercentChange(change);
                        }
                    }
                } catch (err) {
                    console.error('Index chart tick parse error:', err);
                }
            };
        }

        // Handle resize
        const handleResize = () => {
            if (chartContainerRef.current && chart) {
                chart.applyOptions({ width: chartContainerRef.current.clientWidth });
            }
        };
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            if (wsRef.current) {
                wsRef.current.close();
            }
            chart.remove();
        };
    }, [tradingSymbol, color, staticData]);

    return (
        <div style={{
            background: 'linear-gradient(135deg, rgba(30, 30, 30, 0.8) 0%, rgba(20, 20, 20, 0.9) 100%)',
            borderRadius: '12px',
            padding: '16px',
            border: '1px solid rgba(255, 255, 255, 0.05)',
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <div>
                    <div style={{ fontSize: '12px', color: '#888', fontWeight: '600', marginBottom: '4px' }}>
                        {indexName}
                    </div>
                    <div style={{ fontSize: '20px', fontWeight: '700', color: '#fff' }}>
                        {currentValue}
                    </div>
                </div>
                <div style={{
                    fontSize: '12px',
                    fontWeight: '700',
                    color: percentChange >= 0 ? '#10b981' : '#ef4444',
                    display: 'flex',
                    alignItems: 'center',
                }}>
                    {percentChange >= 0 ? '▲' : '▼'} {Math.abs(percentChange).toFixed(2)}%
                </div>
            </div>
            <div ref={chartContainerRef} style={{ width: '100%', height: '120px' }} />
        </div>
    );
};

export default MiniIndexChart;
