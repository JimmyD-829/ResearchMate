'use client';

import React, { useEffect, useRef, useCallback } from 'react';
import {
  createChart,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  ColorType,
  CrosshairMode,
  type IChartApi,
  type ISeriesApi,
  type Time,
  type CandlestickData,
  type HistogramData,
  type LineData,
} from 'lightweight-charts';

interface KLineChartProps {
  data: Array<{
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }>;
  maLines?: {
    ma5?: number[];
    ma10?: number[];
    ma20?: number[];
    ma60?: number[];
  };
  height?: number;
}

export default function KLineChart({ data, maLines, height = 420 }: KLineChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeRef = useRef<ISeriesApi<'Histogram'> | null>(null);

  // 清理旧图表
  const disposeChart = useCallback(() => {
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
      candleRef.current = null;
      volumeRef.current = null;
    }
  }, []);

  // 初始化/更新图表
  useEffect(() => {
    if (!containerRef.current || data.length === 0) return;

    disposeChart();

    const container = containerRef.current;
    const chart = createChart(container, {
      layout: {
        background: { type: ColorType.Solid, color: '#0f172a' },
        textColor: '#94a3b8',
        fontSize: 11,
        fontFamily: "'JetBrains Mono', monospace",
      },
      grid: {
        vertLines: { color: 'rgba(255,255,255,0.03)' },
        horzLines: { color: 'rgba(255,255,255,0.03)' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: {
          color: 'rgba(99,102,241,0.4)',
          width: 1,
          style: 2,
          labelBackgroundColor: '#6366f1',
        },
        horzLine: {
          color: 'rgba(99,102,241,0.4)',
          width: 1,
          style: 2,
          labelBackgroundColor: '#6366f1',
        },
      },
      rightPriceScale: {
        borderColor: 'rgba(255,255,255,0.06)',
        scaleMargins: { top: 0.1, bottom: 0.2 },
      },
      timeScale: {
        borderColor: 'rgba(255,255,255,0.06)',
        timeVisible: true,
        secondsVisible: false,
      },
      handleScroll: { vertTouchDrag: false },
    });

    chartRef.current = chart;

    // ── K线数据 ──
    const candleData: CandlestickData[] = data.map((d) => ({
      time: (d.date as unknown as Time),
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }));

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#10b981',
      downColor: '#ef4444',
      borderUpColor: '#10b981',
      borderDownColor: '#ef4444',
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });
    candleSeries.setData(candleData);
    candleRef.current = candleSeries;

    // ── 成交量（底部）──
    const volumeData: HistogramData[] = data.map((d) => ({
      time: (d.date as unknown as Time),
      value: d.volume,
      color: d.close >= d.open ? 'rgba(16,185,129,0.25)' : 'rgba(239,68,68,0.25)',
    }));

    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume_scale',
    });
    volumeSeries.setData(volumeData);
    volumeRef.current = volumeSeries;

    chart.priceScale('volume_scale').applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

    // ── MA 均线叠加 ──
    const maColors: Record<string, string> = {
      ma5: '#f59e0b',
      ma10: '#3b82f6',
      ma20: '#a855f7',
      ma60: '#ec4899',
    };
    const maWidths: Record<string, number> = {
      ma5: 1,
      ma10: 1,
      ma20: 2,
      ma60: 2,
    };

    if (maLines) {
      for (const [key, values] of Object.entries(maLines)) {
        if (!values || values.length === 0) continue;
        const lineData: LineData[] = [];
        for (let i = 0; i < data.length; i++) {
          const val = values[i];
          if (val !== null && val !== undefined && val > 0 && !isNaN(val)) {
            lineData.push({
              time: (data[i].date as unknown as Time),
              value: val,
            });
          }
        }

        if (lineData.length > 0) {
          const lineSeries = chart.addSeries(LineSeries, {
            color: maColors[key] || '#888',
            lineWidth: (maWidths[key] || 1) as 1 | 2 | 3 | 4,
            priceLineVisible: false,
            lastValueVisible: false,
            crosshairMarkerVisible: false,
          });
          lineSeries.setData(lineData);
        }
      }
    }

    chart.timeScale().fitContent();

    return () => {
      disposeChart();
    };
  }, [data, maLines, disposeChart]);

  // 响应式调整
  useEffect(() => {
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width } = entry.contentRect;
        if (chartRef.current && width > 0) {
          chartRef.current.applyOptions({ width });
        }
      }
    });

    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={containerRef}
      style={{ width: '100%', height }}
    />
  );
}
