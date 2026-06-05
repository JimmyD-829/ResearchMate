'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import dynamic from 'next/dynamic';
import { investApi } from '../services/api';
import Layout from '../components/Layout';

// 动态导入K线组件（避免SSR问题）
const KLineChart = dynamic(() => import('../components/KLineChart'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-[420px] bg-gray-900 rounded-xl">
      <div className="text-gray-500 text-sm">加载图表...</div>
    </div>
  ),
});

// ── 类型定义 ──
interface IndicatorData {
  indicators?: {
    ma?: { ma5?: number | null; ma10?: number | null; ma20?: number | null; ma60?: number | null;
            series_5?: number[]; series_10?: number[]; series_20?: number[]; series_60?: number[] };
    macd?: { dif?: number | null; dea?: number | null; histogram?: number | null;
              series_dif?: number[]; series_dea?: number[]; series_hist?: number[] };
    rsi?: { value?: number | null; series?: number[] };
    kdj?: { k?: number | null; d?: number | null; j?: number | null;
             series_k?: number[]; series_d?: number[]; series_j?: number[] };
    boll?: { upper?: number | null; mid?: number | null; lower?: number | null; bandwidth?: number | null;
              series_upper?: number[]; series_mid?: number[]; series_lower?: number[] };
  };
  signals?: {
    ma?: { signal: string; description: string } | { signal: string; index: number | null; description: string };
    macd?: { signal: string; description: string; histogram_trend?: string };
    rsi?: { signal: string; value?: number | null; description: string };
    kdj?: { signal: string; description: string; values?: { K?: number | null; D?: number | null; J?: number | null } };
    boll?: { signal: string; description: string; bandwidth?: number | null };
  };
  risk?: {
    period_returns?: Record<string, number>;
    total_return_pct?: number;
    max_drawdown_pct?: number;
    annualized_volatility?: number;
    annualized_return_pct?: number;
    sharpe_ratio?: number;
    risk_level?: string;
    max_up_streak?: number;
    max_down_streak?: number;
  };
  metadata?: { symbol: string; kline_count: number; update_time: string };
}

interface OverviewData {
  symbol: string;
  market: string;
  quote?: Record<string, any>;
  indicators?: IndicatorData;
  company?: Record<string, any>;
  risk?: IndicatorData['risk'];
}

// ── 热门股票列表 ──
const HOT_STOCKS = [
  // A股
  { code: '600519', name: '贵州茅台', market: 'CN' },
  { code: '000858', name: '五粮液', market: 'CN' },
  { code: '300750', name: '宁德时代', market: 'CN' },
  { code: '601318', name: '中国平安', market: 'CN' },
  { code: '600036', name: '招商银行', market: 'CN' },
  { code: '000333', name: '美的集团', market: 'CN' },
  { code: '002594', name: '比亚迪', market: 'CN' },
  { code: '601012', name: '隆基绿能', market: 'CN' },
  // 美股
  { code: 'AAPL', name: 'Apple 苹果', market: 'US' },
  { code: 'TSLA', name: 'Tesla 特斯拉', market: 'US' },
  { code: 'MSFT', name: 'Microsoft 微软', market: 'US' },
  { code: 'NVDA', name: 'NVIDIA 英伟达', market: 'US' },
  { code: 'GOOGL', name: 'Google 谷歌', market: 'US' },
  { code: 'AMZN', name: 'Amazon 亚马逊', market: 'US' },
  { code: 'META', name: 'Meta 平台', market: 'US' },
];

// ── 信号颜色映射 ──
function signalColor(signal: string): string {
  if (signal.includes('golden') || signal === 'oversold' || signal === 'extreme_oversold') return '#10b981';
  if (signal.includes('death') || signal === 'overbought' || signal === 'extreme_overbought') return '#ef4444';
  if (signal === 'none' || signal === 'neutral' || signal === 'normal') return '#64748b';
  return '#f59e0b';
}

function signalLabel(signal: string): string {
  const map: Record<string, string> = {
    golden_cross: '金叉',
    death_cross: '死叉',
    overbought: '超买',
    extreme_overbought: '极端超买',
    oversold: '超卖',
    extreme_oversold: '极端超卖',
    neutral: '中性',
    none: '无信号',
    normal: '正常',
    touch_band: '触及轨道',
    bandwidth_squeeze: '带宽收窄',
    j_overbought: 'J超买',
    j_oversold: 'J超卖',
    red_column_growing: '红柱增长',
    green_column_growing: '绿柱增长',
  };
  return map[signal] || signal;
}

function riskLevelColor(level: string): string {
  switch (level) {
    case 'high': return '#ef4444';
    case 'medium': return '#f59e0b';
    case 'low': return '#10b981';
    default: return '#64748b';
  }
}

function riskLevelLabel(level: string): string {
  switch (level) {
    case 'high': return '高风险';
    case 'medium': return '中风险';
    case 'low': return '低风险';
    default: return '未知';
  }
}

export default function InvestPage() {
  const [symbol, setSymbol] = useState('600519');
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [klineData, setKlineData] = useState<Array<{
    date: string; open: number; high: number; low: number; close: number; volume: number;
  }>>([]);

  // 搜索相关状态
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearchResults, setShowSearchResults] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);

  // 当前选中的股票信息
  const currentStock = HOT_STOCKS.find(s => s.code === symbol);
  const isUSStock = currentStock?.market === 'US';

  // 过滤搜索结果
  const filteredStocks = HOT_STOCKS.filter(s =>
    s.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // 选择股票
  const selectStock = (code: string) => {
    setSymbol(code);
    setSearchQuery('');
    setShowSearchResults(false);
    fetchData(code);
  };

  // 获取数据
  const fetchData = useCallback(async (sym: string) => {
    setLoading(true);
    setError('');
    try {
      const res = await investApi.getOverview(sym) as any;
      const wrapped = res?.data || res;
      // 解包 API 响应 {success, data: {quote, indicators, risk}} → 直接使用内层数据
      const overview = wrapped?.data || wrapped;
      setData(overview);

      // 提取K线数据（从indicators的metadata或单独获取）
      if (overview?.indicators) {
        // 需要从history接口单独拿K线数据用于图表（使用完整后端URL，避免静态部署时相对路径问题）
        const historyRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://researchmate-aznu.onrender.com'}/api/data/history/${sym}?days=120&adjust=qfq`);
        const histData = await historyRes.json();
        if (histData?.success && histData.data) {
          const records: any[] = Array.isArray(histData.data) ? histData.data : [];
          const bars = records.map((r: any) => ({
            date: typeof r.日期 === 'string'
              ? r.日期.split('T')[0].split(' ')[0]
              : new Date(r.日期).toISOString().split('T')[0],
            open: parseFloat(r.开盘),
            high: parseFloat(r.最高),
            low: parseFloat(r.最低),
            close: parseFloat(r.收盘),
            volume: parseFloat(r.成交量 || 0),
          })).reverse();
          setKlineData(bars);
        }
      }
    } catch (err: any) {
      setError(err.message || '获取数据失败');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData(symbol);
  }, [symbol, fetchData]);

  const overviewIndicators = data?.indicators;
  const sig = overviewIndicators?.signals;
  const risk = data?.risk || overviewIndicators?.risk;
  const quote = data?.quote;

  return (
    <Layout>
    <div className="min-h-screen bg-slate-950 text-white p-4 md:p-6">
      {/* ══ Header ══ */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight" style={{ fontFamily: "'JetBrains Mono', monospace" }}>
              投资分析
            </h1>
            <p className="text-sm text-slate-500 mt-1">中长期投资分析面板 — A股 & 美股</p>
          </div>

          {/* 搜索选股器 */}
          <div className="flex items-center gap-2 relative">
            <div className="relative">
              <input
                ref={searchRef}
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setShowSearchResults(e.target.value.length > 0);
                }}
                onFocus={() => setShowSearchResults(searchQuery.length > 0 || true)}
                onBlur={() => setTimeout(() => setShowSearchResults(false), 200)}
                placeholder="搜索股票代码或名称..."
                className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 pl-9 text-sm font-mono w-64
                           focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 placeholder-slate-600"
              />
              <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>

              {/* 搜索结果下拉 */}
              {showSearchResults && (
                <div className="absolute top-full mt-1 w-full bg-slate-900 border border-slate-700 rounded-lg shadow-xl z-50 max-h-64 overflow-y-auto">
                  {filteredStocks.length > 0 ? (
                    <>
                      {/* A股分组 */}
                      {filteredStocks.filter(s => s.market === 'CN').length > 0 && (
                        <>
                          <div className="px-3 py-1.5 text-[10px] font-semibold text-slate-500 uppercase tracking-wider bg-slate-800/50 sticky top-0">
                            A股
                          </div>
                          {filteredStocks.filter(s => s.market === 'CN').map((s) => (
                            <button
                              key={s.code}
                              onMouseDown={() => selectStock(s.code)}
                              className={`w-full px-3 py-2 text-left text-sm hover:bg-indigo-500/10 transition-colors flex items-center justify-between ${
                                symbol === s.code ? 'bg-indigo-500/20 text-indigo-300' : 'text-slate-300'
                              }`}
                            >
                              <span>
                                <span className="font-mono font-bold">{s.code}</span>
                                <span className="ml-2 text-slate-400">{s.name}</span>
                              </span>
                            </button>
                          ))}
                        </>
                      )}
                      {/* 美股分组 */}
                      {filteredStocks.filter(s => s.market === 'US').length > 0 && (
                        <>
                          <div className="px-3 py-1.5 text-[10px] font-semibold text-slate-500 uppercase tracking-wider bg-slate-800/50 sticky top-0">
                            美股 (US)
                          </div>
                          {filteredStocks.filter(s => s.market === 'US').map((s) => (
                            <button
                              key={s.code}
                              onMouseDown={() => selectStock(s.code)}
                              className={`w-full px-3 py-2 text-left text-sm hover:bg-indigo-500/10 transition-colors flex items-center justify-between ${
                                symbol === s.code ? 'bg-indigo-500/20 text-indigo-300' : 'text-slate-300'
                              }`}
                            >
                              <span>
                                <span className="font-mono font-bold">{s.code}</span>
                                <span className="ml-2 text-slate-400">{s.name}</span>
                              </span>
                              <span className={`text-[10px] px-1.5 py-0.5 rounded ${s.market === 'US' ? 'bg-emerald-500/15 text-emerald-400' : ''}`}>
                                US
                              </span>
                            </button>
                          ))}
                        </>
                      )}
                    </>
                  ) : (
                    <div className="px-3 py-4 text-center text-sm text-slate-500">未找到匹配的股票</div>
                  )}
                </div>
              )}
            </div>

            {/* 当前选中标签 */}
            {currentStock && (
              <span className={`text-xs px-2 py-1 rounded-md font-mono flex items-center gap-1 ${
                isUSStock ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20'
                         : 'bg-blue-500/15 text-blue-400 border border-blue-500/20'
              }`}>
                {symbol} · {currentStock.name}
                <span className="text-[9px] opacity-60">{isUSStock ? '美股' : 'A股'}</span>
              </span>
            )}

            <button
              onClick={() => fetchData(symbol)}
              disabled={loading}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50
                         rounded-lg text-sm font-medium transition-colors"
            >
              {loading ? '分析中...' : '刷新'}
            </button>
          </div>
        </div>

        {/* 实时行情条 */}
        {quote && (
          <div className="mt-4 flex flex-wrap items-center gap-4 px-4 py-3 rounded-xl"
               style={{ background: 'linear-gradient(135deg, rgba(30,41,59,0.8), rgba(15,23,42,0.6))', border: '1px solid rgba(255,255,255,0.05)' }}>
            <span className="text-xs uppercase tracking-wider text-slate-500">{symbol}</span>
            <span className="text-xl font-bold font-mono">
              {quote.price ? `¥${parseFloat(quote.price).toFixed(2)}` : '-'}
            </span>
            {quote.change_pct != null && (
              <span className={`text-sm font-mono px-2 py-0.5 rounded ${parseFloat(quote.change_pct) >= 0 ? 'text-emerald-400 bg-emerald-400/10' : 'text-red-400 bg-red-400/10'}`}>
                {parseFloat(quote.change_pct) >= 0 ? '+' : ''}{parseFloat(quote.change_pct).toFixed(2)}%
              </span>
            )}
            <span className="text-xs text-slate-500 font-mono">
              成交额: {quote.volume || quote.turnover || '-'}
            </span>
            {overviewIndicators?.metadata && (
              <span className="text-xs text-slate-600 ml-auto font-mono">
                K线{overviewIndicators?.metadata?.kline_count}根 · 更新于 {new Date(overviewIndicators?.metadata?.update_time || '').toLocaleTimeString()}
              </span>
            )}
          </div>
        )}
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="max-w-7xl mx-auto mb-4 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* ══ 主内容区：上2下2 布局 ══ */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-4">

        {/* ─── 左侧：K线图（占8列）─── */}
        <div className="lg:col-span-8 space-y-4">
          <section
            className="rounded-xl overflow-hidden"
            style={{ background: 'linear-gradient(135deg, rgba(15,23,42,0.95), rgba(17,24,39,0.8))', border: '1px solid rgba(255,255,255,0.05)' }}
          >
            <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <h2 className="text-xs font-semibold uppercase tracking-widest text-slate-500">
                  K-Line Chart
                </h2>
              </div>
              <div className="flex items-center gap-3 text-[10px] font-mono text-slate-600">
                <span className="flex items-center gap-1"><span className="w-2 h-0.5 bg-amber-500 inline-block"/>MA5</span>
                <span className="flex items-center gap-1"><span className="w-2 h-0.5 bg-blue-500 inline-block"/>MA10</span>
                <span className="flex items-center gap-1"><span className="w-2 h-0.5 bg-purple-500 inline-block"/>MA20</span>
                <span className="flex items-center gap-1"><span className="w-2 h-0.5 bg-pink-500 inline-block"/>MA60</span>
              </div>
            </div>
            <div className="p-2">
              {klineData.length > 0 ? (
                <KLineChart
                  data={klineData}
                  maLines={{
                    ma5: overviewIndicators?.indicators?.ma?.series_5,
                    ma10: overviewIndicators?.indicators?.ma?.series_10,
                    ma20: overviewIndicators?.indicators?.ma?.series_20,
                    ma60: overviewIndicators?.indicators?.ma?.series_60,
                  }}
                  height={420}
                />
              ) : (
                <div className="flex items-center justify-center h-[420px] text-slate-600 text-sm">
                  {loading ? '加载数据中...' : '请选择股票开始分析'}
                </div>
              )}
            </div>
          </section>

          {/* ─── 技术指标卡片组 ─── */}
          <section
            className="rounded-xl p-4"
            style={{ background: 'linear-gradient(135deg, rgba(15,23,42,0.95), rgba(17,24,39,0.8))', border: '1px solid rgba(255,255,255,0.05)' }}
          >
            <div className="flex items-center gap-2 mb-4">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
              <h2 className="text-xs font-semibold uppercase tracking-widest text-slate-500">
                Technical Indicators
              </h2>
            </div>

            {!overviewIndicators ? (
              <div className="text-slate-600 text-sm text-center py-8">等待数据...</div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {/* MA */}
                <IndicatorCard
                  title="MA均线"
                  subtitle={`${overviewIndicators.indicators?.ma?.ma20 ?? '-'}`}
                  signal={sig?.ma}
                  detail={`MA5=${overviewIndicators.indicators?.ma?.ma5} MA10=${overviewIndicators.indicators?.ma?.ma10} MA60=${overviewIndicators.indicators?.ma?.ma60}`}
                />
                {/* MACD */}
                <IndicatorCard
                  title="MACD"
                  subtitle={`DIF:${overviewIndicators.indicators?.macd?.dif != null ? overviewIndicators.indicators.macd.dif.toFixed(2) : '-'}`}
                  signal={sig?.macd}
                  detail={`DEA=${overviewIndicators.indicators?.macd?.dea != null ? overviewIndicators.indicators.macd.dea.toFixed(2) : '-'} 柱=${overviewIndicators.indicators?.macd?.histogram != null ? overviewIndicators.indicators.macd.histogram.toFixed(2) : '-'}`}
                />
                {/* RSI */}
                <IndicatorCard
                  title="RSI(14)"
                  subtitle={`${overviewIndicators.indicators?.rsi?.value != null ? overviewIndicators.indicators.rsi.value.toFixed(1) : '-'}`}
                  signal={sig?.rsi}
                  detail={sig?.rsi?.description || ''}
                />
                {/* KDJ */}
                <IndicatorCard
                  title="KDJ(9,3,3)"
                  subtitle={`K=${overviewIndicators.indicators?.kdj?.k ?? '-'} D=${overviewIndicators.indicators?.kdj?.d ?? '-'}`}
                  signal={sig?.kdj}
                  detail={`J=${overviewIndicators.indicators?.kdj?.j ?? '-'} ${sig?.kdj?.description || ''}`}
                />
                {/* BOLL */}
                <IndicatorCard
                  title="BOLL(20,2)"
                  subtitle={`带宽${overviewIndicators.indicators?.boll?.bandwidth != null ? overviewIndicators.indicators.boll.bandwidth.toFixed(1) : '-'}%`}
                  signal={sig?.boll}
                  detail={`UP=${overviewIndicators.indicators?.boll?.upper != null ? overviewIndicators.indicators.boll.upper.toFixed(2) : '-'} LO=${overviewIndicators.indicators?.boll?.lower != null ? overviewIndicators.indicators.boll.lower.toFixed(2) : '-'}`}
                />
              </div>
            )}
          </section>
        </div>

        {/* ─── 右侧：基本面 + 风险（占4列）─── */}
        <div className="lg:col-span-4 space-y-4">
          {/* 基本面概览 */}
          <section
            className="rounded-xl p-4"
            style={{ background: 'linear-gradient(135deg, rgba(15,23,42,0.95), rgba(17,24,39,0.8))', border: '1px solid rgba(255,255,255,0.05)' }}
          >
            <div className="flex items-center gap-2 mb-4">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse" />
              <h2 className="text-xs font-semibold uppercase tracking-widest text-slate-500">
                Fundamentals
              </h2>
            </div>

            {quote ? (
              <div className="space-y-3">
                <FundRow label="PE(TTM)" value={quote.pe_ratio} highlight />
                <FundRow label="PB" value={quote.pb_ratio} />
                <FundRow label="总市值" value={quote.market_cap} />
                <FundRow label="流通市值" value={quote.float_market_cap || quote.circulating_mv} />
                <FundRow label="52周最高" value={quote.high_52w || quote.year_high} />
                <FundRow label="52周最低" value={quote.low_52w || quote.year_low} />
              </div>
            ) : (
              <div className="text-slate-600 text-sm text-center py-4">暂无基本面数据</div>
            )}

            {/* AI 解读（如果有） */}
            {quote && (
              <div className="mt-4 pt-3" style={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                <p className="text-[11px] text-slate-600 leading-relaxed">
                  {(() => {
                    const pe = parseFloat(quote.pe_ratio || quote.pe || '0');
                    if (pe > 0 && pe < 15) return `PE=${pe.toFixed(1)}，估值偏低，具备一定安全边际。`;
                    if (pe >= 15 && pe < 30) return `PE=${pe.toFixed(1)}，估值处于合理区间。`;
                    if (pe >= 30 && pe < 50) return `PE=${pe.toFixed(1)}，估值偏高，需关注业绩支撑。`;
                    if (pe >= 50) return `PE=${pe.toFixed(1)}，高估值区域，注意回调风险。`;
                    return '等待更多基本面数据...';
                  })()}
                </p>
              </div>
            )}
          </section>

          {/* 风险分析面板 */}
          <section
            className="rounded-xl p-4"
            style={{ background: 'linear-gradient(135deg, rgba(15,23,42,0.95), rgba(17,24,39,0.8))', border: '1px solid rgba(255,255,255,0.05)' }}
          >
            <div className="flex items-center gap-2 mb-4">
              <span className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse" />
              <h2 className="text-xs font-semibold uppercase tracking-widest text-slate-500">
                Risk Analysis
              </h2>
              {risk?.risk_level && (
                <span
                  className="ml-auto text-[10px] font-bold px-2 py-0.5 rounded"
                  style={{ color: riskLevelColor(risk.risk_level), background: `${riskLevelColor(risk.risk_level)}18` }}
                >
                  {riskLevelLabel(risk.risk_level)}
                </span>
              )}
            </div>

            {risk ? (
              <>
                {/* 区间收益 */}
                <div className="mb-4">
                  <div className="text-[10px] text-slate-600 uppercase tracking-wider mb-2">区间收益</div>
                  <div className="grid grid-cols-4 gap-2">
                    {(['1M', '3M', '6M', '1Y'] as const).map((period) => {
                      const val = risk.period_returns?.[period];
                      const isPos = val !== undefined && val > 0;
                      return (
                        <div key={period} className="text-center p-2 rounded-lg" style={{ background: 'rgba(255,255,255,0.02)' }}>
                          <div className="text-[10px] text-slate-600">{period}</div>
                          <div className={`text-sm font-mono font-bold ${isPos ? 'text-emerald-400' : val !== undefined ? 'text-red-400' : 'text-slate-600'}`}>
                            {val != null ? `${val > 0 ? '+' : ''}${val}%` : '-'}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* 风险指标网格 */}
                <div className="space-y-2">
                  <RiskRow label="最大回撤" value={`${risk.max_drawdown_pct}%`} warn={!!(risk.max_drawdown_pct && risk.max_drawdown_pct > 25)} />
                  <RiskRow label="年化波动率" value={`${risk.annualized_volatility}%`} warn={!!(risk.annualized_volatility && risk.annualized_volatility > 35)} />
                  <RiskRow label="年化收益" value={`${risk.annualized_return_pct}%`} isReturn />
                  <RiskRow label="夏普比率" value={`${risk.sharpe_ratio}`} warn={!!(risk.sharpe_ratio != null && risk.sharpe_ratio < 0)} />
                  <RiskRow label="最长连涨" value={`${risk.max_up_streak}天`} />
                  <RiskRow label="最长连跌" value={`${risk.max_down_streak}天`} warn={!!(risk.max_down_streak && risk.max_down_streak > 10)} />
                </div>
              </>
            ) : (
              <div className="text-slate-600 text-sm text-center py-4">暂无风险数据</div>
            )}
          </section>

          {/* 综合建议 */}
          <section
            className="rounded-xl p-4"
            style={{ background: 'linear-gradient(135deg, rgba(30,27,75,0.6), rgba(15,23,42,0.8))', border: '1px solid rgba(99,102,241,0.15)' }}
          >
            <div className="flex items-center gap-2 mb-3">
              <span className="text-base">&#x1F9E0;</span>
              <h2 className="text-xs font-semibold uppercase tracking-widest text-indigo-400">
                AI Insight
              </h2>
            </div>
            <div className="text-xs text-slate-400 leading-relaxed space-y-2">
              {sig ? (
                <>
                  <p><strong className="text-slate-300">技术面：</strong>{sig.ma?.description || sig.macd?.description || '无明显信号'}</p>
                  <p><strong className="text-slate-300">动量：</strong>{sig.rsi?.description || '-'}</p>
                  <p><strong className="text-slate-300">波动：</strong>{sig.boll?.description || '-'}</p>
                  {risk?.risk_level && (
                    <p><strong className="text-slate-300">风控：</strong>综合风险等级为<span style={{ color: riskLevelColor(risk.risk_level) }}> {riskLevelLabel(risk.risk_level)}</span>，
                      最大回撤{risk.max_drawdown_pct}%，
                      {risk.sharpe_ratio != null && risk.sharpe_ratio > 1 ? '夏普比率表现良好' : '需关注风险调整后收益'}
                    </p>
                  )}
                  <p className="pt-2" style={{ borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                    <span className="text-slate-600 text-[10px]">* 以上分析基于历史数据计算，不构成投资建议。</span>
                  </p>
                </>
              ) : (
                <p className="text-slate-600">选择股票后显示综合分析...</p>
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
    </Layout>
  );
}

// ── 子组件：指标卡片 ──
function IndicatorCard({ title, subtitle, signal, detail }: {
  title: string;
  subtitle: string;
  signal?: { signal: string; description: string } | { signal: string; index: number | null; description: string; histogram_trend?: string } | { signal: string; value?: number | null; description: string } | { signal: string; description: string; values?: any; bandwidth?: number | null };
  detail: string;
}) {
  const sigKey = typeof signal?.signal === 'string' ? signal.signal : 'none';
  const sc = signalColor(sigKey);

  return (
    <div
      className="p-3 rounded-lg transition-all hover:bg-white/[0.02]"
      style={{ background: 'rgba(255,255,255,0.02)', border: `1px solid rgba(255,255,255,0.04)` }}
    >
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">{title}</span>
        {signal && (
          <span
            className="text-[9px] font-bold px-1.5 py-0.5 rounded"
            style={{ color: sc, background: `${sc}18` }}
          >
            {signalLabel(sigKey)}
          </span>
        )}
      </div>
      <div className="font-mono text-sm font-bold text-slate-200">{subtitle}</div>
      <div className="text-[10px] text-slate-600 mt-1 truncate" title={detail}>{detail}</div>
    </div>
  );
}

// ── 子组件：基本面行 ──
function FundRow({ label, value, highlight }: { label: string; value: any; highlight?: boolean }) {
  return (
    <div className="flex items-center justify-between py-1.5" style={{ borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
      <span className="text-xs text-slate-500">{label}</span>
      <span className={`text-sm font-mono ${highlight ? 'text-indigo-300 font-bold' : 'text-slate-300'}`}>
        {value ?? '-'}
      </span>
    </div>
  );
}

// ── 子组件：风险指标行 ──
function RiskRow({ label, value, warn, isReturn }: { label: string; value: string; warn?: boolean; isReturn?: boolean }) {
  return (
    <div className="flex items-center justify-between py-1.5" style={{ borderBottom: '1px solid rgba(255,255,255,0.02)' }}>
      <span className="text-xs text-slate-500">{label}</span>
      <span className={`text-sm font-mono ${
        isReturn ? (value.startsWith('+') || (!value.startsWith('-') && parseFloat(value.replace('%','')) > 0) ? 'text-emerald-400' : 'text-red-400')
        : warn ? 'text-red-400' : 'text-slate-300'
      }`}>
        {value}
      </span>
    </div>
  );
}
