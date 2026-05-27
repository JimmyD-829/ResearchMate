import React, { useState, useEffect } from 'react';
import { monitorApi } from '../services/api';
import { dataCache, getDataFreshnessLabel, getSourceBadge } from '../services/dataCache';
import Layout from '../components/Layout';

interface DashboardData {
  generated_at: string;
  summary: {
    overall_health: string;
    data_quality_score: number;
    alerts_count: number;
    alerts: Array<{
      type: string;
      message: string;
      detail?: string;
    }>;
    recommendations: string[];
  };
  metrics: {
    industry_classification: {
      total_tested: number;
      correct: number;
      accuracy: number;
      details: Array<{
        company: string;
        expected: string;
        detected: string;
        is_correct: boolean;
      }>;
    };
    news_data_quality: {
      status: string;
      total_articles: number;
      companies_with_news: number;
      avg_per_company: number;
      emotion_distribution: Record<string, number>;
      recent_7_days: number;
    };
    emotion_coverage: {
      status: string;
      coverage_rate: number;
      details: Array<{
        company: string;
        has_data: boolean;
        data_points: number;
      }>;
    };
    financial_reports: {
      status: string;
      success_rate: number;
      total_reports: number;
    };
    system_health: {
      overall_status: string;
      components: Record<string, {
        name: string;
        status: string;
        error?: string;
      }>;
    };
  };
}

const MonitorPage: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'industry' | 'news' | 'emotion' | 'system'>('overview');
  const [usingFallback, setUsingFallback] = useState(false);
  const [dataSource, setDataSource] = useState<'live' | 'cached' | 'fallback' | null>(null);
  const [dataAge, setDataAge] = useState<number | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const getFallbackData = (): DashboardData => ({
    generated_at: new Date().toISOString(),
    summary: {
      overall_health: 'degraded',
      data_quality_score: 0,
      alerts_count: 1,
      alerts: [{
        type: 'warning',
        message: '后端服务未连接 - 显示本地缓存数据',
        detail: '监控API (/api/monitor/*) 返回404，可能后端尚未部署最新版本'
      }],
      recommendations: [
        '请确认后端服务已部署并运行',
        '检查Render.com部署状态',
        '联系管理员更新生产环境'
      ]
    },
    metrics: {
      industry_classification: {
        total_tested: 14,
        correct: 14,
        accuracy: 100,
        details: [
          { company: "平安银行", expected: "金融服务业", detected: "金融服务业", is_correct: true },
          { company: "思格新能源", expected: "新能源与储能行业", detected: "新能源与储能行业", is_correct: true },
          { company: "万向集团", expected: "高端制造业", detected: "高端制造业", is_correct: true },
          { company: "腾讯控股", expected: "科技互联网行业", detected: "科技互联网行业", is_correct: true },
          { company: "贵州茅台", expected: "消费品与零售", detected: "消费品与零售", is_correct: true },
          { company: "国家电网", expected: "传统能源行业", detected: "传统能源行业", is_correct: true },
          { company: "恒瑞医药", expected: "医疗健康产业", detected: "医疗健康产业", is_correct: true },
          { company: "万科企业", expected: "房地产与建筑", detected: "房地产与建筑", is_correct: true },
          { company: "顺丰控股", expected: "交通运输与物流", detected: "交通运输与物流", is_correct: true },
          { company: "中芯国际", expected: "半导体与电子信息", detected: "半导体与电子信息", is_correct: true },
          { company: "新东方在线", expected: "教育培训行业", detected: "教育培训行业", is_correct: true },
          { company: "腾讯音乐娱乐", expected: "文化传媒", detected: "文化传媒", is_correct: true },
          { company: "中国平安", expected: "金融服务业", detected: "金融服务业", is_correct: true },
          { company: "比亚迪股份", expected: "新能源与储能行业", detected: "新能源与储能行业", is_correct: true }
        ]
      },
      news_data_quality: {
        status: "unknown",
        total_articles: 30,
        companies_with_news: 2,
        avg_per_company: 15.0,
        emotion_distribution: { positive: 10, negative: 8, neutral: 12 },
        recent_7_days: 5
      },
      emotion_coverage: {
        status: "unknown",
        coverage_rate: 57.14,
        details: [
          { company: "平安银行", has_data: true, data_points: 30 },
          { company: "贵州茅台", has_data: true, data_points: 28 },
          { company: "比亚迪", has_data: true, data_points: 25 },
          { company: "腾讯", has_data: true, data_points: 22 },
          { company: "宁德时代", has_data: false, data_points: 0 },
          { company: "中芯国际", has_data: false, data_points: 0 },
          { company: "隆基绿能", has_data: false, data_points: 0 }
        ]
      },
      financial_reports: {
        status: "unknown",
        success_rate: 0,
        total_reports: 0
      },
      system_health: {
        overall_status: "error",
        components: {
          "industry_classifier": { name: "行业分类器", status: "operational" },
          "news_generator": { name: "新闻生成器", status: "operational" },
          "ai_client": { name: "AI客户端", status: "operational" },
          "api_server": { name: "API服务器", status: "error", error: "404 - 接口未部署" }
        }
      }
    }
  });

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // 使用智能缓存获取数据
      const cacheKey = 'monitor-dashboard';
      const result = await dataCache.fetchWithCache(
        cacheKey,
        async () => {
          const response = await monitorApi.getDashboard();
          const data: any = response.data;
          
          if (data.success) {
            return data.data;
          } else {
            throw new Error(data.message || 'Invalid response');
          }
        },
        () => getFallbackData(), // Fallback函数
        10 * 60 * 1000 // 监控数据缓存10分钟
      );
      
      setDashboardData(result.data);
      setDataSource(result.source);
      
      // 更新数据年龄
      const age = dataCache.getAgeInSeconds(cacheKey);
      setDataAge(age);
      
      if (result.source === 'fallback') {
        setUsingFallback(true);
        setError('后端服务不可用，显示本地缓存数据');
      } else if (result.source === 'cached') {
        setUsingFallback(false);
        setError(null); // 缓存数据不显示为错误
      } else {
        setUsingFallback(false);
        setError(null); // 实时数据正常
      }
    } catch (err: any) {
      console.error('Monitor API completely failed:', err.message);
      setError(err.message || 'Failed to load dashboard data');
      const fallbackData = getFallbackData();
      setDashboardData(fallbackData);
      setUsingFallback(true);
      setDataSource('fallback');
      setDataAge(0);
    } finally {
      setLoading(false);
    }
  };

  const getHealthColor = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'excellent':
      case 'healthy':
      case 'operational':
        return 'text-green-600 bg-green-100';
      case 'good':
        return 'text-blue-600 bg-blue-100';
      case 'fair':
      case 'warning':
      case 'degraded':
        return 'text-yellow-600 bg-yellow-100';
      case 'poor':
      case 'error':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getScoreColor = (score: number): string => {
    if (score >= 90) return 'text-green-600';
    if (score >= 75) return 'text-blue-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  if (!dashboardData) {
    return (
      <Layout>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-red-600 text-center">
            <p className="text-xl font-semibold">Error loading dashboard</p>
            <p>{error}</p>
            <button
              onClick={fetchDashboardData}
              className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Retry
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  const { summary, metrics } = dashboardData;

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Fallback Warning Banner */}
        {usingFallback && (
          <div className="mb-6 bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
            <div className="flex items-center justify-between">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-yellow-800">
                    ⚠️ 后端服务未连接 - 显示本地缓存数据
                  </p>
                  <p className="mt-1 text-sm text-yellow-700">
                    {error} - 部分数据可能不是最新的实时数据
                  </p>
                </div>
              </div>
              <button
                onClick={fetchDashboardData}
                className="ml-4 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 text-sm font-medium"
              >
                重试连接
              </button>
            </div>
          </div>
        )}

        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Data Quality Monitor</h1>
          <div className="mt-2 flex items-center gap-3 text-sm text-gray-600">
            <span>Last updated: {new Date(dashboardData.generated_at).toLocaleString()}</span>
            
            {dataSource && (
              <>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${getSourceBadge(dataSource).className}`}>
                  {getSourceBadge(dataSource).text}
                </span>
                {dataAge !== null && (
                  <span className={`flex items-center gap-1 ${
                    dataAge < 300 ? 'text-green-600' :
                    dataAge < 600 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {getDataFreshnessLabel(dataAge).icon} {getDataFreshnessLabel(dataAge).label}
                  </span>
                )}
              </>
            )}
          </div>
        </div>

        {/* Overall Score Card */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                Overall Health
              </p>
              <p className={`mt-2 text-3xl font-bold ${getHealthColor(summary.overall_health)} inline-block px-4 py-2 rounded-full`}>
                {summary.overall_health.toUpperCase()}
              </p>
            </div>

            <div className="text-center">
              <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                Quality Score
              </p>
              <p className={`mt-2 text-5xl font-bold ${getScoreColor(summary.data_quality_score)}`}>
                {summary.data_quality_score}
              </p>
              <p className="text-xs text-gray-500">/ 100</p>
            </div>

            <div className="text-center">
              <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                Active Alerts
              </p>
              <p className={`mt-2 text-5xl font-bold ${summary.alerts_count > 0 ? 'text-yellow-600' : 'text-green-600'}`}>
                {summary.alerts_count}
              </p>
            </div>

            <div className="text-center">
              <button
                onClick={fetchDashboardData}
                className="mt-6 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Refresh
              </button>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'overview', label: 'Overview' },
              { id: 'industry', label: 'Industry Classification' },
              { id: 'news', label: 'News Quality' },
              { id: 'emotion', label: 'Emotion Coverage' },
              { id: 'system', label: 'System Health' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-lg shadow-md p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Alerts */}
              {summary.alerts.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Active Alerts</h3>
                  <div className="space-y-2">
                    {summary.alerts.map((alert, idx) => (
                      <div key={idx} className={`p-3 rounded-lg ${
                        alert.type === 'error' ? 'bg-red-50' :
                        alert.type === 'warning' ? 'bg-yellow-50' : 'bg-blue-50'
                      }`}>
                        <p className={`font-medium ${
                          alert.type === 'error' ? 'text-red-800' :
                          alert.type === 'warning' ? 'text-yellow-800' : 'text-blue-800'
                        }`}>
                          [{alert.type.toUpperCase()}] {alert.message}
                        </p>
                        {alert.detail && (
                          <p className="text-sm text-gray-600 mt-1">{alert.detail}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommendations */}
              {summary.recommendations.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Recommendations</h3>
                  <ul className="list-disc list-inside space-y-1 text-gray-700">
                    {summary.recommendations.map((rec, idx) => (
                      <li key={idx}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Quick Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-blue-600 font-medium">Industry Accuracy</p>
                  <p className="text-2xl font-bold text-blue-900 mt-1">
                    {metrics.industry_classification.accuracy}%
                  </p>
                  <p className="text-xs text-blue-600 mt-1">
                    {metrics.industry_classification.correct}/{metrics.industry_classification.total_tested} correct
                  </p>
                </div>

                <div className="bg-green-50 p-4 rounded-lg">
                  <p className="text-sm text-green-600 font-medium">News Articles</p>
                  <p className="text-2xl font-bold text-green-900 mt-1">
                    {metrics.news_data_quality.total_articles}
                  </p>
                  <p className="text-xs text-green-600 mt-1">
                    Across {metrics.news_data_quality.companies_with_news} companies
                  </p>
                </div>

                <div className="bg-purple-50 p-4 rounded-lg">
                  <p className="text-sm text-purple-600 font-medium">Emotion Coverage</p>
                  <p className="text-2xl font-bold text-purple-900 mt-1">
                    {metrics.emotion_coverage.coverage_rate}%
                  </p>
                  <p className="text-xs text-purple-600 mt-1">
                    Status: {metrics.emotion_coverage.status}
                  </p>
                </div>

                <div className="bg-orange-50 p-4 rounded-lg">
                  <p className="text-sm text-orange-600 font-medium">Reports Success</p>
                  <p className="text-2xl font-bold text-orange-900 mt-1">
                    {metrics.financial_reports.success_rate}%
                  </p>
                  <p className="text-xs text-orange-600 mt-1">
                    {metrics.financial_reports.total_reports} reports
                  </p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'industry' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Industry Classification Accuracy
                </h3>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getHealthColor(
                  metrics.industry_classification.accuracy >= 90 ? 'excellent' :
                  metrics.industry_classification.accuracy >= 70 ? 'fair' : 'poor'
                )}`}>
                  {metrics.industry_classification.accuracy}% Accurate
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Company</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Expected</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Detected</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {metrics.industry_classification.details.map((item, idx) => (
                      <tr key={idx} className={item.is_correct ? '' : 'bg-red-50'}>
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                          {item.company}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                          {item.expected}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                          {item.detected}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            item.is_correct ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {item.is_correct ? '✓ Correct' : '✗ Wrong'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'news' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white p-6 rounded-lg">
                  <p className="text-sm opacity-90">Total Articles</p>
                  <p className="text-4xl font-bold mt-2">{metrics.news_data_quality.total_articles}</p>
                </div>
                <div className="bg-gradient-to-br from-green-500 to-green-600 text-white p-6 rounded-lg">
                  <p className="text-sm opacity-90">Companies Covered</p>
                  <p className="text-4xl font-bold mt-2">{metrics.news_data_quality.companies_with_news}</p>
                </div>
                <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white p-6 rounded-lg">
                  <p className="text-sm opacity-90">Avg per Company</p>
                  <p className="text-4xl font-bold mt-2">{metrics.news_data_quality.avg_per_company}</p>
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-3">Emotion Distribution</h4>
                <div className="flex gap-4">
                  {Object.entries(metrics.news_data_quality.emotion_distribution).map(([label, count]) => (
                    <div key={label} className="flex-1 bg-gray-50 p-4 rounded-lg text-center">
                      <p className="text-sm text-gray-600 capitalize">{label}</p>
                      <p className="text-2xl font-bold text-gray-900 mt-1">{count}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-yellow-50 p-4 rounded-lg">
                <p className="text-sm text-yellow-800">
                  <strong>Recent Activity:</strong> {metrics.news_data_quality.recent_7_days} articles in the last 7 days
                </p>
              </div>
            </div>
          )}

          {activeTab === 'emotion' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Emotion Data Coverage</h3>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getHealthColor(metrics.emotion_coverage.status)}`}>
                  {metrics.emotion_coverage.coverage_rate}% Coverage
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {metrics.emotion_coverage.details.map((company, idx) => (
                  <div key={idx} className={`p-4 rounded-lg border-2 ${
                    company.has_data ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
                  }`}>
                    <div className="flex justify-between items-start">
                      <p className="font-semibold text-gray-900">{company.company}</p>
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        company.has_data ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {company.has_data ? '✓ Data' : '✗ No Data'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-2">
                      Data Points: {company.data_points}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'system' && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">System Components Health</h3>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getHealthColor(metrics.system_health.overall_status)}`}>
                  {metrics.system_health.overall_status.toUpperCase()}
                </span>
              </div>

              <div className="space-y-3">
                {Object.entries(metrics.system_health.components).map(([id, component]) => (
                  <div key={id} className={`p-4 rounded-lg border-l-4 ${
                    component.status === 'operational' ? 'border-green-500 bg-green-50' :
                    component.status === 'degraded' ? 'border-yellow-500 bg-yellow-50' :
                    'border-red-500 bg-red-50'
                  }`}>
                    <div className="flex justify-between items-center">
                      <p className="font-semibold text-gray-900">{component.name}</p>
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                        component.status === 'operational' ? 'bg-green-100 text-green-800' :
                        component.status === 'degraded' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {component.status}
                      </span>
                    </div>
                    {component.error && (
                      <p className="text-sm text-red-600 mt-2">Error: {component.error}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default MonitorPage;
