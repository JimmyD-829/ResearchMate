import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';
import ComplianceNote from '../components/ComplianceNote';
import { newsApi, NewsArticle, Follow } from '../services/api';

export default function NewsPage() {
  const [news, setNews] = useState<NewsArticle[]>([]);
  const [follows, setFollows] = useState<Follow[]>([]);
  const [loading, setLoading] = useState(true);
  const [companyName, setCompanyName] = useState('');
  const [filterCompany, setFilterCompany] = useState<string | null>(null);

  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }
    fetchFollows();
    fetchNews();
  }, [user, router]);

  const fetchFollows = async () => {
    try {
      const response = await newsApi.getFollows();
      const followsData = response.data?.data || response.data;
      setFollows(Array.isArray(followsData) ? followsData : []);
    } catch (err) {
      console.error('获取关注列表失败');
    }
  };

  const fetchNews = async (company?: string) => {
    setLoading(true);
    try {
      const params = company ? { company_name: company } : undefined;
      const response = await newsApi.getNews(params);
      const newsData = response.data?.data || response.data;
      setNews(newsData?.items || []);
      setFilterCompany(company || null);
    } catch (err) {
      console.error('获取新闻失败');
    } finally {
      setLoading(false);
    }
  };

  const handleFollow = async () => {
    if (!companyName.trim()) return;

    try {
      await newsApi.follow({ company_name: companyName.trim() });
      await fetchFollows();
      setCompanyName('');
    } catch (err) {
      console.error('关注失败');
    }
  };

  const handleUnfollow = async (id: string) => {
    try {
      await newsApi.unfollow(id);
      await fetchFollows();
      if (filterCompany && follows.find(f => f.id === id)?.company_name === filterCompany) {
        fetchNews();
      }
    } catch (err) {
      console.error('取消关注失败');
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  const getEmotionColor = (label?: string) => {
    switch (label) {
      case 'positive': return 'text-green-600 dark:text-green-400 bg-green-100 dark:bg-green-900/30';
      case 'negative': return 'text-red-600 dark:text-red-400 bg-red-100 dark:bg-red-900/30';
      default: return 'text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700';
    }
  };

  const getEmotionText = (label?: string) => {
    switch (label) {
      case 'positive': return '积极';
      case 'negative': return '消极';
      default: return '中性';
    }
  };

  if (!user) return null;

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">市场新闻聚合</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">关注公司最新动态，获取聚合资讯</p>
        </div>

        <ComplianceNote />

        <div className="grid md:grid-cols-4 gap-6">
          <div className="md:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">📋 关注列表</h2>
              
              <div className="mb-6">
                <input
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="输入公司名称"
                  className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 dark:focus:border-primary-400 outline-none transition text-gray-900 dark:text-white"
                  onKeyPress={(e) => e.key === 'Enter' && handleFollow()}
                />
                <button
                  onClick={handleFollow}
                  className="mt-3 w-full py-3 bg-gradient-to-r from-primary-600 to-blue-600 hover:from-primary-500 hover:to-blue-500 text-white font-semibold rounded-xl transition-all"
                >
                  添加关注
                </button>
              </div>
              
              {follows.length === 0 ? (
                <p className="text-sm text-gray-600 dark:text-gray-400 text-center py-6">暂无关注公司</p>
              ) : (
                <div className="space-y-2">
                  <button
                    onClick={() => fetchNews()}
                    className={`w-full text-left p-4 rounded-xl transition-colors ${
                      filterCompany === null
                        ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400'
                        : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
                    }`}
                  >
                    <span className="font-medium">全部资讯</span>
                  </button>
                  {follows.map((follow) => (
                    <div
                      key={follow.id}
                      className={`flex items-center justify-between p-4 rounded-xl cursor-pointer transition-colors ${
                        filterCompany === follow.company_name
                          ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400'
                          : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
                      }`}
                      onClick={() => fetchNews(follow.company_name)}
                    >
                      <div>
                        <p className="font-medium">{follow.company_name}</p>
                        {follow.stock_code && (
                          <p className="text-xs text-gray-500 dark:text-gray-400">{follow.stock_code}</p>
                        )}
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleUnfollow(follow.id);
                        }}
                        className="text-gray-400 hover:text-red-500 text-sm font-medium"
                      >
                        取消
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="md:col-span-3">
            <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700">
              <div className="px-6 py-5 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    {filterCompany ? `${filterCompany} - 相关新闻` : '全部新闻'}
                  </h2>
                  {filterCompany && (
                    <button
                      onClick={() => fetchNews()}
                      className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 font-semibold"
                    >
                      查看全部
                    </button>
                  )}
                </div>
              </div>
              
              {loading ? (
                <div className="py-16 text-center">
                  <div className="animate-spin rounded-full h-10 w-10 border-2 border-primary-500 border-t-transparent mx-auto" />
                  <p className="mt-4 text-gray-600 dark:text-gray-400">加载中...</p>
                </div>
              ) : news.length === 0 ? (
                <div className="py-16 text-center">
                  <span className="text-5xl">📰</span>
                  <p className="mt-4 text-gray-600 dark:text-gray-400">暂无新闻数据</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-200 dark:divide-gray-700 max-h-[700px] overflow-y-auto">
                  {news.map((article) => (
                    <a
                      key={article.id}
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block p-6 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
                    >
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white hover:text-primary-600 dark:hover:text-primary-400 transition-colors line-clamp-2">
                        {article.title}
                      </h3>
                      <div className="flex items-center gap-4 mt-3 text-sm text-gray-600 dark:text-gray-400">
                        <span>{article.source}</span>
                        <span>{formatDate(article.publish_time)}</span>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getEmotionColor(article.emotion_label)}`}>
                          {getEmotionText(article.emotion_label)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">{article.company_name}</p>
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
