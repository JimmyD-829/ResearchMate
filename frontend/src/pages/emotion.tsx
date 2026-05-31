import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';
import ComplianceNote from '../components/ComplianceNote';
import { newsApi, emotionApi, Follow, EmotionScore, EmotionTrendResponse } from '../services/api';
import { dataCache, getDataFreshnessLabel, getSourceBadge } from '../services/dataCache';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
} from 'chart.js';
import { Line as LineChart } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler
);

interface EmotionMetadata {
  is_real_data: boolean;
  data_source?: string;
  stock_code?: string;
  reasoning?: string;
  indicators?: Record<string, any>;
  realtime_data?: {
    price?: number;
    change_pct?: number;
    volume?: number;
  };
  warning?: string;
}

export default function EmotionPage() {
  const [follows, setFollows] = useState<Follow[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null);
  const [emotionScore, setEmotionScore] = useState<EmotionScore | null>(null);
  const [emotionTrend, setEmotionTrend] = useState<EmotionTrendResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dataSource, setDataSource] = useState<'live' | 'cached' | 'fallback' | null>(null);
  const [dataAge, setDataAge] = useState<number | null>(null);
  
  // V2.0 新增状态
  const [isRealData, setIsRealData] = useState(false);
  const [realSource, setRealSource] = useState<string | null>(null);  // akshare / alpha_vantage
  const [metadata, setMetadata] = useState<EmotionMetadata | null>(null);

  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    fetchFollows();
  }, [user]);

  useEffect(() => {
    if (selectedCompany) {
      fetchEmotionData(selectedCompany);
    }
  }, [selectedCompany]);

  const fetchFollows = async () => {
    try {
      if (user) {
        const response = await newsApi.getFollows() as any;
        const responseData = response?.data || response;
        const followsData = responseData?.data || responseData || [];
        setFollows(Array.isArray(followsData) ? followsData : []);
        if (Array.isArray(followsData) && followsData.length > 0) {
          setSelectedCompany(followsData[0].company_name);
        } else {
          setSelectedCompany('阿里巴巴');
        }
      } else {
        setSelectedCompany('阿里巴巴');
      }
    } catch (err) {
      console.error('获取关注列表失败，使用默认公司');
      setSelectedCompany('阿里巴巴');
    }
  };

  const getFallbackEmotionData = (company: string) => {
    const companyEmotions: Record<string, { score: number; label: string; avg7d: number; avg30d: number; articles: number }> = {
      '平安银行': { score: 18.2, label: 'positive', avg7d: 15.6, avg30d: 12.1, articles: 189 },
      '贵州茅台': { score: 25.8, label: 'positive', avg7d: 22.3, avg30d: 19.5, articles: 234 },
      '比亚迪': { score: 32.1, label: 'positive', avg7d: 28.7, avg30d: 24.3, articles: 312 },
      '腾讯控股': { score: 12.4, label: 'positive', avg7d: 10.2, avg30d: 8.9, articles: 167 },
      '宁德时代': { score: -8.5, label: 'negative', avg7d: -5.2, avg30d: -2.1, articles: 145 },
      '中芯国际': { score: -15.3, label: 'negative', avg7d: -12.1, avg30d: -8.7, articles: 98 },
      '隆基绿能': { score: -22.6, label: 'negative', avg7d: -18.9, avg30d: -14.2, articles: 87 },
      'Microsoft Corp': { score: 28.5, label: 'positive', avg7d: 25.1, avg30d: 21.3, articles: 278 },
      '字节跳动': { score: 5.3, label: 'neutral', avg7d: 3.1, avg30d: 1.8, articles: 156 },
      '阿里巴巴': { score: -3.2, label: 'neutral', avg7d: -1.5, avg30d: 0.8, articles: 201 },
    };

    const defaultEmotion = { score: 8.5, label: 'positive' as const, avg7d: 6.2, avg30d: 4.1, articles: 120 };
    const emotion = companyEmotions[company] || companyEmotions[company.replace(/\s/g, '')] || defaultEmotion;

    const seed = company.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);

    return {
      score: {
        company_name: company,
        current_score: emotion.score,
        current_label: emotion.label,
        last_7d_avg: emotion.avg7d,
        last_30d_avg: emotion.avg30d,
        article_count: emotion.articles,
        last_updated: new Date().toISOString()
      } as EmotionScore,
      trend: {
        company_name: company,
        trend: Array.from({ length: 30 }, (_, i) => ({
          date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          daily_score: Math.sin((i + seed) / 5) * 25 + emotion.avg30d + (Math.random() - 0.5) * 8,
          article_count: Math.floor(Math.random() * 8) + 2
        }))
      } as EmotionTrendResponse
    };
  };

  const fetchEmotionData = async (company: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const cacheKey = `emotion-${company}`;
      const result = await dataCache.fetchWithCache(
        cacheKey,
        async () => {
          // V2.0: 使用新的API端点（支持真实数据）
          const response = await emotionApi.getScore(company);
          
          const result: any = response?.data || response;
          
          // V2.0 API响应格式
          const scoreData = result?.data || result;
          const source = result?.source || 'live';
          const isReal = result?.is_real_data || false;
          const realSource = result?.real_source || null;
          const meta = result?.metadata || {};
          
          // 获取趋势数据
          let trendData: any = null;
          try {
            const trendResponse = await emotionApi.getTrend(company, 30);
            const trendResult: any = trendResponse?.data || trendResponse;
            trendData = trendResult?.data || trendResult;
          } catch (trendErr) {
            console.warn('获取趋势数据失败:', trendErr);
            trendData = { trend: [] };
          }
          
          return { 
            score: scoreData, 
            trend: trendData,
            source,
            isRealData: isReal,
            realSource: realSource,
            metadata: meta
          };
        },
        () => {
          const fallback = getFallbackEmotionData(company);
          return { 
            score: fallback.score, 
            trend: fallback.trend,
            source: 'fallback' as const,
            isRealData: false,
            realSource: null,
            metadata: { is_real_data: false, data_source: 'simulation' }
          };
        }
      );
      
      setEmotionScore(result.data.score);
      setEmotionTrend(result.data.trend);
      
      // V2.0: 设置增强的状态
      setDataSource(result.data.source === 'real' ? 'live' : result.data.source);
      setIsRealData(result.data.isRealData);
      setRealSource(result.data.realSource);
      setMetadata(result.data.metadata);
      
      const age = dataCache.getAgeInSeconds(cacheKey);
      setDataAge(age);
      
      // 根据数据来源设置提示信息
      if (result.data.source === 'fallback') {
        setError('⚠️ 显示示例数据（所有数据源不可用）');
      } else if (!result.data.isRealData && result.data.source !== 'fallback') {
        setError('ℹ️ 显示非实时数据（基于新闻NLP分析）');
      } else if (result.data.isRealData) {
        setError(null);
        console.log(`✅ ${company}: 真实金融数据已加载 (source=${result.data.realSource})`);
      } else {
        setError(null);
      }
    } catch (err: any) {
      console.error('获取情绪数据完全失败:', err.message);
      const fallback = getFallbackEmotionData(company);
      setEmotionScore(fallback.score);
      setEmotionTrend(fallback.trend);
      setDataSource('fallback');
      setIsRealData(false);
      setRealSource(null);
      setMetadata({ is_real_data: false, data_source: 'simulation' });
      setDataAge(0);
      setError('❌ 网络连接失败，显示示例数据');
    } finally {
      setLoading(false);
    }
  };

  const getEmotionIcon = (label: string) => {
    switch (label) {
      case 'positive': return '🟢';
      case 'negative': return '🔴';
      default: return '⚪';
    }
  };

  const getEmotionTextColor = (score: number) => {
    if (score > 20) return 'text-green-600 dark:text-green-400';
    if (score < -20) return 'text-red-600 dark:text-red-400';
    return 'text-gray-600 dark:text-gray-400';
  };

  const chartData = emotionTrend?.trend.map(d => ({
    date: new Date(d.date).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }),
    score: d.daily_score,
    articles: d.article_count,
  })) || [];

  const lineChartData = {
    labels: chartData.map(d => d.date),
    datasets: [
      {
        data: chartData.map(d => d.score),
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        fill: true,
        tension: 0.4,
        pointBackgroundColor: '#3b82f6',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        titleFont: { size: 14 },
        bodyFont: { size: 13 },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: { maxTicksLimit: 7 },
      },
      y: {
        min: -100,
        max: 100,
        grid: { color: 'rgba(0, 0, 0, 0.05)' },
      },
    },
  };

  const defaultCompanies = [
    { id: 'default-1', company_name: '阿里巴巴', stock_code: 'BABA' },
    { id: 'default-2', company_name: '平安银行', stock_code: '000001' },
    { id: 'default-3', company_name: '贵州茅台', stock_code: '600519' },
    { id: 'default-4', company_name: '比亚迪', stock_code: '002594' },
    { id: 'default-5', company_name: '宁德时代', stock_code: '300750' },
    { id: 'default-6', company_name: '腾讯控股', stock_code: '00700.HK' },
  ];

  const displayCompanies = follows.length > 0 ? follows : defaultCompanies;

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">情绪指标分析</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">跟踪市场情绪变化，辅助投资决策</p>
        </div>

        {/* Error/Warning Banner */}
        {error && (
          <div className={`mb-6 border-l-4 p-4 rounded ${
            error.includes('示例数据') ? 'bg-yellow-50 border-yellow-400' :
            error.includes('非实时') ? 'bg-blue-50 border-blue-400' :
            'bg-red-50 border-red-400'
          }`}>
            <div className="flex items-center justify-between">
              <p className={`text-sm font-medium ${
                error.includes('示例数据') ? 'text-yellow-800' :
                error.includes('非实时') ? 'text-blue-800' :
                'text-red-800'
              }`}>
                {error}
              </p>
              <button
                onClick={() => selectedCompany && fetchEmotionData(selectedCompany)}
                className={`ml-4 px-4 py-2 text-white rounded-lg hover:opacity-90 text-sm font-medium ${
                  error.includes('示例数据') ? 'bg-yellow-600' :
                  error.includes('非实时') ? 'bg-blue-600' :
                  'bg-red-600'
                }`}
              >
                刷新数据
              </button>
            </div>
          </div>
        )}

        <ComplianceNote />

        <div className="grid md:grid-cols-4 gap-6">
          <div className="md:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                选择公司 {follows.length === 0 && <span className="text-sm text-gray-500">(默认)</span>}
              </h2>
              <div className="space-y-2">
                {displayCompanies.map((company) => (
                  <button
                    key={company.id}
                    onClick={() => setSelectedCompany(company.company_name)}
                    className={`w-full text-left p-4 rounded-xl transition-colors ${
                      selectedCompany === company.company_name
                        ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400'
                        : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
                    }`}
                  >
                    <p className="font-semibold">{company.company_name}</p>
                    {company.stock_code && (
                      <p className="text-xs text-gray-500 dark:text-gray-400">{company.stock_code}</p>
                    )}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="md:col-span-3 space-y-6">
            {loading ? (
              <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-16 text-center">
                <div className="animate-spin rounded-full h-10 w-10 border-2 border-primary-500 border-t-transparent mx-auto" />
                <p className="mt-4 text-gray-600 dark:text-gray-400">
                  {isRealData ? '正在获取真实金融数据...' : '加载中...'}
                </p>
              </div>
            ) : emotionScore && emotionTrend ? (
              <>
                <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-8">
                  <div className="flex items-start justify-between mb-8">
                    <div>
                      <h2 className="text-2xl font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                        {selectedCompany}
                        {isRealData && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-green-100 text-green-800">
                            ✓ 实时
                          </span>
                        )}
                      </h2>
                      
                      {metadata?.stock_code && (
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                          股票代码: {metadata.stock_code}
                          {realSource && (
                            <span className="ml-2 text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">
                              数据源: {realSource.toUpperCase()}
                            </span>
                          )}
                        </p>
                      )}

                      <div className="flex items-center gap-3 mt-3">
                        <span className="text-5xl">{getEmotionIcon(emotionScore.current_label)}</span>
                        <span className={`font-bold text-4xl ${getEmotionTextColor(emotionScore.current_score)}`}>
                          {emotionScore.current_score.toFixed(1)}
                        </span>
                        <span className="text-gray-500 dark:text-gray-400 text-lg">分</span>
                      </div>

                      {metadata?.reasoning && (
                        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 italic">
                          📊 分析依据: {metadata.reasoning}
                        </p>
                      )}
                    </div>

                    <div className={`px-6 py-3 rounded-xl font-bold text-xl ${
                      emotionScore.current_label === 'positive'
                        ? 'bg-green-500 dark:bg-green-600 text-white shadow-lg shadow-green-500/30'
                        : emotionScore.current_label === 'negative'
                        ? 'bg-red-500 dark:bg-red-600 text-white shadow-lg shadow-red-500/30'
                        : 'bg-yellow-500 dark:bg-yellow-600 text-white shadow-lg shadow-yellow-500/30'
                    }`}>
                      {emotionScore.current_label === 'positive' ? '积极' :
                       emotionScore.current_label === 'negative' ? '消极' : '中性'}
                    </div>
                  </div>

                  {/* V2.0: 数据来源和技术指标展示 */}
                  {(dataSource || metadata) && (
                    <div className="mb-6 space-y-3">
                      {/* 数据来源标签 */}
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className={`px-2 py-1 rounded-md font-medium text-xs ${getSourceBadge(dataSource || 'fallback').className}`}>
                          {getSourceBadge(dataSource || 'fallback').text}
                        </span>
                        
                        {isRealData && realSource && (
                          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-bold bg-green-100 text-green-800">
                            <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                            真实金融数据 ({realSource.toUpperCase()})
                          </span>
                        )}
                        
                        {!isRealData && dataSource !== 'fallback' && (
                          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800">
                            新闻NLP分析
                          </span>
                        )}
                        
                        {dataSource === 'fallback' && (
                          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium bg-orange-100 text-orange-800">
                            ⚠️ 示例模拟数据
                          </span>
                        )}

                        {dataAge !== null && (
                          <span className={`flex items-center gap-1 text-xs ${
                            dataAge < 300 ? 'text-green-500' :
                            dataAge < 1800 ? 'text-yellow-500' : 'text-red-500'
                          }`}>
                            {getDataFreshnessLabel(dataAge).icon} {getDataFreshnessLabel(dataAge).label}
                          </span>
                        )}

                        {/* ❓ Tooltip */}
                        <span className="group relative inline-flex items-center gap-1 text-gray-400 dark:text-gray-500 cursor-help ml-2">
                          <span className="inline-flex items-center justify-center w-4 h-4 text-[10px] font-bold text-white bg-gray-400 dark:bg-gray-500 rounded-full">
                            ?
                          </span>
                          <span className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-80 px-3 py-2 text-xs text-white bg-gray-900 dark:bg-gray-700 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                            <div className="font-semibold mb-2">📊 数据来源说明 (V2.0)</div>
                            <ul className="space-y-1.5 text-left">
                              <li>✅ <strong>实时数据</strong>: AKShare/Alpha Vantage真实股价</li>
                              <li>&nbsp;&nbsp;&nbsp;&nbsp;→ 基于涨跌幅、波动率、RSI、MA等量化指标计算</li>
                              <li>📰 <strong>新闻NLP</strong>: 数据库中的新闻情绪分析结果</li>
                              <li>⚠️ <strong>示例数据</strong>: 所有数据源不可用时的模拟数据</li>
                            </ul>
                            <div className="mt-2 pt-2 border-t border-gray-600 text-[10px] text-gray-300">
                              💡 当前状态: {isRealData ? '✓ 已接入真实金融数据' : dataSource === 'fallback' ? '⚠️ 示例模式' : 'ℹ️ 非实时'}
                              <br/>
                              {isRealData && `🔗 数据源: ${realSource?.toUpperCase()}`}
                            </div>
                            <span className="absolute top-full left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900 dark:border-t-gray-700"></span>
                          </span>
                        </span>
                      </div>

                      {/* 技术指标详情 */}
                      {isRealData && metadata?.indicators && Object.keys(metadata.indicators).length > 0 && (
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                          {Object.entries(metadata.indicators).map(([key, value]) => (
                            <div key={key} className="text-center">
                              <p className="text-[10px] text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                {key.replace(/_/g, ' ')}
                              </p>
                              <p className="text-sm font-bold text-gray-900 dark:text-white">
                                {typeof value === 'number' ? value.toFixed(1) : String(value)}
                              </p>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* 实时行情快照 */}
                      {isRealData && metadata?.realtime_data && (
                        <div className="flex items-center gap-4 p-3 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg text-sm">
                          <span className="font-semibold text-gray-700 dark:text-gray-300">💹 实时行情:</span>
                          {metadata.realtime_data.price && (
                            <span className="text-gray-900 dark:text-white font-mono">
                              ¥{metadata.realtime_data.price.toFixed(2)}
                            </span>
                          )}
                          {metadata.realtime_data.change_pct !== undefined && (
                            <span className={`font-mono ${Number(metadata.realtime_data.change_pct) >= 0 ? 'text-red-600' : 'text-green-600'}`}>
                              {Number(metadata.realtime_data.change_pct) >= 0 ? '+' : ''}{metadata.realtime_data.change_pct.toFixed(2)}%
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  <div className="grid grid-cols-3 gap-5">
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-5 text-center">
                      <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">近7日平均</p>
                      <p className={`text-3xl font-bold ${getEmotionTextColor(emotionScore.last_7d_avg)}`}>
                        {emotionScore.last_7d_avg.toFixed(1)}
                      </p>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-5 text-center">
                      <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">近30日平均</p>
                      <p className={`text-3xl font-bold ${getEmotionTextColor(emotionScore.last_30d_avg)}`}>
                        {emotionScore.last_30d_avg.toFixed(1)}
                      </p>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-5 text-center">
                      <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">趋势判断</p>
                      <p className={`text-2xl font-bold ${
                        emotionScore.current_score > emotionScore.last_7d_avg
                          ? 'text-green-600 dark:text-green-400'
                          : emotionScore.current_score < emotionScore.last_7d_avg
                          ? 'text-red-600 dark:text-red-400'
                          : 'text-gray-600 dark:text-gray-400'
                      }`}>
                        {emotionScore.current_score > emotionScore.last_7d_avg ? '↑ 上升' :
                         emotionScore.current_score < emotionScore.last_7d_avg ? '↓ 下降' : '→ 持平'}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-8">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6 flex items-center gap-2">
                    📈 近30天情绪趋势
                    {isRealData && (
                      <span className="text-xs font-normal text-green-600">(基于真实股价)</span>
                    )}
                  </h2>
                  <div className="h-80">
                    <LineChart data={lineChartData} options={chartOptions} />
                  </div>
                </div>
              </>
            ) : (
              <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-16 text-center">
                <span className="text-5xl">📈</span>
                <p className="mt-4 text-gray-600 dark:text-gray-400">暂无情绪数据</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
