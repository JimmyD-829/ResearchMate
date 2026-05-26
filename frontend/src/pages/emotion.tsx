import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';
import ComplianceNote from '../components/ComplianceNote';
import { newsApi, emotionApi, Follow, EmotionScore, EmotionTrendResponse } from '../services/api';
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

export default function EmotionPage() {
  const [follows, setFollows] = useState<Follow[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null);
  const [emotionScore, setEmotionScore] = useState<EmotionScore | null>(null);
  const [emotionTrend, setEmotionTrend] = useState<EmotionTrendResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
          setSelectedCompany('平安银行');
        }
      } else {
        setSelectedCompany('平安银行');
      }
    } catch (err) {
      console.error('获取关注列表失败，使用默认公司');
      setSelectedCompany('平安银行');
    }
  };

  const getFallbackEmotionData = () => ({
    score: {
      company_name: selectedCompany || '平安银行',
      current_score: 15.5,
      current_label: 'positive',
      last_7d_avg: 12.3,
      last_30d_avg: 8.7,
      article_count: 156,
      last_updated: new Date().toISOString()
    } as EmotionScore,
    trend: {
      company_name: selectedCompany || '平安银行',
      trend: Array.from({ length: 30 }, (_, i) => ({
        date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        daily_score: Math.sin(i / 5) * 20 + 10 + (Math.random() - 0.5) * 10,
        article_count: Math.floor(Math.random() * 10) + 3
      }))
    } as EmotionTrendResponse
  });

  const fetchEmotionData = async (company: string) => {
    setLoading(true);
    setError(null);
    try {
      const [scoreResponse, trendResponse] = await Promise.all([
        emotionApi.getScore(company),
        emotionApi.getTrend(company, 30),
      ]);
      const scoreResult: any = scoreResponse?.data || scoreResponse;
      const trendResult: any = trendResponse?.data || trendResponse;

      const scoreData = scoreResult?.data || scoreResult;
      const trendData = trendResult?.data || trendResult;

      if (scoreData && trendData) {
        setEmotionScore(scoreData);
        setEmotionTrend(trendData);
      } else {
        console.warn('Empty emotion data received, using fallback');
        const fallback = getFallbackEmotionData();
        setEmotionScore(fallback.score);
        setEmotionTrend(fallback.trend);
        setError('使用示例数据（后端未返回数据）');
      }
    } catch (err: any) {
      console.error('获取情绪数据失败，使用示例数据:', err.message);
      const fallback = getFallbackEmotionData();
      setEmotionScore(fallback.score);
      setEmotionTrend(fallback.trend);
      setError(err.message || '网络连接失败，显示示例数据');
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
    { id: 'default-1', company_name: '平安银行', stock_code: '000001' },
    { id: 'default-2', company_name: '贵州茅台', stock_code: '600519' },
    { id: 'default-3', company_name: '比亚迪', stock_code: '002594' },
    { id: 'default-4', company_name: '腾讯控股', stock_code: '00700' },
    { id: 'default-5', company_name: '宁德时代', stock_code: '300750' },
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
          <div className="mb-6 bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-yellow-800">
                ⚠️ {error}
              </p>
              <button
                onClick={() => selectedCompany && fetchEmotionData(selectedCompany)}
                className="ml-4 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 text-sm font-medium"
              >
                重试
              </button>
            </div>
          </div>
        )}

        <ComplianceNote />

        <div className="grid md:grid-cols-4 gap-6">
          <div className="md:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
                选择公司 {follows.length === 0 && <span className="text-sm text-gray-500">(示例)</span>}
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
                <p className="mt-4 text-gray-600 dark:text-gray-400">加载中...</p>
              </div>
            ) : emotionScore && emotionTrend ? (
              <>
                <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-8">
                  <div className="flex items-center justify-between mb-8">
                    <div>
                      <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">{selectedCompany}</h2>
                      <div className="flex items-center gap-3 mt-3">
                        <span className="text-5xl">{getEmotionIcon(emotionScore.current_label)}</span>
                        <span className={`font-bold text-4xl ${getEmotionTextColor(emotionScore.current_score)}`}>
                          {emotionScore.current_score.toFixed(1)}
                        </span>
                        <span className="text-gray-500 dark:text-gray-400 text-lg">分</span>
                      </div>
                    </div>
                    <div className={`px-6 py-3 rounded-xl ${
                      emotionScore.current_score > 20 ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' :
                      emotionScore.current_score < -20 ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' :
                      'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-400'
                    }`}>
                      <p className="font-bold text-xl">
                        {emotionScore.current_label === 'positive' ? '积极' :
                         emotionScore.current_label === 'negative' ? '消极' : '中性'}
                      </p>
                    </div>
                  </div>

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
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">📈 近30天情绪趋势</h2>
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
