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
      setFollows(response.data);
    } catch (err) {
      console.error('获取关注列表失败');
    }
  };

  const fetchNews = async (company?: string) => {
    setLoading(true);
    try {
      const params = company ? { company_name: company } : undefined;
      const response = await newsApi.getNews(params);
      setNews(response.data.items);
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
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 dark:text-white">市场新闻聚合</h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">关注公司最新动态，获取聚合资讯</p>
          </div>
        </div>

        <ComplianceNote />

        <div className="grid md:grid-cols-4 gap-6">
          <div className="md:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 border border-gray-100 dark:border-gray-700">
              <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-4">📋 关注列表</h2>
              
              <div className="mb-6">
                <input
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="输入公司名称"
                  className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-primary-500 outline-none transition"
                  onKeyPress={(e) => e.key === 'Enter' && handleFollow()}
                />
                <button
                  onClick={handleFollow}
                  className="mt-3 w-full py-3 bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium rounded-xl transition-all"
                >
                  添加关注
                </button>
              </div>
              
              {follows.length === 0 ? (
                <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">暂无关注公司</p>
              ) : (
                <div className="space-y-2">
                  <button
                    onClick={() => fetchNews()}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      filterCompany === null
                        ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400'
                        : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
                    }`}
                  >
                    全部资讯
                  </button>
                  {follows.map((follow) => (
                    <div
                      key={follow.id}
                      className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition-colors ${
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
                        className="text-gray-400 hover:text-red-500 text-xs"
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
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-100 dark:border-gray-700">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-semibold text-gray-800 dark:text-white">
                    {filterCompany ? `${filterCompany} - 相关新闻` : '全部新闻'}
                  </h2>
                  {filterCompany && (
                    <button
                      onClick={() => fetchNews()}
                      className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
                    >
                      查看全部
                    </button>
                  )}
                </div>
              </div>
              
              {loading ? (
                <div className="p-12 text-center">
                  <div className="animate-spin rounded-full h-10 w-10 border-4 border-primary-400 border-t-transparent mx-auto" />
                  <p className="mt-4 text-gray-500 dark:text-gray-400">加载中...</p>
                </div>
              ) : news.length === 0 ? (
                <div className="p-16 text-center">
                  <span className="text-5xl">📰</span>
                  <p className="mt-4 text-gray-500 dark:text-gray-400">暂无新闻数据</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-100 dark:divide-gray-700 max-h-[700px] overflow-y-auto">
                  {news.map((article) => (
                    <a
                      key={article.id}
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                    >
                      <h3 className="font-medium text-gray-800 dark:text-white hover:text-primary-600 dark:hover:text-primary-400 transition-colors line-clamp-2">
                        {article.title}
                      </h3>
                      <div className="flex items-center gap-4 mt-3 text-sm text-gray-500 dark:text-gray-400">
                        <span>{article.source}</span>
                        <span>{formatDate(article.publish_time)}</span>
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${getEmotionColor(article.emotion_label)}`}>
                          {getEmotionText(article.emotion_label)}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 mt-2">{article.company_name}</p>
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
