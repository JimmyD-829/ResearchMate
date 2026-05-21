import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';
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
      case 'positive': return 'text-green-600 bg-green-100';
      case 'negative': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
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
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">市场新闻聚合</h1>
            <p className="text-gray-500 mt-1">关注公司最新动态，获取聚合资讯</p>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <div className="md:col-span-1">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-lg font-semibold text-gray-800 mb-4">关注列表</h2>
              
              <div className="mb-4">
                <input
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="输入公司名称"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition text-sm"
                  onKeyPress={(e) => e.key === 'Enter' && handleFollow()}
                />
                <button
                  onClick={handleFollow}
                  className="mt-2 w-full py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition"
                >
                  添加关注
                </button>
              </div>
              
              {follows.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-4">暂无关注公司</p>
              ) : (
                <div className="space-y-2">
                  {follows.map((follow) => (
                    <div
                      key={follow.id}
                      className={`flex items-center justify-between p-3 rounded-lg cursor-pointer transition ${
                        filterCompany === follow.company_name
                          ? 'bg-primary-100 text-primary-700'
                          : 'hover:bg-gray-100 text-gray-700'
                      }`}
                      onClick={() => fetchNews(follow.company_name)}
                    >
                      <div>
                        <p className="font-medium">{follow.company_name}</p>
                        {follow.stock_code && (
                          <p className="text-xs text-gray-500">{follow.stock_code}</p>
                        )}
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleUnfollow(follow.id);
                        }}
                        className="text-gray-400 hover:text-red-500 text-sm"
                      >
                        取消
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="md:col-span-2">
            <div className="bg-white rounded-xl shadow-lg">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-800">
                    {filterCompany ? `${filterCompany} - 相关新闻` : '全部新闻'}
                  </h2>
                  {filterCompany && (
                    <button
                      onClick={() => fetchNews()}
                      className="text-sm text-primary-600 hover:text-primary-700"
                    >
                      查看全部
                    </button>
                  )}
                </div>
              </div>
              
              {loading ? (
                <div className="p-8 text-center">
                  <div className="animate-spin rounded-full h-10 w-10 border-4 border-primary-400 border-t-transparent mx-auto"></div>
                  <p className="mt-4 text-gray-500">加载中...</p>
                </div>
              ) : news.length === 0 ? (
                <div className="p-16 text-center">
                  <span className="text-4xl">📰</span>
                  <p className="mt-4 text-gray-500">暂无新闻数据</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-100 max-h-[600px] overflow-y-auto">
                  {news.map((article) => (
                    <div key={article.id} className="p-4 hover:bg-gray-50 transition">
                      <a
                        href={article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block"
                      >
                        <h3 className="font-medium text-gray-800 hover:text-primary-600 transition line-clamp-2">
                          {article.title}
                        </h3>
                      </a>
                      <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                        <span>{article.source}</span>
                        <span>{formatDate(article.publish_time)}</span>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getEmotionColor(article.emotion_label)}`}>
                          {getEmotionText(article.emotion_label)}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 mt-2">{article.company_name}</p>
                    </div>
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
