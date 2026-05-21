import Link from 'next/link';
import { useAuth } from '../context/AuthContext';
import ComplianceNote from '../components/ComplianceNote';

export default function HomePage() {
  const { user } = useAuth();

  const features = [
    {
      icon: '📄',
      title: '财报智能解读',
      description: '上传财报PDF，自动解析关键指标，AI生成摘要',
      link: '/reports',
    },
    {
      icon: '📰',
      title: '市场新闻聚合',
      description: '关注公司动态，多平台资讯统一呈现',
      link: '/news',
    },
    {
      icon: '📈',
      title: '情绪指标分析',
      description: '量化市场情绪，趋势图表直观展示',
      link: '/emotion',
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 dark:from-gray-800 to-blue-100 dark:to-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <span className="text-6xl">📊</span>
          <h1 className="text-4xl font-bold text-gray-800 dark:text-white mt-6">ResearchMate</h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mt-4">个人投资者的财报解读第一站</p>
          <p className="text-gray-500 dark:text-gray-400 mt-2 max-w-2xl mx-auto">
            让个人投资者在10分钟内完成对一家公司的基本面、新闻动态和市场情绪的全面分析
          </p>
        </div>

        <ComplianceNote />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {features.map((feature) => (
            <Link key={feature.title} href={feature.link}>
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 hover:shadow-xl transition-all hover:-translate-y-1 cursor-pointer border border-gray-100 dark:border-gray-700">
                <span className="text-4xl block mb-4">{feature.icon}</span>
                <h3 className="text-xl font-semibold text-gray-800 dark:text-white mb-2">{feature.title}</h3>
                <p className="text-gray-500 dark:text-gray-400">{feature.description}</p>
              </div>
            </Link>
          ))}
        </div>

        <div className="text-center">
          {user ? (
            <Link
              href="/reports"
              className="inline-block px-8 py-4 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transition-all"
            >
              开始分析 →
            </Link>
          ) : (
            <div className="space-x-4">
              <Link
                href="/login"
                className="inline-block px-8 py-4 bg-white dark:bg-gray-800 text-primary-600 dark:text-primary-400 font-medium rounded-xl shadow-lg hover:shadow-xl transition-all"
              >
                登录
              </Link>
              <Link
                href="/register"
                className="inline-block px-8 py-4 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transition-all"
              >
                免费注册
              </Link>
            </div>
          )}
        </div>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-6 bg-white/50 dark:bg-gray-800/50 rounded-xl">
            <p className="text-3xl font-bold text-primary-600 dark:text-primary-400">10分钟</p>
            <p className="text-gray-600 dark:text-gray-400 mt-1">完成一份财报分析</p>
          </div>
          <div className="text-center p-6 bg-white/50 dark:bg-gray-800/50 rounded-xl">
            <p className="text-3xl font-bold text-primary-600 dark:text-primary-400">AI驱动</p>
            <p className="text-gray-600 dark:text-gray-400 mt-1">专业解读，效率翻倍</p>
          </div>
          <div className="text-center p-6 bg-white/50 dark:bg-gray-800/50 rounded-xl">
            <p className="text-3xl font-bold text-primary-600 dark:text-primary-400">深色模式</p>
            <p className="text-gray-600 dark:text-gray-400 mt-1">投研产品标准设计</p>
          </div>
        </div>
      </div>
    </div>
  );
}
