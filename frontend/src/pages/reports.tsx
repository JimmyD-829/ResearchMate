import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useRouter } from 'next/router';
import Layout from '../components/Layout';
import { reportApi, FinancialReport } from '../services/api';

export default function ReportsPage() {
  const [reports, setReports] = useState<FinancialReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState('');
  
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

  const handleUpload = async () => {
    if (!selectedFile) return;
    
    setUploading(true);
    setError('');
    
    try {
      await reportApi.upload(selectedFile);
      await fetchReports();
      setSelectedFile(null);
    } catch (err) {
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

  if (!user) return null;

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">财报解析</h1>
            <p className="text-gray-500 mt-1">上传财报PDF，自动解析关键财务指标</p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">上传财报</h2>
          
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}
          
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-primary-400 transition">
            <span className="text-4xl block mb-4">📄</span>
            <p className="text-gray-600 mb-4">点击或拖拽上传财报PDF文件</p>
            <input
              type="file"
              accept="application/pdf"
              onChange={handleFileChange}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-600 file:text-white hover:file:bg-primary-700 cursor-pointer"
            />
            {selectedFile && (
              <p className="mt-4 text-sm text-green-600">已选择: {selectedFile.name}</p>
            )}
          </div>
          
          {selectedFile && (
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="mt-4 w-full py-3 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:bg-gray-400 transition"
            >
              {uploading ? '上传中...' : '开始解析'}
            </button>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-lg">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-800">解析历史</h2>
          </div>
          
          {loading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-10 w-10 border-4 border-primary-400 border-t-transparent mx-auto"></div>
              <p className="mt-4 text-gray-500">加载中...</p>
            </div>
          ) : reports.length === 0 ? (
            <div className="p-16 text-center">
              <span className="text-4xl">📊</span>
              <p className="mt-4 text-gray-500">暂无财报解析记录</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {reports.map((report) => (
                <div key={report.id} className="p-6 hover:bg-gray-50 transition">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="font-semibold text-gray-800">{report.company_name}</h3>
                      {report.stock_code && (
                        <span className="text-sm text-gray-500">{report.stock_code}</span>
                      )}
                    </div>
                    <span className={`px-3 py-1 text-xs font-medium rounded-full ${
                      report.status === 'success' ? 'bg-green-100 text-green-700' :
                      report.status === 'processing' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {report.status === 'success' ? '解析成功' :
                       report.status === 'processing' ? '解析中' : '解析失败'}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-xs text-gray-500 mb-1">营收</p>
                      <p className="font-semibold text-gray-800">{formatNumber(report.revenue)} 万元</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-xs text-gray-500 mb-1">净利润</p>
                      <p className="font-semibold text-gray-800">{formatNumber(report.net_profit)} 万元</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-xs text-gray-500 mb-1">负债率</p>
                      <p className="font-semibold text-gray-800">{report.debt_ratio || '未识别'}%</p>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-xs text-gray-500 mb-1">毛利率</p>
                      <p className="font-semibold text-gray-800">{report.gross_margin || '未识别'}%</p>
                    </div>
                  </div>
                  
                  {report.ai_summary && (
                    <div className="bg-blue-50 rounded-lg p-4">
                      <p className="text-xs text-blue-600 mb-1">AI摘要</p>
                      <p className="text-sm text-gray-700">{report.ai_summary}</p>
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
