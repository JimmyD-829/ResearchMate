import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
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
      const response = await api.post('/api/analysis/benchmark', {
        company_name: companyName
      });

      const resultData = response.data?.data || response.data;
      setBenchmarkResult(resultData);
    } catch (error: any) {
      console.error('Benchmark error:', error);
      const errorMessage = error.response?.data?.detail || error.message || '请稍后重试';
      alert(`分析失败: ${errorMessage}`);
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
            {benchmarkResult.company_name && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="font-semibold text-gray-900 dark:text-white mb-4">分析公司</h2>
                <p className="text-gray-600 dark:text-gray-300">{benchmarkResult.company_name}</p>
                {benchmarkResult.analysis_date && (
                  <p className="text-sm text-gray-400 mt-2">分析日期: {benchmarkResult.analysis_date}</p>
                )}
              </div>
            )}

            {benchmarkResult.industry_positioning && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="font-semibold text-gray-900 dark:text-white mb-4">行业定位</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {benchmarkResult.industry_positioning.market_share && (
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                      <p className="text-sm text-gray-500 dark:text-gray-400">市场份额</p>
                      <p className="text-xl font-bold text-primary-600">{benchmarkResult.industry_positioning.market_share}</p>
                    </div>
                  )}
                  {benchmarkResult.industry_positioning.industry_ranking && (
                    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                      <p className="text-sm text-gray-500 dark:text-gray-400">行业排名</p>
                      <p className="text-xl font-bold text-green-600">{benchmarkResult.industry_positioning.industry_ranking}</p>
                    </div>
                  )}
                </div>
                {benchmarkResult.industry_positioning.competitive_advantage && (
                  <div className="mt-4">
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">竞争优势</p>
                    <div className="flex flex-wrap gap-2">
                      {benchmarkResult.industry_positioning.competitive_advantage.map((adv: string, idx: number) => (
                        <span key={idx} className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded-full text-sm">
                          {adv}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {benchmarkResult.financial_comparison && typeof benchmarkResult.financial_comparison === 'object' && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="font-semibold text-gray-900 dark:text-white mb-4">财务指标对比</h2>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200 dark:border-gray-700">
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-500 dark:text-gray-400">指标</th>
                        <th className="right py-3 px-4 text-sm font-semibold text-gray-500 dark:text-gray-400">公司水平</th>
                        <th className="text-right py-3 px-4 text-sm font-semibold text-gray-500 dark:text-gray-400">行业平均</th>
                        <th className="text-center py-3 px-4 text-sm font-semibold text-gray-500 dark:text-gray-400">评估</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(benchmarkResult.financial_comparison).map(([key, value]: [string, any]) => {
                        const isObject = typeof value === 'object' && value !== null;
                        const companyValue = isObject && value.company ? String(value.company) : '-';
                        const industryAvg = isObject && value.industry_avg ? String(value.industry_avg) : '-';
                        const assessment = isObject && value.assessment ? String(value.assessment) : '-';
                        
                        let ratingClass = 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400';
                        if (assessment.includes('优于') || assessment.includes('优秀')) ratingClass = 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400';
                        else if (assessment.includes('良好') || assessment.includes('突出')) ratingClass = 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400';
                        
                        return (
                          <tr key={key} className="border-b border-gray-100 dark:border-gray-700/50">
                            <td className="py-3 px-4 text-gray-900 dark:text-white font-medium">{key.replace(/_/g, ' ')}</td>
                            <td className="py-3 px-4 text-right text-gray-900 dark:text-white font-semibold">{companyValue}</td>
                            <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">{industryAvg}</td>
                            <td className="py-3 px-4 text-center">
                              <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${ratingClass}`}>
                                {assessment}
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

            {benchmarkResult.swot_analysis && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="font-semibold text-gray-900 dark:text-white mb-4">SWOT分析</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    { label: '优势 Strengths', items: benchmarkResult.swot_analysis.strengths, bgColor: 'bg-green-50 dark:bg-green-900/20', textColor: 'text-green-700 dark:text-green-400' },
                    { label: '劣势 Weaknesses', items: benchmarkResult.swot_analysis.weaknesses, bgColor: 'bg-red-50 dark:bg-red-900/20', textColor: 'text-red-700 dark:text-red-400' },
                    { label: '机会 Opportunities', items: benchmarkResult.swot_analysis.opportunities, bgColor: 'bg-blue-50 dark:bg-blue-900/30', textColor: 'text-blue-700 dark:text-blue-400' },
                    { label: '威胁 Threats', items: benchmarkResult.swot_analysis.threats, bgColor: 'bg-yellow-50 dark:bg-yellow-900/20', textColor: 'text-yellow-700 dark:text-yellow-400' },
                  ].map((swot, idx) => (
                    <div key={idx} className={`rounded-xl p-4 ${swot.bgColor}`}>
                      <h3 className={`font-medium ${swot.textColor} mb-2`}>{swot.label}</h3>
                      <ul className="list-disc list-inside space-y-1">
                        {swot.items?.map((item: string, i: number) => (
                          <li key={i} className="text-sm text-gray-700 dark:text-gray-300">{item}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {benchmarkResult.peer_comparison && Array.isArray(benchmarkResult.peer_comparison) && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="font-semibold text-gray-900 dark:text-white mb-4">同行对比</h2>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200 dark:border-gray-700">
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-500 dark:text-gray-400">公司</th>
                        <th className="text-right py-3 px-4 text-sm font-semibold text-gray-500 dark:text-gray-400">综合评分</th>
                        <th className="text-right py-3 px-4 text-sm font-semibold text-gray-500 dark:text-gray-400">营收增长</th>
                      </tr>
                    </thead>
                    <tbody>
                      {benchmarkResult.peer_comparison.map((peer: any, index: number) => (
                        <tr key={index} className="border-b border-gray-100 dark:border-gray-700/50">
                          <td className="py-3 px-4 text-gray-900 dark:text-white font-medium">{peer.peer}</td>
                          <td className="py-3 px-4 text-right">
                            <span className="font-bold text-primary-600">{peer.score}</span>
                          </td>
                          <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">{peer.revenue_growth}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {benchmarkResult.overall_assessment && (
              <div className="bg-gradient-to-r from-primary-50 to-blue-50 dark:from-primary-900/20 dark:to-blue-900/20 rounded-2xl border border-primary-200 dark:border-primary-800 p-6">
                <h2 className="font-semibold text-gray-900 dark:text-white mb-3">📊 综合评估</h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">{benchmarkResult.overall_assessment}</p>
              </div>
            )}

            {benchmarkResult.recommendation && (
              <div className="bg-green-50 dark:bg-green-900/20 rounded-2xl border border-green-200 dark:border-green-800 p-6">
                <h2 className="font-semibold text-green-800 dark:text-green-300 mb-2">💡 投资建议</h2>
                <p className="text-green-700 dark:text-green-400">{benchmarkResult.recommendation}</p>
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