import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';
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
import { Line } from 'react-chartjs-2';

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
  const chartRef = useRef<ChartJS<'line'>>(null);

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }
    fetchFollows();
  }, [user, router]);

  useEffect(() => {
    if (selectedCompany) {
      fetchEmotionData(selectedCompany);
    }
  }, [selectedCompany]);

  const fetchFollows = async () => {
    try {
      const response = await newsApi.getFollows();
      setFollows(response.data);
      if (response.data.length > 0) {
        setSelectedCompany(response.data[0].company_name);
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
      setEmotionScore(scoreResponse.data);
      setEmotionTrend(trendResponse.data);
    } catch (err) {
      console.error('获取情绪数据失败');
    } finally {
      setLoading(false);
    }
  };

  const getEmotionIcon = (label: string) => {
    switch (label) {
      case 'positive': return '🟢';
      case 'negative': return '🔴';
      default: return '⚪️';
    }
  };

  const getEmotionBgColor = (score: number) => {
    if (score > 20) return 'bg-green-100';
    if (score < -20) return 'bg-red-100';
    return 'bg-gray-100';
  };

  const getEmotionTextColor = (score: number) => {
    if (score > 20) return 'text-green-700';
    if (score < -20) return 'text-red-700';
    return 'text-gray-700';
  };

  const chartData = emotionTrend?.trend.map(d => ({
    date: new Date(d.date).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }),
    score: d.daily_score,
    articles: d.article_count,
  })) || [];

  const chartOptions = {
    responsive: true,
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
    elements: {
      point: { radius: 4, hoverRadius: 6 },
      line: { tension: 0.4 },
    },
  };

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

  if (!user) return null;

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">情绪指标分析</h1>
            <p className="text-gray-500 mt-1">追踪市场情绪变化，辅助投资决策</p>
          </div>
        </div>

        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <div className="md:col-span-1">
            <div className="bg-white rounded-xl shadow-lg p-4">
              <h3 className="text-sm font-medium text-gray-500 mb-3">选择公司</h3>
              {follows.length === 0 ? (
                <p className="text-sm text-gray-400">暂无关注公司</p>
              ) : (
                <div className="space-y-2">
                  {follows.map((follow) => (
                    <button
                      key={follow.id}
                      onClick={() => setSelectedCompany(follow.company_name)}
                      className={`w-full text-left p-3 rounded-lg transition ${
                        selectedCompany === follow.company_name
                          ? 'bg-primary-100 text-primary-700 font-medium'
                          : 'hover:bg-gray-100 text-gray-700'
                      }`}
                    >
                      <p>{follow.company_name}</p>
                      {follow.stock_code && (
                        <p className="text-xs text-gray-500">{follow.stock_code}</p>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="md:col-span-3">
            {loading ? (
              <div className="bg-white rounded-xl shadow-lg p-16 text-center">
                <div className="animate-spin rounded-full h-10 w-10 border-4 border-primary-400 border-t-transparent mx-auto"></div>
                <p className="mt-4 text-gray-500">加载中...</p>
              </div>
            ) : emotionScore && emotionTrend ? (
              <>
                <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h2 className="text-xl font-semibold text-gray-800">{selectedCompany}</h2>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-2xl">{getEmotionIcon(emotionScore.current_label)}</span>
                        <span className={`font-bold text-2xl ${getEmotionTextColor(emotionScore.current_score)}`}>
                          {emotionScore.current_score.toFixed(1)}
                        </span>
                        <span className="text-sm text-gray-500">分</span>
                      </div>
                    </div>
                    <div className={`px-4 py-2 rounded-lg ${getEmotionBgColor(emotionScore.current_score)}`}>
                      <p className={`font-medium ${getEmotionTextColor(emotionScore.current_score)}`}>
                        {emotionScore.current_label === 'positive' ? '积极' :
                         emotionScore.current_label === 'negative' ? '消极' : '中性'}
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <p className="text-xs text-gray-500 mb-1">近7日平均</p>
                      <p className={`font-bold ${getEmotionTextColor(emotionScore.last_7d_avg)}`}>
                        {emotionScore.last_7d_avg.toFixed(1)}
                      </p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <p className="text-xs text-gray-500 mb-1">近30日平均</p>
                      <p className={`font-bold ${getEmotionTextColor(emotionScore.last_30d_avg)}`}>
                        {emotionScore.last_30d_avg.toFixed(1)}
                      </p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4 text-center">
                      <p className="text-xs text-gray-500 mb-1">趋势判断</p>
                      <p className={`font-bold ${
                        emotionScore.current_score > emotionScore.last_7d_avg
                          ? 'text-green-600'
                          : emotionScore.current_score < emotionScore.last_7d_avg
                          ? 'text-red-600'
                          : 'text-gray-600'
                      }`}>
                        {emotionScore.current_score > emotionScore.last_7d_avg ? '↑ 上升' :
                         emotionScore.current_score < emotionScore.last_7d_avg ? '↓ 下降' : '→ 持平'}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-xl shadow-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4">近30天情绪趋势</h3>
                  <div className="h-64">
                    <Line ref={chartRef} data={lineChartData} options={chartOptions} />
                  </div>
                </div>
              </>
            ) : (
              <div className="bg-white rounded-xl shadow-lg p-16 text-center">
                <span className="text-4xl">📈</span>
                <p className="mt-4 text-gray-500">暂无情绪数据</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
