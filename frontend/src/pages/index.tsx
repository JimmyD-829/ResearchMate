import Link from 'next/link';
import { useAuth } from '../context/AuthContext';
import ComplianceNote from '../components/ComplianceNote';
import Layout from '../components/Layout';

export default function HomePage() {
  const { user } = useAuth();

  const features = [
    {
      icon: '📊',
      title: '财报智能解读',
      description: '上传财报PDF，自动解析关键指标，AI生成专业摘要',
      link: '/reports',
      stats: '支持500+上市公司财报',
    },
    {
      icon: '📰',
      title: '市场新闻聚合',
      description: '关注公司动态，多平台资讯统一呈现',
      link: '/news',
      stats: '实时更新，每日1000+资讯',
    },
    {
      icon: '📈',
      title: '情绪指标分析',
      description: '量化市场情绪，趋势图表直观展示',
      link: '/emotion',
      stats: 'AI情感分析，准确率85%+',
    },
  ];

  return (
    <Layout>
      <div className="text-center mb-10">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-600/20 rounded-2xl mb-6">
          <span className="text-3xl">📊</span>
        </div>
        <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-primary-500 to-blue-600 bg-clip-text text-transparent">
          ResearchMate
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400 mt-4 max-w-2xl mx-auto">
          个人投资者的财报解读第一站
        </p>
        <p className="text-gray-500 dark:text-gray-500 mt-2 max-w-xl mx-auto text-sm">
          让个人投资者在10分钟内完成对一家公司的基本面、新闻动态和市场情绪的全面分析
        </p>
      </div>

      <ComplianceNote />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        {features.map((feature) => (
          <Link key={feature.title} href={feature.link}>
            <div className="group h-full bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 hover:shadow-xl hover:shadow-primary-500/5 transition-all duration-300 cursor-pointer flex flex-col">
              <div className="flex items-start gap-4 flex-1">
                <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-primary-500 to-blue-600 rounded-xl flex items-center justify-center">
                  <span className="text-xl">{feature.icon}</span>
                </div>
                <div className="flex-1 min-w-0 flex flex-col justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white mb-2 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                      {feature.title}
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">
                      {feature.description}
                    </p>
                  </div>
                  <span className="inline-flex items-center text-xs text-primary-600 dark:text-primary-400 bg-primary-500/10 px-2.5 py-1 rounded-full mt-4">
                    {feature.stats}
                  </span>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>

      <div className="text-center mb-12">
        {user ? (
          <Link
            href="/reports"
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-primary-600 to-blue-600 hover:from-primary-500 hover:to-blue-500 text-white font-medium rounded-xl shadow-lg shadow-primary-500/25 transition-all duration-300 hover:shadow-xl hover:shadow-primary-500/30"
          >
            开始分析
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        ) : (
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/login"
              className="inline-flex items-center px-6 py-3 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 hover:border-primary-500 dark:hover:border-primary-500 text-gray-900 dark:text-white font-medium rounded-xl transition-all duration-300"
            >
              登录
            </Link>
            <Link
              href="/register"
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-primary-600 to-blue-600 hover:from-primary-500 hover:to-blue-500 text-white font-medium rounded-xl shadow-lg shadow-primary-500/25 transition-all duration-300"
            >
              免费注册
            </Link>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-green-500/20 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">10分钟</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">完成一份财报分析</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-primary-500/20 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">AI驱动</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">专业解读，效率翻倍</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-500/20 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">深色模式</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">投研产品标准设计</p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
