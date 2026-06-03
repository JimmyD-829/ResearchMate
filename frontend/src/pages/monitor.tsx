import React, { useState, useEffect, useCallback, useRef } from 'react';
import { pipelineApi } from '../services/api';
import Layout from '../components/Layout';

/* ── Types ─────────────────────────────────────────────── */

interface PipelineNode {
  name: string;
  status: 'ok' | 'error' | 'warning' | 'unknown' | 'skipped';
  latency_ms?: number | null;
  detail: string;
  url?: string;
  version?: string;
  data_source?: string;
  last_query_ms?: number | null;
  calls_remaining?: number | null;
}

interface Alert {
  level: 'error' | 'warning';
  node: string;
  message: string;
}

interface RequestLog {
  time?: string;
  endpoint?: string;
  path?: string;
  status?: string;
  duration_ms?: number;
  result_preview?: string;
}

interface PipelineData {
  timestamp: string;
  overall: string;
  pipeline: Record<string, PipelineNode>;
  recent_requests: RequestLog[];
  alerts: Alert[];
  env_summary: {
    relay_url_set: boolean;
    relay_key_set: boolean;
    proxy_vars: number;
    provider_mode: string;
  };
  query_elapsed_ms?: number;
}

/* ── Mock data (for prototype preview when backend unavailable) ── */

const MOCK_DATA: PipelineData = {
  timestamp: new Date().toISOString(),
  overall: 'healthy',
  pipeline: {
    render_api: {
      name: 'Render API',
      status: 'ok',
      latency_ms: 1,
      detail: 'mode=proxy',
    },
    ngrok: {
      name: 'ngrok Tunnel',
      status: 'ok',
      latency_ms: 450,
      url: 'abc123***',
      detail: '450ms',
    },
    relay_server: {
      name: 'Relay Server',
      status: 'ok',
      version: '1.3.0',
      data_source: 'tencent',
      detail: 'v1.3.0 via tencent',
    },
    cn_data_source: {
      name: '腾讯财经 (A股)',
      status: 'ok',
      last_query_ms: 89,
      detail: '600519 ¥1281.91 (89ms)',
    },
    us_data_source: {
      name: 'AlphaVantage (美股)',
      status: 'ok',
      last_query_ms: 200,
      detail: 'AAPL $178.50 (200ms)',
    },
  },
  recent_requests: [
    { time: '21:06:47', endpoint: '/realtime/600519', path: 'Render → ngrok → Relay → 腾讯', status: 'ok', duration_ms: 541, result_preview: '¥1281.91' },
    { time: '21:06:45', endpoint: '/realtime/000001', path: 'Render → ngrok → Relay → 腾讯', status: 'ok', duration_ms: 520, result_preview: '¥11.23' },
    { time: '21:06:40', endpoint: '/history/600519?days=30', path: 'Render → ngrok → Relay → 腾讯K线', status: 'ok', duration_ms: 680, result_preview: '30 records' },
    { time: '21:06:38', endpoint: '/realtime/AAPL', path: 'Render → AlphaVantage', status: 'ok', duration_ms: 200, result_preview: '$178.50' },
    { time: '21:06:35', endpoint: '/stocks', path: 'Render → ngrok → Relay', status: 'ok', duration_ms: 490, result_preview: '50 stocks' },
    { time: '21:06:30', endpoint: '/market-index', path: 'Render → ngrok → Relay', status: 'ok', duration_ms: 510, result_preview: '8 indices' },
    { time: '21:06:25', endpoint: '/realtime/300750', path: 'Render → ngrok → Relay → 腾讯', status: 'ok', duration_ms: 555, result_preview: '¥228.30' },
    { time: '21:06:20', endpoint: '/company/AAPL', path: 'Render → AlphaVantage', status: 'warning', duration_ms: 3200, result_preview: 'slow' },
  ],
  alerts: [],
  env_summary: {
    relay_url_set: true,
    relay_key_set: true,
    proxy_vars: 0,
    provider_mode: 'proxy',
  },
};

/* ── Constants ─────────────────────────────────────────── */

const PIPELINE_ORDER = ['render_api', 'ngrok', 'relay_server', 'cn_data_source', 'us_data_source'] as const;

const NODE_LABELS: Record<string, { short: string; sub: string; icon: string }> = {
  render_api:     { short: 'RENDER',   sub: 'API Server',       icon: '⚡' },
  ngrok:          { short: 'NGROK',    sub: 'Secure Tunnel',     icon: '🔗' },
  relay_server:   { short: 'RELAY',    sub: 'Domestic Node',     icon: '🖥' },
  cn_data_source: { short: 'A-SHARE',  sub: 'Tencent Finance',   icon: '🇨🇳' },
  us_data_source: { short: 'US-STOCK', sub: 'AlphaVantage',      icon: '🇺🇸' },
};

const REFRESH_INTERVAL_MS = 15_000;

/* ── Helpers ───────────────────────────────────────────── */

function statusColor(s: string): string {
  switch (s) {
    case 'ok':       return '#10b981';
    case 'warning':  return '#f59e0b';
    case 'error':    return '#ef4444';
    case 'skipped':  return '#6b7280';
    default:         return '#3b82f6';
  }
}

function statusBg(s: string): string {
  const c = statusColor(s);
  return s === 'ok' ? `rgba(16,185,129,0.12)` :
         s === 'warning' ? `rgba(245,158,11,0.12)` :
         s === 'error' ? `rgba(239,68,68,0.12)` : `rgba(107,114,128,0.10)`;
}

function statusLabel(s: string): string {
  switch (s) {
    case 'ok': return 'OPERATIONAL';
    case 'warning': return 'DEGRADED';
    case 'error': return 'DOWN';
    case 'skipped': return 'SKIPPED';
    default: return 'UNKNOWN';
  }
}

function overallBadge(overall: string): { bg: string; text: string; label: string } {
  switch (overall) {
    case 'healthy':
      return { bg: 'rgba(16,185,129,0.15)', text: '#10b981', label: 'ALL SYSTEMS OPERATIONAL' };
    case 'degraded':
      return { bg: 'rgba(245,158,11,0.15)', text: '#f59e0b', label: 'PARTIAL DEGRADATION' };
    case 'error':
      return { bg: 'rgba(239,68,68,0.15)', text: '#ef4444', label: 'SYSTEM ERROR' };
    default:
      return { bg: 'rgba(59,130,246,0.12)', text: '#60a5fa', label: 'CHECKING...' };
  }
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch {
    return '--:--:--';
  }
}

/* ════════════════════════════════════════════════════════
   COMPONENT
   ════════════════════════════════════════════════════════ */

const MonitorPage: React.FC = () => {
  const [data, setData] = useState<PipelineData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [usingMock, setUsingMock] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const [countdown, setCountdown] = useState(REFRESH_INTERVAL_MS / 1000);
  const logContainerRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  /* ── Fetch ────────────────────────────────────────── */

  const fetchData = useCallback(async () => {
    try {
      const res = await pipelineApi.getStatus();
      if (res.data) {
        setData(res.data);
        setUsingMock(false);
        setError(null);
      }
    } catch {
      // Backend not available — show mock for prototype
      setData({ ...MOCK_DATA, timestamp: new Date().toISOString() });
      setUsingMock(true);
      setError(null);
    } finally {
      setLoading(false);
      setLastRefresh(new Date());
      setCountdown(REFRESH_INTERVAL_MS / 1000);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  useEffect(() => {
    timerRef.current = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          fetchData();
          return REFRESH_INTERVAL_MS / 1000;
        }
        return prev - 1;
      });
    }, 1000);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [fetchData]);

  /* Auto-scroll log to bottom */
  useEffect(() => {
    if (logContainerRef.current && data?.recent_requests) {
      logContainerRef.current.scrollTop = 0; // newest first
    }
  }, [data?.recent_requests]);

  /* ── Render ───────────────────────────────────────── */

  if (loading && !data) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen" style={{ background: '#0a0f1a' }}>
          <div className="text-center">
            <div className="w-10 h-10 border-2 border-emerald-500/40 border-t-emerald-400 rounded-full animate-spin mx-auto mb-4" />
            <p className="text-slate-500 font-mono text-sm">INITIALIZING PIPELINE...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (!data) return null;

  const badge = overallBadge(data.overall);

  return (
    <Layout>
      {/* ── Full-bleed dashboard container ── */}
      <div style={{ background: '#0a0f1a', minHeight: '100vh' }} className="-m-4 sm:-m-6 lg:-m-8">

        {/* ═══ TOP BAR ═══ */}
        <div className="border-b" style={{ borderColor: 'rgba(255,255,255,0.06)', background: 'rgba(15,23,42,0.7)', backdropFilter: 'blur(12px)' }}>
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-wrap items-center justify-between gap-3">
            {/* Left: Title + Status */}
            <div className="flex items-center gap-4">
              <div>
                <h1 className="text-lg font-bold tracking-wider" style={{ color: '#e2e8f0', fontFamily: "'JetBrains Mono', 'SF Mono', 'Fira Code', monospace" }}>
                  DATA PIPELINE
                </h1>
                <p className="text-xs mt-0.5 font-mono" style={{ color: '#475569' }}>
                  Real-time chain monitoring &middot; {formatTime(data.timestamp)}
                </p>
              </div>

              <div
                className="px-3 py-1 rounded-full text-xs font-bold tracking-widest"
                style={{ background: badge.bg, color: badge.text }}
              >
                {badge.label}
              </div>
            </div>

            {/* Right: Controls */}
            <div className="flex items-center gap-3">
              {usingMock && (
                <span className="text-xs px-2 py-1 rounded" style={{ background: 'rgba(139,92,246,0.15)', color: '#a78bfa' }}>
                  PROTOTYPE MODE
                </span>
              )}
              <button
                onClick={fetchData}
                className="px-3 py-1.5 rounded text-xs font-mono font-medium transition-all hover:brightness-125"
                style={{
                  background: 'rgba(255,255,255,0.06)',
                  color: '#94a3b8',
                  border: '1px solid rgba(255,255,255,0.08)'
                }}
              >
                REFRESH NOW
              </button>
              <div className="text-xs font-mono px-2 py-1 rounded" style={{ background: 'rgba(255,255,255,0.04)', color: '#475569' }}>
                {countdown}s
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">

          {/* ═══════ SECTION 1: PIPELINE FLOW DIAGRAM ═══════ */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <h2 className="text-xs font-semibold uppercase tracking-widest" style={{ color: '#64748b' }}>
                Pipeline Flow
              </h2>
            </div>

            <div
              className="rounded-xl p-6 overflow-x-auto"
              style={{ background: 'linear-gradient(135deg, rgba(15,23,42,0.9), rgba(17,24,39,0.7))', border: '1px solid rgba(255,255,255,0.05)' }}
            >
              {/* Horizontal pipeline nodes */}
              <div className="flex items-stretch gap-0 min-w-[720px]">
                {PIPELINE_ORDER.map((key, idx) => {
                  const node = data.pipeline[key];
                  if (!node) return null;
                  const lbl = NODE_LABELS[key];
                  const sc = statusColor(node.status);
                  const sbg = statusBg(node.status);

                  return (
                    <React.Fragment key={key}>
                      {/* Node Card */}
                      <div className="flex-1 min-w-[120px]">
                        <div
                          className="h-full rounded-lg p-3 relative transition-all"
                          style={{
                            background: sbg,
                            border: `1.5px solid ${sc}33`,
                            boxShadow: node.status === 'ok'
                              ? `0 0 20px ${sc}10`
                              : node.status === 'error'
                                ? `0 0 20px ${sc}18`
                                : 'none',
                          }}
                        >
                          {/* Status dot — top-right */}
                          <div className="absolute top-2 right-2">
                            <div
                              className="w-2.5 h-2.5 rounded-full"
                              style={{
                                background: sc,
                                boxShadow: node.status === 'ok' ? `0 0 8px ${sc}` : 'none',
                                animation: node.status === 'error' ? 'pulse 1.5s infinite' : undefined,
                              }}
                            />
                          </div>

                          {/* Icon + Name */}
                          <div className="text-base mb-1">{lbl.icon}</div>
                          <div className="font-bold text-sm tracking-wide" style={{ color: '#e2e8f0', fontFamily: "'JetBrains Mono', monospace", fontSize: '13px' }}>
                            {lbl.short}
                          </div>
                          <div className="text-[10px] uppercase tracking-wider mt-0.5" style={{ color: '#475569' }}>
                            {lbl.sub}
                          </div>

                          {/* Status label */}
                          <div
                            className="inline-block mt-2 text-[10px] font-bold px-1.5 py-0.5 rounded"
                            style={{ color: sc, background: `${sc}18` }}
                          >
                            {statusLabel(node.status)}
                          </div>

                          {/* Latency / Detail */}
                          <div className="mt-2 space-y-0.5">
                            {(node.latency_ms ?? node.last_query_ms) != null && (
                              <div className="font-mono text-xs" style={{ color: '#94a3b8' }}>
                                {node.latency_ms != null ? node.latency_ms : node.last_query_ms}<span className="opacity-50">ms</span>
                              </div>
                            )}
                            <div className="font-mono text-[10px] truncate" style={{ color: '#475569', maxWidth: '140px' }} title={node.detail}>
                              {node.detail || '-'}
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Connector arrow (not after last) */}
                      {idx < PIPELINE_ORDER.length - 1 && (
                        <div className="flex items-center px-1 shrink-0">
                          <svg width="24" height="16" viewBox="0 0 24 16" fill="none">
                            <path
                              d="M2 8 H20 M16 4 L20 8 L16 12"
                              stroke={statusColor(data.pipeline[PIPELINE_ORDER[idx + 1]]?.status)}
                              strokeWidth="1.5"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              opacity="0.4"
                            />
                          </svg>
                        </div>
                      )}
                    </React.Fragment>
                  );
                })}
              </div>

              {/* Environment summary strip */}
              <div className="mt-4 pt-3 flex flex-wrap gap-4 text-[11px] font-mono" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                <span style={{ color: '#475569' }}>ENV:</span>
                <span style={{ color: data.env_summary.relay_url_set ? '#10b981' : '#ef4444' }}>
                  RELAY_URL {data.env_summary.relay_url_set ? 'SET' : 'MISSING'}
                </span>
                <span style={{ color: data.env_summary.relay_key_set ? '#10b981' : '#ef4444' }}>
                  RELAY_KEY {data.env_summary.relay_key_set ? 'SET' : 'MISSING'}
                </span>
                <span style={{ color: data.env_summary.proxy_vars > 0 ? '#f59e0b' : '#10b981' }}>
                  PROXY_VARS={data.env_summary.proxy_vars}
                </span>
                <span style={{ color: '#64748b' }}>MODE={data.env_summary.provider_mode}</span>
                {data.query_elapsed_ms != null && (
                  <span style={{ color: '#475569' }}>query {data.query_elapsed_ms}ms</span>
                )}
              </div>
            </div>
          </section>

          {/* ═════ SECTION 2: ALERTS BANNER ═════ */}
          {data.alerts.length > 0 && (
            <section>
              <div className="space-y-2">
                {data.alerts.map((alert, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 rounded-lg p-3 text-sm"
                    style={{
                      background: alert.level === 'error' ? 'rgba(239,68,68,0.08)' : 'rgba(245,158,11,0.08)',
                      borderLeft: `3px solid ${alert.level === 'error' ? '#ef4444' : '#f59e0b'}`,
                    }}
                  >
                    <span className="shrink-0 mt-0.5">{alert.level === 'error' ? '\u26A0\uFE0F' : '\u26A0'}</span>
                    <div>
                      <span className="font-mono text-xs font-bold uppercase mr-2"
                        style={{ color: alert.level === 'error' ? '#fca5a5' : '#fcd34d' }}>
                        [{alert.node}]
                      </span>
                      <span style={{ color: '#cbd5e1' }}>{alert.message}</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* ═════ SECTION 3: REQUEST LOG STREAM ═════ */}
          <section>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                <h2 className="text-xs font-semibold uppercase tracking-widest" style={{ color: '#64748b' }}>
                  Live Request Stream
                </h2>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded" style={{ background: 'rgba(255,255,255,0.04)', color: '#475569' }}>
                  last {Math.min(data.recent_requests.length, 10)} requests
                </span>
              </div>
            </div>

            <div
              ref={logContainerRef}
              className="rounded-xl overflow-hidden"
              style={{ background: 'rgba(0,0,0,0.3)', border: '1px solid rgba(255,255,255,0.05)' }}
            >
              {/* Table header */}
              <div className="grid grid-cols-[70px_1fr_180px_80px_110px] gap-2 px-4 py-2 text-[10px] font-mono uppercase tracking-wider"
                   style={{ background: 'rgba(255,255,255,0.02)', color: '#334155', borderBottom: '1px solid rgba(255,255,255,0.04)' }}
              >
                <span>TIME</span><span>ENDPOINT</span><span>PATH</span><span>STATUS</span><span>DURATION</span>
              </div>

              {/* Log rows */}
              <div className="divide-y" style={{ divideColor: 'rgba(255,255,255,0.03)' }}>
                {data.recent_requests.length > 0 ? (
                  data.recent_requests.map((req, i) => (
                    <div
                      key={i}
                      className="grid grid-cols-[70px_1fr_180px_80px_110px] gap-2 px-4 py-2.5 items-center text-xs font-mono hover:bg-white/[0.02] transition-colors"
                    >
                      <span style={{ color: '#475569' }}>{req.time || '--:--'}</span>
                      <span className="truncate" style={{ color: '#93c5fd' }}>{req.endpoint || '-'}</span>
                      <span className="truncate hidden sm:block" style={{ color: '#475569', fontSize: '11px' }}>{req.path || '-'}</span>
                      <span className="inline-flex items-center gap-1.5">
                        <span
                          className="w-1.5 h-1.5 rounded-full shrink-0"
                          style={{
                            background:
                              req.status === 'ok' ? '#10b981' :
                              req.status === 'warning' ? '#f59e0b' : '#ef4444',
                          }}
                        />
                        <span style={{
                          color:
                            req.status === 'ok' ? '#34d399' :
                            req.status === 'warning' ? '#fbbf24' : '#f87171',
                        }}>
                          {req.status?.toUpperCase() || '?'}
                        </span>
                      </span>
                      <span style={{ color: '#64748b' }}>
                        {req.duration_ms != null ? `${req.duration_ms}ms` : '-'}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="px-4 py-8 text-center text-xs font-mono" style={{ color: '#334155' }}>
                    No requests recorded yet
                  </div>
                )}
              </div>
            </div>
          </section>

          {/* ═════ SECTION 4: NODE DETAIL CARDS ═════ */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <span className="w-1.5 h-1.5 rounded-full bg-violet-400" />
              <h2 className="text-xs font-semibold uppercase tracking-widest" style={{ color: '#64748b' }}>
                Node Details
              </h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {PIPELINE_ORDER.map(key => {
                const node = data.pipeline[key];
                if (!node) return null;
                const lbl = NODE_LABELS[key];
                const sc = statusColor(node.status);

                return (
                  <div
                    key={key}
                    className="rounded-lg p-4 transition-all hover:brightness-110"
                    style={{
                      background: 'rgba(15,23,42,0.6)',
                      border: `1px solid ${sc}22`,
                    }}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span>{lbl.icon}</span>
                        <span className="font-bold text-sm" style={{ color: '#e2e8f0' }}>{lbl.short}</span>
                      </div>
                      <span
                        className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                        style={{ color: sc, background: `${sc}14` }}
                      >
                        {statusLabel(node.status)}
                      </span>
                    </div>
                    <div className="text-[11px] font-mono space-y-1" style={{ color: '#64748b' }}>
                      <div className="flex justify-between">
                        <span>Name</span>
                        <span style={{ color: '#94a3b8' }}>{node.name}</span>
                      </div>
                      {node.version && (
                        <div className="flex justify-between">
                          <span>Version</span>
                          <span style={{ color: '#94a3b8' }}>{node.version}</span>
                        </div>
                      )}
                      {node.data_source && (
                        <div className="flex justify-between">
                          <span>Data Source</span>
                          <span style={{ color: '#94a3b8' }}>{node.data_source}</span>
                        </div>
                      )}
                      {(node.latency_ms ?? node.last_query_ms) != null && (
                        <div className="flex justify-between">
                          <span>Latency</span>
                          <span style={{ color: '#94a3b8' }}>{node.latency_ms ?? node.last_query_ms} ms</span>
                        </div>
                      )}
                      <div className="pt-1 border-t" style={{ borderColor: 'rgba(255,255,255,0.04)' }}>
                        <span style={{ color: '#475569' }}>{node.detail || '-'}</span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          {/* Footer */}
          <div className="pt-4 pb-8 text-center">
            <p className="text-[10px] font-mono" style={{ color: '#1e293b' }}>
              ResearchMate Data Pipeline Monitor &middot; Auto-refresh every {REFRESH_INTERVAL_MS / 1000}s &middot;
              Last update: {lastRefresh?.toLocaleTimeString('zh-CN') ?? '--'}
            </p>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default MonitorPage;
