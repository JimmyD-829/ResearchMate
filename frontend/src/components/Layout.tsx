import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import ThemeToggle from './ThemeToggle';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuth();
  const pathname = usePathname();

  const isActive = (path: string) => pathname === path || pathname?.startsWith(path + '/');

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 transition-colors">
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Link href="/" className="flex items-center space-x-2">
                <span className="text-2xl">📊</span>
                <span className="text-xl font-bold text-primary-600 dark:text-primary-400">ResearchMate</span>
              </Link>
            </div>
            
            <nav className="flex items-center space-x-1">
              <Link 
                href="/reports" 
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive('/reports') 
                    ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400' 
                    : 'text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                财报解析
              </Link>
              <Link 
                href="/compare" 
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive('/compare') 
                    ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400' 
                    : 'text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                财报对比
              </Link>
              <Link 
                href="/news" 
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive('/news') 
                    ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400' 
                    : 'text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                新闻聚合
              </Link>
              <Link 
                href="/emotion" 
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive('/emotion') 
                    ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400' 
                    : 'text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                情绪分析
              </Link>
              <Link 
                href="/benchmark" 
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive('/benchmark') 
                    ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400' 
                    : 'text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                行业对标
              </Link>

              <ThemeToggle />
              
              {user ? (
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-gray-600 dark:text-gray-300">欢迎, {user.nickname}</span>
                  <button
                    onClick={logout}
                    className="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400"
                  >
                    退出登录
                  </button>
                </div>
              ) : (
                <div className="flex items-center space-x-4">
                  <Link href="/login" className="text-sm text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400">
                    登录
                  </Link>
                  <Link
                    href="/register"
                    className="px-4 py-2 text-sm text-white bg-primary-600 hover:bg-primary-700 rounded-lg"
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

      <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 py-6 mt-8">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm text-gray-500 dark:text-gray-400">
          <p>AI生成，仅供参考。本分析不构成投资建议。</p>
        </div>
      </footer>
    </div>
  );
}
