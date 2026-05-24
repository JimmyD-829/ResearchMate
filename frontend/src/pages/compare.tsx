import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import Layout from '../components/Layout';
import ComplianceNote from '../components/ComplianceNote';

interface Report {
  id: string;
  company_name: string;
  created_at: string;
}

export default function ComparePage() {
  const { user } = useAuth();
  const [reports, setReports] = useState<Report[]>([]);
  const [selectedReports, setSelectedReports] = useState<string[]>([]);
  const [comparisonResult, setComparisonResult] = useState<any>(null);
  const [isComparing, setIsComparing] = useState(false);

  useEffect(() => {
    if (user) {
      fetchReports();
    }
  }, [user]);

  const fetchReports = async () => {
    try {
      const response = await api.get('/api/reports');
      setReports(response.data?.data || []);
    } catch (error) {
      console.error('Failed to fetch reports:', error);
    }
  };

  const toggleReportSelection = (reportId: string) => {
    if (selectedReports.includes(reportId)) {
      setSelectedReports(selectedReports.filter(id => id !== reportId));
    } else if (selectedReports.length < 5) {
      setSelectedReports([...selectedReports, reportId]);
    }
  };

  const handleCompare = async () => {
    if (selectedReports.length < 2) {
      alert('请至少选择2份财报进行对比');
      return;
    }

    setIsComparing(true);
    setComparisonResult(null);

    try {
      const response = await api.post('/api/analysis/compare', { report_ids: selectedReports });
      setComparisonResult(response.data?.data);
    } catch (error: any) {
      console.error('Compare error:', error);
      alert(`对比失败: ${error.response?.data?.detail || '请稍后重试'}`);
    } finally {
      setIsComparing(false);
    }
  };

  const handleClear = () => {
    setSelectedReports([]);
    setComparisonResult(null);
  };

  if (!user) {
    return (
      <Layout>
        <div className="text-center py-12">
          <p className="text-gray-600 dark:text-gray-400">请先登录以使用财报对比功能</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">财报对比分析</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">选择多份财报进行对比分析</p>
        </div>

        <ComplianceNote />

        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 mb-6">
          <h2 className="font-semibold text-gray-900 dark:text-white mb-4">选择要对比的财报</h2>
          
          {reports.length === 0 ? (
            <p className="text-gray-500 dark:text-gray-400 text-center py-8">暂无财报数据</p>
          ) : (
            <div className="space-y-3">
              {reports.map((report) => (
                <div
                  key={report.id}
                  onClick={() => toggleReportSelection(report.id)}
                  className={`flex items-center justify-between p-4 rounded-xl border cursor-pointer transition-all duration-200 ${
                    selectedReports.includes(report.id)
                      ? 'bg-primary-500/10 border-primary-500'
                      : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                  }`}
                >
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{report.company_name}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {new Date(report.created_at).toLocaleDateString('zh-CN')}
                    </p>
                  </div>
                  <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
                    selectedReports.includes(report.id)
                      ? 'bg-primary-500 border-primary-500'
                      : 'border-gray-300 dark:border-gray-500'
                  }`}>
                    {selectedReports.includes(report.id) && (
                      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
            <span className="text-sm text-gray-500 dark:text-gray-400">
              已选择 {selectedReports.length}/5 份财报
            </span>
            <div className="flex gap-3">
              {selectedReports.length > 0 && (
                <button
                  onClick={handleClear}
                  className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
                >
                  清除选择
                </button>
              )}
              <button
                onClick={handleCompare}
                disabled={selectedReports.length < 2 || isComparing}
                className="px-6 py-2 bg-gradient-to-r from-primary-600 to-blue-600 hover:from-primary-500 hover:to-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-xl transition-all duration-300"
              >
                {isComparing ? '对比中...' : '开始对比'}
              </button>
            </div>
          </div>
        </div>

        {comparisonResult && (
          <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="font-semibold text-gray-900 dark:text-white">对比分析结果</h2>
              <button
                onClick={handleClear}
                className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
              >
                返回重新选择
              </button>
            </div>

            {comparisonResult.comparison_summary && (
              <div className="mb-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">对比摘要</h3>
                <p className="text-gray-600 dark:text-gray-300">{comparisonResult.comparison_summary}</p>
              </div>
            )}

            {comparisonResult.growth_rates && typeof comparisonResult.growth_rates === 'object' && (
              <div className="mb-6">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">增长率对比</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(comparisonResult.growth_rates).map(([key, value]) => {
                    const displayValue = String(value);
                    return (
                      <div key={key} className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                        <p className="text-sm text-gray-500 dark:text-gray-400">{key}</p>
                        <p className={`text-xl font-bold ${
                          displayValue.includes('-') ? 'text-red-500' : 'text-green-500'
                        }`}>
                          {displayValue}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {comparisonResult.trend_analysis && (
              <div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">趋势分析</h3>
                <p className="text-gray-600 dark:text-gray-300">{comparisonResult.trend_analysis}</p>
              </div>
            )}

            {typeof comparisonResult === 'string' && (
              <div className="text-gray-600 dark:text-gray-300 whitespace-pre-wrap">
                {comparisonResult}
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
}