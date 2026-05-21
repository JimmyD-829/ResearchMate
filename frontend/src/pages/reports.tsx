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
      const response = await reportApi.getAll();
      setReports(response.data);
    } catch (err) {
      setError('获取财报列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setError('');
    } else {
      setSelectedFile(null);
      setError('请选择PDF文件');
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
    } catch (err) {
      setUploadStep('error');
      setError('上传失败，请重试');
    } finally {
      setUploading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('zh-CN');
  };

  const formatNumber = (num?: number) => {
    if (!num) return '未识别';
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
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 dark:text-white">财报智能解读</h1>
            <p className="text-gray-500 dark:text-gray-400 mt-1">上传财报PDF，自动解析关键财务指标</p>
          </div>
        </div>

        <ComplianceNote />

        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8 mb-8 border border-gray-100 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-6">📄 上传财报</h2>
          
          {error && (
            <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-lg text-red-600 dark:text-red-300">
              {error}
            </div>
          )}
          
          {uploadStep !== 'idle' && (
            <div className="mb-6">
              <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">{getStepText(uploadStep)}</p>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all duration-300 ${
                    uploadStep === 'error' ? 'bg-red-500' :
                    uploadStep === 'success' ? 'bg-green-500' :
                    'bg-primary-500'
                  }`}
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-right text-xs text-gray-500 dark:text-gray-400 mt-1">{Math.round(uploadProgress)}%</p>
            </div>
          )}
          
          <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-10 text-center hover:border-primary-400 dark:hover:border-primary-500 transition-colors">
            <span className="text-5xl block mb-4">📊</span>
            <p className="text-gray-600 dark:text-gray-300 mb-4">点击或拖拽上传财报PDF文件</p>
            <input
              type="file"
              accept="application/pdf"
              onChange={handleFileChange}
              className="block w-full text-sm text-gray-500 dark:text-gray-400 file:mr-4 file:py-3 file:px-6 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-600 file:text-white hover:file:bg-primary-700 cursor-pointer"
              disabled={uploading}
            />
            {selectedFile && (
              <p className="mt-4 text-sm text-green-600 dark:text-green-400">
                已选择: {selectedFile.name}
              </p>
            )}
          </div>
          
          {selectedFile && uploadStep === 'idle' && (
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="mt-6 w-full py-4 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white font-medium rounded-xl transition-all shadow-lg"
            >
              {uploading ? '处理中...' : '开始解析财报'}
            </button>
          )}
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-100 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-800 dark:text-white">📋 解析历史</h2>
          </div>
          
          {loading ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-10 w-10 border-4 border-primary-400 border-t-transparent mx-auto" />
              <p className="mt-4 text-gray-500 dark:text-gray-400">加载中...</p>
            </div>
          ) : reports.length === 0 ? (
            <div className="p-16 text-center">
              <span className="text-5xl">📄</span>
              <p className="mt-4 text-gray-500 dark:text-gray-400">暂无财报解析记录</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-700">
              {reports.map((report) => (
                <div key={report.id} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                  <div className="flex items-center justify-between mb-6">
                    <div>
                      <h3 className="text-xl font-semibold text-gray-800 dark:text-white">{report.company_name}</h3>
                      {report.stock_code && (
                        <span className="text-sm text-gray-500 dark:text-gray-400">{report.stock_code}</span>
                      )}
                    </div>
                    <span className={`px-4 py-1.5 text-sm font-medium rounded-full ${
                      report.status === 'success' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' :
                      report.status === 'processing' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400' :
                      'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                    }`}>
                      {report.status === 'success' ? '解析成功' :
                       report.status === 'processing' ? '解析中' : '解析失败'}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-5">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">营收</p>
                      <p className="text-xl font-bold text-gray-800 dark:text-white">{formatNumber(report.revenue)} 万元</p>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-5">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">净利润</p>
                      <p className="text-xl font-bold text-gray-800 dark:text-white">{formatNumber(report.net_profit)} 万元</p>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-5">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">负债率</p>
                      <p className="text-xl font-bold text-gray-800 dark:text-white">{report.debt_ratio || '未识别'}%</p>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-700 rounded-xl p-5">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">毛利率</p>
                      <p className="text-xl font-bold text-gray-800 dark:text-white">{report.gross_margin || '未识别'}%</p>
                    </div>
                  </div>
                  
                  {report.ai_summary && (
                    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-5 border border-blue-100 dark:border-blue-800">
                      <p className="text-xs text-blue-600 dark:text-blue-400 mb-2 flex items-center gap-2">
                        <span>🤖</span> AI摘要
                      </p>
                      <p className="text-gray-700 dark:text-gray-300">{report.ai_summary}</p>
                    </div>
                  )}
                  
                  <p className="mt-4 text-xs text-gray-400">上传时间: {formatDate(report.upload_time)}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
