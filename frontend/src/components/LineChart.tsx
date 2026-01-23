import React, { useEffect, useRef, useState } from 'react';
import { createChart, type IChartApi, type ISeriesApi, type LineData } from 'lightweight-charts';

interface Props {
    data: LineData[];
    symbol: string;
    height?: number;
}

const LineChart: React.FC<Props> = ({ data, symbol, height = 300 }) => {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const seriesRef = useRef<ISeriesApi<"Line"> | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        try {
            // Create chart
            const chart = createChart(chartContainerRef.current, {
                width: chartContainerRef.current.clientWidth,
                height,
                layout: {
                    background: { color: '#1a1a1a' },
                    textColor: '#d1d5db',
                },
                grid: {
                    vertLines: { color: '#2d2d2d' },
                    horzLines: { color: '#2d2d2d' },
                },
                timeScale: {
                    borderColor: '#3d3d3d',
                    timeVisible: true,
                    secondsVisible: false,
                },
                rightPriceScale: {
                    borderColor: '#3d3d3d',
                },
            });

            // Add line series using v4 API
            const lineSeries = chart.addLineSeries({
                color: '#2563eb',
                lineWidth: 2,
            });

            if (data.length > 0) {
                lineSeries.setData(data);
            }

            chartRef.current = chart;
            seriesRef.current = lineSeries;

            // Handle resize
            const handleResize = () => {
                if (chartContainerRef.current && chartRef.current) {
                    chartRef.current.applyOptions({
                        width: chartContainerRef.current.clientWidth,
                    });
                }
            };

            window.addEventListener('resize', handleResize);

            return () => {
                window.removeEventListener('resize', handleResize);
                if (chartRef.current) {
                    chartRef.current.remove();
                }
            };
        } catch (err: any) {
            console.error('Chart initialization error:', err);
            setError(err.message);
        }
    }, [height]);

    // Update data when it changes
    useEffect(() => {
        if (seriesRef.current && data.length > 0) {
            try {
                seriesRef.current.setData(data);
            } catch (err: any) {
                console.error('Chart data update error:', err);
            }
        }
    }, [data]);

    if (error) {
        return (
            <div style={{ width: '100%', padding: '20px', backgroundColor: '#2d2d2d', borderRadius: '8px', border: '1px solid #ef4444' }}>
                <div style={{ color: '#ef4444', marginBottom: '8px', fontWeight: '500' }}>Chart Error</div>
                <div style={{ color: '#fca5a5', fontSize: '14px' }}>{error}</div>
            </div>
        );
    }

    return (
        <div style={{ width: '100%' }}>
            <div style={{ marginBottom: '8px', color: '#d1d5db', fontSize: '14px', fontWeight: '500', display: 'flex', justifyContent: 'space-between' }}>
                <span>{symbol} - Live Price</span>
                <span style={{ fontSize: '12px', color: data.length === 0 ? '#f59e0b' : '#10b981' }}>
                    {data.length === 0 ? 'Waiting for data...' : `${data.length} points`}
                </span>
            </div>
            <div ref={chartContainerRef} style={{ position: 'relative', minHeight: `${height}px`, backgroundColor: '#1a1a1a', borderRadius: '4px' }} />
        </div>
    );
};

export default LineChart;
