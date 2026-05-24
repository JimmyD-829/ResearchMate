import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import Layout from '../components/Layout';
import ComplianceNote from '../components/ComplianceNote';

export default function BenchmarkPage() {
  const { user } = useAuth();
  const [companyName, setCompanyName] = useState('');
  const [benchmarkResult, setBenchmarkResult] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!companyName.trim()) return;
    if (!user) {
      alert('请先登录以使用行业对标功能');
      return;
    }

    setIsAnalyzing(true);
    setBenchmarkResult(null);

    try {
      const response = await fetch('/api/analysis/benchmark', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ company_name: companyName }),
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setBenchmarkResult(data);
      } else {
        const errorData = await response.json().catch(() => null);
        console.error('Benchmark error:', errorData);
        alert(`分析失败: ${errorData?.detail || '请稍后重试'}`);
      }
    } catch (error) {
      alert('网络错误，请稍后重试');
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (!user) {
    return (
      <Layout>
        <div className="text-center py-12">
          <p className="text-gray-600 dark:text-gray-400">请先登录以使用行业对标功能</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">行业对标分析</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">分析公司在行业中的定位和竞争力</p>
        </div>

        <ComplianceNote />

        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <form onSubmit={handleAnalyze}>
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1 relative">
                <input
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="输入公司名称，例如：贵州茅台、比亚迪"
                  className="w-full px-5 py-4 text-gray-900 dark:text-white bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-xl shadow-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all duration-300"
                />
              </div>
              <button
                type="submit"
                disabled={isAnalyzing || !companyName.trim()}
                className="px-8 py-4 bg-gradient-to-r from-primary-600 to-blue-600 hover:from-primary-500 hover:to-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-xl shadow-lg shadow-primary-500/25 transition-all duration-300 whitespace-nowrap"
              >
                {isAnalyzing ? (
                  <svg className="w-5 h-5 animate-spin inline-block mr-2" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  '开始分析'
                )}
              </button>
            </div>
          </form>
        </div>

        {benchmarkResult && (
          <div className="space-y-6">
            {benchmarkResult.industry && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="font-semibold text-gray-900 dark:text-white mb-4">所属行业</h2>
                <p className="text-gray-600 dark:text-gray-300">{benchmarkResult.industry}</p>
              </div>
            )}

            {benchmarkResult.competitors && Array.isArray(benchmarkResult.competitors) && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="font-semibold text-gray-900 dark:text-white mb-4">主要竞争对手</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {benchmarkResult.competitors.map((competitor: string, index: number) => (
                    <div key={index} className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-primary-500/20 rounded-lg flex items-center justify-center">
                          <span className="text-sm font-medium text-primary-600 dark:text-primary-400">{index + 1}</span>
                        </div>
                        <span className="text-gray-900 dark:text-white">{competitor}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {benchmarkResult.benchmark_data && typeof benchmarkResult.benchmark_data === 'object' && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="font-semibold text-gray-900 dark:text-white mb-4">行业平均指标对比</h2>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200 dark:border-gray-700">
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-500 dark:text-gray-400">指标</th>
                        <th className="text-right py-3 px-4 text-sm font-semibold text-gray-500 dark:text-gray-400">行业平均</th>
                        <th className="text-right py-3 px-4 text-sm font-semibold text-gray-500 dark:text-gray-400">公司水平</th>
                        <th className="text-center py-3 px-4 text-sm font-semibold text-gray-500 dark:text-gray-400">评级</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(benchmarkResult.benchmark_data).map(([key, value]) => {
                        const isObject = typeof value === 'object' && value !== null;
                        const industryAvg = isObject && 'industry_avg' in value ? String(value.industry_avg) : '-';
                        const companyValue = isObject && 'company_value' in value ? String(value.company_value) : '-';
                        const rating = isObject && 'rating' in value ? String(value.rating) : '-';
                        
                        let ratingClass = 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400';
                        if (rating === '优秀') ratingClass = 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400';
                        else if (rating === '良好') ratingClass = 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400';
                        else if (rating === '一般') ratingClass = 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400';
                        
                        return (
                          <tr key={key} className="border-b border-gray-100 dark:border-gray-700/50">
                            <td className="py-3 px-4 text-gray-900 dark:text-white">{key}</td>
                            <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">{industryAvg}</td>
                            <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">{companyValue}</td>
                            <td className="py-3 px-4 text-center">
                              <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${ratingClass}`}>
                                {rating}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {benchmarkResult.competitive_position && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="font-semibold text-gray-900 dark:text-white mb-4">竞争力分析</h2>
                <p className="text-gray-600 dark:text-gray-300 leading-relaxed">{benchmarkResult.competitive_position}</p>
              </div>
            )}

            {typeof benchmarkResult === 'string' && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
                <p className="text-gray-600 dark:text-gray-300 whitespace-pre-wrap">{benchmarkResult}</p>
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
}