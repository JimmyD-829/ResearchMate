import { useAuth } from '../context/AuthContext';
import Link from 'next/link';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Link href="/" className="flex items-center space-x-2">
                <span className="text-2xl">📊</span>
                <span className="text-xl font-bold text-primary-600">ResearchMate</span>
              </Link>
            </div>
            
            <nav className="flex items-center space-x-6">
              <Link href="/reports" className="text-gray-600 hover:text-primary-600">
                财报解析
              </Link>
              <Link href="/news" className="text-gray-600 hover:text-primary-600">
                新闻聚合
              </Link>
              <Link href="/emotion" className="text-gray-600 hover:text-primary-600">
                情绪分析
              </Link>
              
              {user ? (
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-gray-600">欢迎, {user.nickname}</span>
                  <button
                    onClick={logout}
                    className="px-4 py-2 text-sm text-gray-600 hover:text-primary-600"
                  >
                    退出登录
                  </button>
                </div>
              ) : (
                <div className="flex items-center space-x-4">
                  <Link href="/login" className="text-sm text-gray-600 hover:text-primary-600">
                    登录
                  </Link>
                  <Link
                    href="/register"
                    className="px-4 py-2 text-sm text-white bg-primary-600 rounded-lg hover:bg-primary-700"
                  >
                    注册
                  </Link>
                </div>
              )}
            </nav>
          </div>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}
