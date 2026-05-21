import Link from 'next/link';
import { useAuth } from '../context/AuthContext';

export default function HomePage() {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-blue-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-16">
          <span className="text-6xl">📊</span>
          <h1 className="text-4xl font-bold text-gray-800 mt-6">ResearchMate</h1>
          <p className="text-xl text-gray-600 mt-4">智能投研助手</p>
          <p className="text-gray-500 mt-2 max-w-2xl mx-auto">
            让个人投资者在10分钟内完成对一家公司的基本面、新闻动态和市场情绪的全面分析
          </p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="bg-white rounded-xl shadow-lg p-8 text-center">
            <span className="text-4xl">📄</span>
            <h3 className="text-xl font-semibold text-gray-800 mt-4">财报智能解读</h3>
            <p className="text-gray-500 mt-2">上传财报PDF，自动解析关键指标，生成AI摘要</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-8 text-center">
            <span className="text-4xl">📰</span>
            <h3 className="text-xl font-semibold text-gray-800 mt-4">市场新闻聚合</h3>
            <p className="text-gray-500 mt-2">多平台资讯整合，统一入口获取财经信息</p>
          </div>
          
          <div className="bg-white rounded-xl shadow-lg p-8 text-center">
            <span className="text-4xl">📈</span>
            <h3 className="text-xl font-semibold text-gray-800 mt-4">情绪指标分析</h3>
            <p className="text-gray-500 mt-2">量化市场情绪，提供客观决策依据</p>
          </div>
        </div>
        
        <div className="text-center">
          {user ? (
            <Link
              href="/reports"
              className="inline-block px-8 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition"
            >
              开始分析
            </Link>
          ) : (
            <div className="space-x-4">
              <Link
                href="/login"
                className="inline-block px-8 py-3 bg-white text-primary-600 font-medium rounded-lg hover:bg-gray-50 transition shadow"
              >
                登录
              </Link>
              <Link
                href="/register"
                className="inline-block px-8 py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 transition"
              >
                免费注册
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
