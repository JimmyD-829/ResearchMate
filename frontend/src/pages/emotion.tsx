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

  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!user) {
      return;
    }
    fetchFollows();
  }, [user]);

  useEffect(() => {
    if (selectedCompany) {
      fetchEmotionData(selectedCompany);
    }
  }, [selectedCompany]);

  const fetchFollows = async () => {
    try {
      const response = await newsApi.getFollows() as any;
      const responseData = response?.data || response;
      const followsData = responseData?.data || responseData || [];
      setFollows(Array.isArray(followsData) ? followsData : []);
      if (Array.isArray(followsData) && followsData.length > 0) {
        setSelectedCompany(followsData[0].company_name);
      }
    } catch (err) {
      console.error('获取关注列表失败');
    }
  };

  const fetchEmotionData = async (company: string) => {
    setLoading(true);
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
        console.error('Empty emotion data received');
        setEmotionScore(null);
        setEmotionTrend(null);
      }
    } catch (err) {
      console.error('获取情绪数据失败:', err);
      setEmotionScore(null);
      setEmotionTrend(null);
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

  if (!user) return null;

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">情绪指标分析</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">跟踪市场情绪变化，辅助投资决策</p>
        </div>

        <ComplianceNote />

        <div className="grid md:grid-cols-4 gap-6">
          <div className="md:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">选择公司</h2>
              {follows.length === 0 ? (
                <p className="text-sm text-gray-600 dark:text-gray-400">暂无关注公司</p>
              ) : (
                <div className="space-y-2">
                  {follows.map((follow) => (
                    <button
                      key={follow.id}
                      onClick={() => setSelectedCompany(follow.company_name)}
                      className={`w-full text-left p-4 rounded-xl transition-colors ${
                        selectedCompany === follow.company_name
                          ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400'
                          : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      <p className="font-semibold">{follow.company_name}</p>
                      {follow.stock_code && (
                        <p className="text-xs text-gray-500 dark:text-gray-400">{follow.stock_code}</p>
                      )}
                    </button>
                  ))}
                </div>
              )}
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
