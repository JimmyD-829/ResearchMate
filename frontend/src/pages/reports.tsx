import { useState, useEffect, useRef } from 'react';
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

  
  // 分页状态
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 5;

  
  // 失败详情弹窗状态
  const [selectedFailedReport, setSelectedFailedReport] = useState<FinancialReport | null>(null);

  // 解析历史容器ref（用于分页滚动定位）
  const historySectionRef = useRef<HTMLDivElement>(null);

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
      setError('获取报告列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 分页计算
  const totalPages = Math.ceil(reports.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentReports = reports.slice(startIndex, endIndex);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    // 滚动到解析历史模块位置（而不是页面顶部）
    setTimeout(() => {
      historySectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
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

  const loadSampleReport = async () => {
    console.log('🎉 点击了示例分析按钮');
    setUploading(true);
    setError('');
    setUploadStep('uploading');
    setUploadProgress(0);
    
    try {
      console.log('寮€濮嬫ā鎷熻繘搴?..');
      await simulateProgress(0, 30, 800, 'uploading');
      console.log('上传完成，开始解析...');
      await simulateProgress(30, 60, 1200, 'parsing');
      console.log('解析完成，开始分析...');
      await simulateProgress(60, 90, 1500, 'analyzing');

      console.log('鐢熸垚绀轰緥鏁版嵁...');
      const sampleData: FinancialReport = {
        id: 'sample-' + Date.now(),
        user_id: 'demo-user',
        company_name: '璐靛窞鑼呭彴',
        stock_code: '600519',
        report_period: '2025骞村害',
        upload_time: new Date().toISOString(),
        status: 'success' as const,
        revenue: 147699000000,
        net_profit: 74800000000,
        cash_flow: 82500000000,
        debt_ratio: 18.5,
        gross_margin: 91.5,
        ai_summary: `## 贵州茅台 (600519) 2025年度财务分析报告

### 📊 核心财务指标

**营业收入**: 1,476.99亿元 (+15.2% YoY)
**净利润**: 748.00亿元 (+16.8% YoY)
**经营现金流**: 825.00亿元 (+12.3% YoY)
**资产负债率**: 18.5% (-1.2pp)
**毛利率**: 91.5% (+0.3pp)

### 🔍 关键发现

#### ✅ **优势亮点**
1. **盈利能力卓越**: 毛利率高达91.5%，位居白酒行业第一
2. **现金流充裕**: 经营性现金流/净利润比率超10%，现金创造能力强大
3. **品牌价值深厚**: 茅台品牌价值持续提升，定价权稳固
4. **财务结构稳健**: 资产负债率仅18.5%，几乎无有息负债
5. **分红慷慨**: 预计2025年分红率超52%，股息率约2.5%

#### ⚠️ **风险提示**
1. **估值偏高**: 当前PE(TTM)约35倍，高于历史均值
2. **增速放缓**: 营收增速从20%+降至15%，高基数效应显现
3. **政策风险**: 白酒消费税改革可能影响利润率
4. **竞争加剧**: 高端白酒市场竞争加剧，五粮液、国窖1573追赶
5. **库存压力**: 经销商库存周期延长至45天（vs 历史平均30天）

### 💡 投资建议

**璇勭骇**: 猸愨瓙猸愨瓙 (鎺ㄨ崘鎸佹湁)

**鐩爣浠?*: 1,950-2,050鍏?(鍩轰簬2026骞?2x PE)

**鏍稿績閫昏緫**:
- 鐭湡锛氭槬鑺傛椇瀛?鎻愪环棰勬湡鍌寲鑲′环
- 涓湡锛氱洿閿€娓犻亾鍗犳瘮鎻愬崌鑷?0%+锛屽鍘氬埄娑?- 闀挎湡锛氬浗闄呭寲甯冨眬+i鑼呭彴鏁板瓧鍖栬祴鑳?
**椋庨櫓鏀剁泭姣?*: 鍦ㄥ綋鍓嶄环浣嶅叿澶囬槻寰″睘鎬э紝閫傚悎闀挎湡閰嶇疆`
      };

      console.log('示例数据生成完成，更新状态');
      await simulateProgress(90, 100, 300, 'success');
      setReports(prev => [sampleData, ...prev]);
      setUploadStep('success');
      setSelectedFile(null);
      
      setTimeout(() => {
        setUploadStep('idle');
        setUploadProgress(0);
      }, 2000);
      
      console.log('✅ 示例分析完成');
    } catch (err) {
      console.error('❌ 加载示例数据失败:', err);
      setError('加载示例数据失败: ' + (err as Error).message);
      setUploadStep('error');
    } finally {
      setUploading(false);
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
        setError('请求超时，服务器响应时间过长。请稍后重试或检查网络连接');
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
          setError(`服务器内部错误(${status})，请稍后重试`);
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
      case 'success': return '分析完成';
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
                  <div className="mt-3 text-xs text-red-500 dark:text-red-400 space-y-1.5">
                    <p>🔍 **常见原因及解决方案**:</p>
                    <p>⏱️ **服务器超时**: Render免费版单次请求需50秒，请耐心等待或使用示例数据</p>
                    <p>📄 **PDF格式问题**: 扫描件/加密PDF无法解析，请使用文字版PDF</p>
                    <p>🌐 **网络连接**: 检查网络，或尝试刷新页面后重试</p>
                    <p>📁 **文件大小**: 请确保文件小于10MB</p>
                    <div className="mt-2 pt-2 border-t border-red-200 dark:border-red-700">
                      <p className="font-medium text-red-600 dark:text-red-400">💡 推荐方案: 点击下方"📋 查看示例分析"按钮，立即体验完整功能！</p>
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setError('');
                    if (selectedFile) handleUpload();
                  }}
                  className="ml-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium whitespace-nowrap"
                >
                  重新上传
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
                宸查€夋嫨: {selectedFile.name}
              </p>
            )}
          </div>

          <div className="mt-6 text-center">
            <div className="relative inline-block">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl blur opacity-20"></div>
              <button
                onClick={loadSampleReport}
                disabled={uploading}
                className="relative px-8 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 disabled:from-gray-400 disabled:to-gray-400 text-white font-semibold rounded-xl transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              >
                📋 查看示例分析（无需上传）
            </div>
            <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">体验完整分析功能，了解报告样式</p>
          </div>
          
          {selectedFile && uploadStep === 'idle' && (
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="mt-6 w-full py-3.5 bg-gradient-to-r from-primary-600 to-blue-600 hover:from-primary-500 hover:to-blue-500 disabled:from-gray-400 disabled:to-gray-400 text-white font-semibold rounded-xl transition-all"
            >
              {uploading ? '处理中...' : '开始解析分析'}
            </button>
          )}
        </div>

        <div ref={historySectionRef} className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700">
          <div className="px-8 py-5 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-blue-500/20 rounded-xl flex items-center justify-center">
                <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">解析历史</h2>
            </div>
            <span className="text-sm text-gray-500 dark:text-gray-400">{reports.length} 鏉¤褰?/span>
          </div>
          
          {loading ? (
            <div className="py-16 text-center">
              <div className="animate-spin rounded-full h-10 w-10 border-2 border-primary-500 border-t-transparent mx-auto" />
              <p className="mt-4 text-gray-600 dark:text-gray-400">鍔犺浇涓?..</p>
            </div>
          ) : reports.length === 0 ? (
            <div className="py-16 text-center">
              <svg className="w-16 h-16 text-gray-400 dark:text-gray-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-gray-600 dark:text-gray-400">暂无财报解析记录</p>
              <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">上传财报或点击"查看示例分析"开始体验</p>
            </div>
          ) : (
            <>
              {/* 鍒嗛〉淇℃伅 */}
              <div className="px-6 py-3 bg-gray-50 dark:bg-gray-700/30 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  鏄剧ず绗?<strong>{startIndex + 1}-{Math.min(endIndex, reports.length)}</strong> 鏉★紝鍏?<strong>{reports.length}</strong> 鏉?                </span>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    鈫?涓婁竴椤?                  </button>
                  
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                    <button
                      key={page}
                      onClick={() => handlePageChange(page)}
                      className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                        currentPage === page
                          ? 'bg-primary-600 text-white border-primary-600'
                          : 'border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600'
                      }`}
                    >
                      {page}
                    </button>
                  ))}
                  
                  <button
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1.5 text-sm rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    涓嬩竴椤?鈫?                  </button>
                </div>
              </div>

              {/* 鎶ュ憡鍒楄〃 */}
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {currentReports.map((report) => (
                  <div key={report.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <h3 className="text-base font-semibold text-gray-900 dark:text-white">{report.company_name || report.id?.includes("sample") ? "示例分析" : "未知"}</h3>
                        {report.stock_code && (
                          <span className="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded">{report.stock_code}</span>
                        )}
                        {report.report_period && (
                          <span className="text-xs text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 px-2 py-0.5 rounded">{report.report_period}</span>
                        )}
                      </div>
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => {
                            if (report.status !== 'success') {
                              setSelectedFailedReport(report);
                            }
                          }}
                          className={`px-2 py-0.5 text-xs font-medium rounded-full transition-all ${
                            report.status === 'success' 
                              ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 cursor-default' 
                              : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 hover:bg-red-200 dark:hover:bg-red-900/50 cursor-pointer hover:shadow-md'
                          }`}
                          title={report.status !== 'success' ? '点击查看失败原因' : ''}
                        >
                          {report.status === 'success' ? '鉁?鎴愬姛' :
                           report.status === 'processing' ? '⏳ 处理中' : '❌ 失败'}
                        </button>
                        <span className="text-xs text-gray-400">{formatDate(report.upload_time)}</span>
                      </div>
                    </div>

                    <div className="flex items-center gap-6 mb-2">
                      <div className="text-center min-w-[80px]">
                        <p className="text-[10px] text-gray-500 dark:text-gray-400">钀ユ敹</p>
                        <p className={`text-sm font-semibold ${report.revenue ? 'text-gray-900 dark:text-white' : 'text-gray-400'}`}>
                          {formatNumber(report.revenue)}{report.revenue ? '浜? : ''}
                        </p>
                      </div>
                      <div className="text-center min-w-[80px]">
                        <p className="text-[10px] text-gray-500 dark:text-gray-400">鍑€鍒╂鼎</p>
                        <p className={`text-sm font-semibold ${report.net_profit ? 'text-gray-900 dark:text-white' : 'text-gray-400'}`}>
                          {formatNumber(report.net_profit)}{report.net_profit ? '浜? : ''}
                        </p>
                      </div>
                      <div className="text-center min-w-[70px]">
                        <p className="text-[10px] text-gray-500 dark:text-gray-400">璐熷€虹巼</p>
                        <p className={`text-sm font-semibold ${report.debt_ratio ? 'text-gray-900 dark:text-white' : 'text-gray-400'}`}>
                          {report.debt_ratio || '--'}%
                        </p>
                      </div>
                      <div className="text-center min-w-[70px]">
                        <p className="text-[10px] text-gray-500 dark:text-gray-400">姣涘埄鐜?/p>
                        <p className={`text-sm font-semibold ${report.gross_margin ? 'text-gray-900 dark:text-white' : 'text-gray-400'}`}>
                          {report.gross_margin || '--'}%
                        </p>
                      </div>
                    </div>

                    {report.ai_summary && report.status === 'success' && (
                      <div className="bg-primary-50 dark:bg-primary-900/10 rounded-lg p-3 border border-primary-100 dark:border-primary-800 mt-2 cursor-pointer hover:bg-primary-100 dark:hover:bg-primary-900/20 transition-colors group">
                        <p className="text-xs text-gray-700 dark:text-gray-300 line-clamp-2 group-hover:line-clamp-none">
                          {report.ai_summary}
                        </p>
                        <p className="text-[10px] text-primary-600 dark:text-primary-400 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          点击展开完整报告 →                        </p>
                      </div>
                    )}

                    {report.status !== 'success' && !report.ai_summary && (
                      <div className="mt-2 p-2 bg-yellow-50 dark:bg-yellow-900/10 rounded text-xs text-yellow-700 dark:text-yellow-400">
                        💡 点击上方"失败"标签查看详细原因和解决方案
                    )}
                  </div>
                ))}
              </div>

              {/* 搴曢儴鍒嗛〉鎺т欢 */}
              {totalPages > 1 && (
                <div className="px-6 py-4 bg-gray-50 dark:bg-gray-700/30 border-t border-gray-200 dark:border-gray-700 flex items-center justify-center gap-2">
                  <button
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="px-4 py-2 text-sm rounded-lg bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    鈫?涓婁竴椤?                  </button>
                  
                  <span className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">
                    绗?<strong>{currentPage}</strong> / {totalPages} 椤?                  </span>
                  
                  <button
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="px-4 py-2 text-sm rounded-lg bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    涓嬩竴椤?鈫?                  </button>
                </div>
              )}
            </>
          )}
        </div>

        {/* 失败详情弹窗 */}
        {selectedFailedReport && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedFailedReport(null)}>
            <div 
              className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-lg w-full max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              {/* 寮圭獥澶撮儴 */}
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                    ❌ 解析失败详情
                  </h3>
                  <button
                    onClick={() => setSelectedFailedReport(null)}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                  文件: {selectedFailedReport.id?.includes('sample') ? '示例分析' : (selectedFailedReport.company_name || '未知文件')}
                  {selectedFailedReport.upload_time && ` 路 ${formatDate(selectedFailedReport.upload_time)}`}
                </p>
              </div>

              {/* 寮圭獥鍐呭 */}
              <div className="p-6 space-y-4">
                {/* 鍙兘鐨勫師鍥?*/}
                <div className="bg-red-50 dark:bg-red-900/10 rounded-lg p-4 border border-red-200 dark:border-red-800">
                  <h4 className="font-semibold text-red-700 dark:text-red-400 mb-2 flex items-center gap-2">
                    🔍 可能的失败原因
                  <ul className="space-y-2 text-sm text-red-600 dark:text-red-300">
                    <li className="flex items-start gap-2">
                      <span>鈥?/span>
                      <span><strong>PDF格式问题</strong>: 文件可能是扫描件（图片格式），系统无法提取文本内容</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>鈥?/span>
                      <span><strong>鏂囦欢鍔犲瘑</strong>: PDF璁剧疆浜嗗瘑鐮佷繚鎶ゆ垨鏉冮檺闄愬埗</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>鈥?/span>
                      <span><strong>文件损坏</strong>: 上传过程中文件可能已损坏或不完整</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>鈥?/span>
                      <span><strong>网络超时</strong>: Render免费版响应时间较长，请求可能超时</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>鈥?/span>
                      <span><strong>服务器错误</strong>: 后端服务暂时不可用或正在维护</span>
                    </li>
                  </ul>
                </div>

                {/* 瑙ｅ喅鏂规 */}
                <div className="bg-blue-50 dark:bg-blue-900/10 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                  <h4 className="font-semibold text-blue-700 dark:text-blue-400 mb-2 flex items-center gap-2">
                    💡 推荐解决方案
                  </h4>
                  <ul className="space-y-2 text-sm text-blue-600 dark:text-blue-300">
                    <li className="flex items-start gap-2">
                      <span>鉁?/span>
                      <span><strong>使用文字版PDF</strong>: 确保PDF包含可选的文本层，而非扫描图片</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>鉁?/span>
                      <span><strong>尝试Excel格式</strong>: 如果有Excel版本的财报，解析成功率更高</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>鉁?/span>
                      <span><strong>鍘嬬缉鏂囦欢澶у皬</strong>: 纭繚鏂囦欢灏忎簬50MB锛屽繀瑕佹椂鍘嬬缉鍥剧墖</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>鉁?/span>
                      <span><strong>检查网络连接</strong>: 确保网络稳定，或稍后重试</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>鉁?/span>
                      <span><strong>使用示例功能</strong>: 点击"📋 查看示例分析"体验完整功能</span>
                    </li>
                  </ul>
                </div>

                {/* 技术细节 */}
                <div className="bg-gray-50 dark:bg-gray-700/30 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                    📊 技术信息
                  <div className="grid grid-cols-2 gap-2 text-xs text-gray-600 dark:text-gray-400">
                    <div>
                      <span className="font-medium">鎶ュ憡ID:</span>
                      <code className="ml-1 bg-gray-200 dark:bg-gray-600 px-1 rounded">{selectedFailedReport.id}</code>
                    </div>
                    <div>
                      <span className="font-medium">鐘舵€?</span>
                      <span className="ml-1 text-red-600 font-medium">{selectedFailedReport.status || 'failed'}</span>
                    </div>
                    <div className="col-span-2">
                      <span className="font-medium">上传时间:</span>
                      <span className="ml-1">{selectedFailedReport.upload_time ? new Date(selectedFailedReport.upload_time).toLocaleString('zh-CN') : '未知'}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* 寮圭獥搴曢儴鎸夐挳 */}
              <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex gap-3">
                <button
                  onClick={() => setSelectedFailedReport(null)}
                  className="flex-1 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  鍏抽棴
                </button>
                <button
                  onClick={() => {
                    setSelectedFailedReport(null);
                    setError('');
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                  className="flex-1 px-4 py-2.5 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-medium rounded-lg hover:from-purple-500 hover:to-pink-500 transition-all shadow-lg"
                >
                  鉁?浣跨敤绀轰緥鏁版嵁
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}






