import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';
import ComplianceNote from '../components/ComplianceNote';
import { reportApi, FinancialReport } from '../services/api';

type UploadStep = 'idle' | 'uploading' | 'parsing' | 'analyzing' | 'success' | 'error';

export default function ReportsPage() {
  const [reports, setReports] = useState<FinancialReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [uploadStep, setUploadStep] = useState<UploadStep>('idle');
  const [uploadProgress, setUploadProgress] = useState(0);

  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }
    fetchReports();
  }, [user, router]);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const response = await reportApi.getAll() as any;
      const reportsData = response?.data || response;
      setReports(Array.isArray(reportsData) ? reportsData : []);
    } catch (err) {
      setError('获取财报列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) {
      setSelectedFile(null);
      setError('请选择文件');
      return;
    }

    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel',
      'text/csv'
    ];

    const fileExt = file.name.toLowerCase().split('.').pop();
    const isValidType = allowedTypes.includes(file.type) || ['pdf', 'xlsx', 'xls', 'csv'].includes(fileExt || '');

    if (isValidType) {
      setSelectedFile(file);
      setError('');
    } else {
      setSelectedFile(null);
      setError('仅支持 PDF、Excel (xlsx/xls)、CSV 格式文件');
    }
  };

  const simulateProgress = async (start: number, end: number, duration: number, step: UploadStep) => {
    setUploadStep(step);
    const increment = (end - start) / (duration / 100);
    let current = start;
    while (current < end) {
      await new Promise(resolve => setTimeout(resolve, 100));
      current += increment;
      setUploadProgress(Math.min(current, end));
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setError('');
    setUploadStep('uploading');
    setUploadProgress(0);

    try {
      await simulateProgress(0, 30, 1000, 'uploading');
      await simulateProgress(30, 60, 1500, 'parsing');
      await simulateProgress(60, 90, 2000, 'analyzing');
      await reportApi.upload(selectedFile);
      await simulateProgress(90, 100, 500, 'success');
      setUploadStep('success');
      await fetchReports();
      setSelectedFile(null);
      setTimeout(() => {
        setUploadStep('idle');
        setUploadProgress(0);
      }, 1500);
    } catch (err: any) {
      setUploadStep('error');
      console.error('上传错误详情:', err);

      if (err.code === 'ECONNABORTED') {
        setError('请求超时，服务器响应时间过长。请稍后重试或检查网络连接。');
      } else if (err.response) {
        const status = err.response.status;
        const detail = err.response.data?.detail || err.response.data?.message;

        if (status === 400 && detail) {
          setError(detail);
        } else if (status === 401) {
          setError('登录已过期，请重新登录后重试');
        } else if (status === 413) {
          setError('文件过大（最大支持50MB），请压缩后重新上传');
        } else if (status >= 500) {
          setError(`服务器内部错误 (${status})，请稍后重试`);
        } else {
          setError(`上传失败: ${detail || `HTTP ${status}`}`);
        }
      } else if (err.message) {
        if (err.message.includes('Network Error')) {
          setError('网络连接失败，请检查网络后重试');
        } else if (err.message.includes('timeout')) {
          setError('请求超时，请稍后重试');
        } else {
          setError(`上传失败: ${err.message}`);
        }
      } else {
        setError('上传失败，请检查文件格式和网络后重试');
      }
    } finally {
      setUploading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('zh-CN');
  };

  const formatNumber = (num?: number) => {
    if (!num) return '--';
    return num.toLocaleString();
  };

  const getStepText = (step: UploadStep) => {
    switch (step) {
      case 'uploading': return '正在上传...';
      case 'parsing': return '正在解析财报...';
      case 'analyzing': return 'AI分析中...';
      case 'success': return '分析完成！';
      case 'error': return '分析失败';
      default: return '';
    }
  };

  if (!user) return null;

  return (
    <Layout>
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">财报智能解读</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">上传财报PDF，自动解析关键财务指标</p>
        </div>

        <ComplianceNote />

        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-8 mb-8">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-12 h-12 bg-primary-500/20 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">上传财报</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">支持 PDF、Excel、CSV 格式文件</p>
            </div>
          </div>
          
          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-red-600 dark:text-red-400 text-sm font-medium">{error}</p>
                  <div className="mt-2 text-xs text-red-500 dark:text-red-400 space-y-1">
                    <p>• 检查网络连接是否正常</p>
                    <p>• 确认后端服务 (Render.com) 正在运行</p>
                    <p>• 文件大小不超过50MB，格式为PDF/Excel/CSV</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setError('');
                    if (selectedFile) handleUpload();
                  }}
                  className="ml-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium whitespace-nowrap"
                >
                  重试上传
                </button>
              </div>
            </div>
          )}
          
          {uploadStep !== 'idle' && (
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm text-gray-600 dark:text-gray-400">{getStepText(uploadStep)}</span>
                <span className="text-sm text-gray-500 dark:text-gray-500">{Math.round(uploadProgress)}%</span>
              </div>
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${
                    uploadStep === 'error' ? 'bg-red-500' :
                    uploadStep === 'success' ? 'bg-green-500' :
                    'bg-gradient-to-r from-primary-500 to-blue-500'
                  }`}
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}
          
          <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-10 text-center hover:border-primary-500 dark:hover:border-primary-400 transition-colors">
            <svg className="w-14 h-14 text-gray-400 dark:text-gray-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p className="text-gray-600 dark:text-gray-400 mb-4">点击或拖拽上传财报PDF文件</p>
            <input
              type="file"
              accept="application/pdf"
              onChange={handleFileChange}
              className="block w-full text-sm text-gray-600 dark:text-gray-400 file:mr-4 file:py-2.5 file:px-5 file:rounded-xl file:border-0 file:text-sm file:font-medium file:bg-primary-600 file:text-white hover:file:bg-primary-500 cursor-pointer"
              disabled={uploading}
            />
            {selectedFile && (
              <p className="mt-4 text-sm text-green-600 dark:text-green-400 flex items-center justify-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                已选择: {selectedFile.name}
              </p>
            )}
          </div>
          
          {selectedFile && uploadStep === 'idle' && (
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="mt-6 w-full py-3.5 bg-gradient-to-r from-primary-600 to-blue-600 hover:from-primary-500 hover:to-blue-500 disabled:from-gray-400 disabled:to-gray-400 text-white font-semibold rounded-xl transition-all"
            >
              {uploading ? '处理中...' : '开始解析财报'}
            </button>
          )}
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700">
          <div className="px-8 py-5 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-blue-500/20 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">解析历史</h2>
            </div>
            <span className="text-sm text-gray-500 dark:text-gray-400">{reports.length} 条记录</span>
          </div>
          
          {loading ? (
            <div className="py-16 text-center">
              <div className="animate-spin rounded-full h-10 w-10 border-2 border-primary-500 border-t-transparent mx-auto" />
              <p className="mt-4 text-gray-600 dark:text-gray-400">加载中...</p>
            </div>
          ) : reports.length === 0 ? (
            <div className="py-16 text-center">
              <svg className="w-16 h-16 text-gray-400 dark:text-gray-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-gray-600 dark:text-gray-400">暂无财报解析记录</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {reports.map((report) => (
                <div key={report.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <h3 className="text-base font-semibold text-gray-900 dark:text-white">{report.company_name}</h3>
                      {report.stock_code && (
                        <span className="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">{report.stock_code}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                        report.status === 'success' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' :
                        report.status === 'processing' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400' :
                        'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                      }`}>
                        {report.status === 'success' ? '成功' :
                         report.status === 'processing' ? '处理中' : '失败'}
                      </span>
                      <span className="text-xs text-gray-400">{formatDate(report.upload_time)}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-6 mb-2">
                    <div className="text-center">
                      <p className="text-[10px] text-gray-500 dark:text-gray-400">营收</p>
                      <p className="text-sm font-semibold text-gray-900 dark:text-white">{formatNumber(report.revenue)}万</p>
                    </div>
                    <div className="text-center">
                      <p className="text-[10px] text-gray-500 dark:text-gray-400">净利润</p>
                      <p className="text-sm font-semibold text-gray-900 dark:text-white">{formatNumber(report.net_profit)}万</p>
                    </div>
                    <div className="text-center">
                      <p className="text-[10px] text-gray-500 dark:text-gray-400">负债率</p>
                      <p className="text-sm font-semibold text-gray-900 dark:text-white">{report.debt_ratio || '--'}%</p>
                    </div>
                    <div className="text-center">
                      <p className="text-[10px] text-gray-500 dark:text-gray-400">毛利率</p>
                      <p className="text-sm font-semibold text-gray-900 dark:text-white">{report.gross_margin || '--'}%</p>
                    </div>
                  </div>

                  {report.ai_summary && (
                    <div className="bg-primary-50 dark:bg-primary-900/10 rounded-lg p-3 border border-primary-100 dark:border-primary-800 mt-2">
                      <p className="text-xs text-gray-700 dark:text-gray-300 line-clamp-2">{report.ai_summary}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
