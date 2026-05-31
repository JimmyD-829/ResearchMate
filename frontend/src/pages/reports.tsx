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
      console.log('开始模拟进度...');
      await simulateProgress(0, 30, 800, 'uploading');
      console.log('上传完成，开始解析...');
      await simulateProgress(30, 60, 1200, 'parsing');
      console.log('解析完成，开始分析...');
      await simulateProgress(60, 90, 1500, 'analyzing');

      console.log('生成示例数据...');
      const sampleData: FinancialReport = {
        id: 'sample-' + Date.now(),
        user_id: 'demo-user',
        company_name: '贵州茅台',
        stock_code: '600519',
        report_period: '2025年度',
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
1. **盈利能力卓越**: 毛利率高达91.5%，位居A股榜首
2. **现金流充裕**: 经营性现金流/净利润比率超110%，现金创造能力强大
3. **品牌护城河深厚**: 茅台品牌价值持续提升，定价权稳固
4. **财务结构健康**: 资产负债率仅18.5%，几乎无有息负债
5. **分红慷慨**: 预计2025年分红率超52%，股息率约2.5%

#### ⚠️ **风险提示**
1. **估值偏高**: 当前PE(TTM)约35倍，高于历史均值
2. **增速放缓**: 营收增速从20%+降至15%，高基数效应显现
3. **政策风险**: 白酒消费税改革可能影响利润率
4. **竞争加剧**: 高端白酒市场竞争加剧，五粮液、国窖1573等追赶
5. **库存压力**: 经销商库存周期延长至45天（vs 历史平均30天）

### 💡 投资建议

**评级**: 🟢🟢🟢 (推荐持有)

**目标价**: 1,950-2,050元 (基于2026年32x PE)

**核心逻辑**:
- 短期: 春节旺季 + 提价预期强化股价
- 中期: 直销渠道占比提升至40%+，增厚利润
- 长期: 国际化布局+i茅台数字化赋能
**风险收益比**: 在当前价位具备防御属性，适合长期配置`
      };

      console.log('示例数据生成完成，更新状态...');
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

      if (!err.response) {
        if (err.message?.includes('timeout')) {
          setError('请求超时，服务器响应时间过长。请稍后重试或检查网络连接');
        } else if (err.message?.includes('Network Error')) {
          setError('网络连接失败，请检查网络后重试');
        } else {
          setError('上传失败，请检查文件格式和网络后重试');
        }
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
                    <p>💡 <strong>常见问题解决方案：</strong></p>
                    <ul className="list-disc list-inside space-y-1 ml-2">
                      <li>确保使用<strong>文字版PDF</strong>（非扫描件）</li>
                      <li>文件大小不超过 <strong>50MB</strong></li>
                      <li>检查网络连接是否稳定</li>
                      <li>如持续失败，可尝试使用下方示例功能体验完整流程</li>
                    </ul>
                  </div>
                </div>
                <button
                  onClick={() => setError('')}
                  className="ml-4 text-red-400 hover:text-red-600"
                >
                  ✕
                </button>
              </div>
            </div>
          )}

          {/* 技术细节 */}
          <div className="mb-6">
            <input
              type="file"
              id="file-upload"
              onChange={handleFileChange}
              accept=".pdf,.xlsx,.xls,.csv"
              className="hidden"
              disabled={uploading}
            />
            {!selectedFile ? (
              <label
                htmlFor="file-upload"
                className={`flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-xl cursor-pointer transition-colors ${
                  uploading
                    ? 'border-gray-300 bg-gray-50 cursor-not-allowed'
                    : 'border-gray-300 hover:border-primary-400 hover:bg-primary-50/30'
                }`}
              >
                <svg className={`w-10 h-10 mb-2 ${uploading ? 'text-gray-400' : 'text-gray-500'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <span className={`text-sm ${uploading ? 'text-gray-400' : 'text-gray-600'}`}>
                  {uploading ? '处理中...' : '点击或拖拽文件到此处'}
                </span>
                <span className="text-xs text-gray-400 mt-1">支持 PDF、Excel、CSV 格式文件</span>
              </label>
            ) : (
              <div className="flex items-center justify-between p-4 bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-800 rounded-xl">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-green-100 dark:bg-green-800 rounded-lg flex items-center justify-center">
                    <svg className="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-green-700 dark:text-green-300">{selectedFile.name}</p>
                    <p className="text-xs text-green-600 dark:text-green-400">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setSelectedFile(null);
                    setError('');
                  }}
                  className="px-3 py-1.5 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                >
                  移除
                </button>
              </div>
            )}
          </div>

          {/* 进度条 */}
          {(uploading || uploadStep !== 'idle') && (
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{getStepText(uploadStep)}</span>
                <span className="text-sm text-gray-500 dark:text-gray-400">{Math.round(uploadProgress)}%</span>
              </div>
              <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full transition-all duration-300 ease-out rounded-full"
                  style={{
                    width: `${uploadProgress}%`,
                    backgroundColor: uploadStep === 'success' ? '#10B981' :
                                     uploadStep === 'error' ? '#EF4444' :
                                     uploadStep === 'analyzing' ? '#8B5CF6' :
                                     uploadStep === 'parsing' ? '#F59E0B' : '#3B82F6'
                  }}
                />
              </div>
            </div>
          )}

          {/* 操作按钮 */}
          <div className="flex gap-4">
            <button
              onClick={handleUpload}
              disabled={!selectedFile || uploading}
              className="flex-1 px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 disabled:from-gray-400 disabled:to-gray-400 text-white font-semibold rounded-xl transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:transform-none"
            >
              {uploading ? getStepText(uploadStep) : '开始解析'}
            </button>

            <button
              onClick={loadSampleReport}
              disabled={uploading}
              className="relative px-8 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 disabled:from-gray-400 disabled:to-gray-400 text-white font-semibold rounded-xl transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 disabled:transform-none"
            >
              📋 查看示例分析（无需上传）
            </button>
          </div>
        </div>

        {/* 解析历史 */}
        <div ref={historySectionRef} className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="px-6 py-4 bg-gradient-to-r from-gray-50 to-white dark:from-gray-700/50 dark:to-gray-800 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <svg className="w-5 h-5 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                解析历史
              </h2>
              <span className="text-sm text-gray-500 dark:text-gray-400">{reports.length} 条记录</span>
            </div>
          </div>

          {loading ? (
            <div className="p-12 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
              <p className="mt-4 text-gray-500 dark:text-gray-400">加载解析历史...</p>
            </div>
          ) : currentReports.length === 0 ? (
            <div className="p-12 text-center">
              <svg className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-gray-500 dark:text-gray-400">暂无财报解析记录</p>
              <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">上传第一份财报或点击上方"查看示例"</p>
            </div>
          ) : (
            <>
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {currentReports.map((report) => (
                  <div key={report.id} className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors cursor-pointer group">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-base font-semibold text-gray-900 dark:text-white truncate">
                            {report.company_name}
                          </h3>
                          <span className={`px-2 py-0.5 text-xs font-medium rounded ${
                            report.status === 'success'
                              ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                              : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                          }`}>
                            {report.status === 'success' ? '✅ 成功' : '❌ 失败'}
                          </span>
                          {report.stock_code && (
                            <span className="text-sm text-gray-500 dark:text-gray-400">{report.stock_code}</span>
                          )}
                        </div>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
                          {report.report_period} · {formatDate(report.upload_time)}
                        </p>

                        {report.status === 'success' && (
                          <div className="grid grid-cols-5 gap-4 mt-3">
                            <div className="text-center min-w-[70px]">
                              <p className="text-[10px] text-gray-500 dark:text-gray-400">营收</p>
                              <p className={`text-sm font-semibold ${report.revenue ? 'text-gray-900 dark:text-white' : 'text-gray-400'}`}>
                                {formatNumber(report.revenue)}{report.revenue ? '亿' : ''}
                              </p>
                            </div>
                            <div className="text-center min-w-[70px]">
                              <p className="text-[10px] text-gray-500 dark:text-gray-400">净利润</p>
                              <p className={`text-sm font-semibold ${report.net_profit ? 'text-gray-900 dark:text-white' : 'text-gray-400'}`}>
                                {formatNumber(report.net_profit)}{report.net_profit ? '亿' : ''}
                              </p>
                            </div>
                            <div className="text-center min-w-[70px]">
                              <p className="text-[10px] text-gray-500 dark:text-gray-400">资产负债率</p>
                              <p className={`text-sm font-semibold ${report.debt_ratio ? 'text-gray-900 dark:text-white' : 'text-gray-400'}`}>
                                {report.debt_ratio || '--'}%
                              </p>
                            </div>
                            <div className="text-center min-w-[70px]">
                              <p className="text-[10px] text-gray-500 dark:text-gray-400">毛利率</p>
                              <p className={`text-sm font-semibold ${report.gross_margin ? 'text-gray-900 dark:text-white' : 'text-gray-400'}`}>
                                {report.gross_margin || '--'}%
                              </p>
                            </div>
                          </div>
                        )}

                        {report.ai_summary && report.status === 'success' && (
                          <div className="bg-primary-50 dark:bg-primary-900/10 rounded-lg p-3 border border-primary-100 dark:border-primary-800 mt-2 cursor-pointer hover:bg-primary-100 dark:hover:bg-primary-900/20 transition-colors group">
                            <p className="text-xs text-gray-700 dark:text-gray-300 line-clamp-2 group-hover:line-clamp-none">
                              {report.ai_summary}
                            </p>
                            <p className="text-[10px] text-primary-600 dark:text-primary-400 mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              点击展开完整报告 →
                            </p>
                          </div>
                        )}

                        {report.status !== 'success' && !report.ai_summary && (
                          <div className="mt-2 p-2 bg-yellow-50 dark:bg-yellow-900/10 rounded text-xs text-yellow-700 dark:text-yellow-400">
                            💡 点击上方"失败"标签查看详细原因和解决方案
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* 底部分页控件 */}
              {totalPages > 1 && (
                <div className="px-6 py-4 bg-gray-50 dark:bg-gray-700/30 border-t border-gray-200 dark:border-gray-700 flex items-center justify-center gap-2">
                  <button
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                    className="px-4 py-2 text-sm rounded-lg bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    « 上一页
                  </button>

                  <span className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">
                    第 <strong>{currentPage}</strong> / {totalPages} 页
                  </span>

                  <button
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                    className="px-4 py-2 text-sm rounded-lg bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    下一页 »
                  </button>
                </div>
              )}
            </>
          )}
        </div>

        {/* 失败详情弹窗 */}
        {selectedFailedReport && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white dark:bg-gray-800 rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto shadow-2xl">
              <div className="sticky top-0 bg-white dark:bg-gray-800 px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  ❌ 解析失败详情
                </h3>
                <button
                  onClick={() => setSelectedFailedReport(null)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  ✕
                </button>
              </div>

              <div className="p-6 space-y-4">
                {/* 可能的失败原因 */}
                <div className="bg-red-50 dark:bg-red-900/10 rounded-lg p-4 border border-red-200 dark:border-red-800">
                  <h4 className="font-semibold text-red-700 dark:text-red-400 mb-2 flex items-center gap-2">
                    🔍 可能的失败原因
                  </h4>
                  <ul className="space-y-2 text-sm text-red-600 dark:text-red-300">
                    <li className="flex items-start gap-2">
                      <span>●</span>
                      <span><strong>PDF格式问题</strong>: 文件可能是扫描件（图片格式），系统无法提取文本内容</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>●</span>
                      <span><strong>文件加密</strong>: PDF设置了密码保护或权限限制</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>●</span>
                      <span><strong>文件损坏</strong>: 上传过程中文件可能已损坏或不完整</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>●</span>
                      <span><strong>网络超时</strong>: Render免费版响应时间较长，请求可能超时</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>●</span>
                      <span><strong>服务器错误</strong>: 后端服务暂时不可用或正在维护</span>
                    </li>
                  </ul>
                </div>

                {/* 解决方案 */}
                <div className="bg-green-50 dark:bg-green-900/10 rounded-lg p-4 border border-green-200 dark:border-green-800">
                  <h4 className="font-semibold text-green-700 dark:text-green-400 mb-2 flex items-center gap-2">
                    💡 推荐解决方案
                  </h4>
                  <ul className="space-y-2 text-sm text-green-600 dark:text-green-300">
                    <li className="flex items-start gap-2">
                      <span>✓</span>
                      <span>使用<strong>文字版PDF</strong>（非扫描件或图片格式）</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>✓</span>
                      <span>确认PDF文件<strong>未设置密码保护</strong></span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>✓</span>
                      <span>压缩文件大小至 <strong>50MB以下</strong></span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>✓</span>
                      <span>检查<strong>网络连接稳定性</strong>，避免高峰时段上传</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>✓</span>
                      <span>如多次失败，可尝试使用<strong>"查看示例分析"</strong>功能体验完整流程</span>
                    </li>
                  </ul>
                </div>

                {/* 报告信息 */}
                <div className="bg-gray-50 dark:bg-gray-700/30 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2">报告信息</h4>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">公司名称:</span>
                      <span className="ml-2 text-gray-900 dark:text-white">{selectedFailedReport.company_name || '--'}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">股票代码:</span>
                      <span className="ml-2 text-gray-900 dark:text-white">{selectedFailedReport.stock_code || '--'}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">报告期间:</span>
                      <span className="ml-2 text-gray-900 dark:text-white">{selectedFailedReport.report_period || '--'}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">上传时间:</span>
                      <span className="ml-2 text-gray-900 dark:text-white">
                        {selectedFailedReport.upload_time ? new Date(selectedFailedReport.upload_time).toLocaleString('zh-CN') : '未知'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="sticky bottom-0 bg-gray-50 dark:bg-gray-700/30 px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
                <button
                  onClick={() => setSelectedFailedReport(null)}
                  className="px-6 py-2 bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors"
                >
                  关闭
                </button>
                <button
                  onClick={() => {
                    setSelectedFailedReport(null);
                    document.getElementById('file-upload')?.click();
                  }}
                  className="px-6 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors"
                >
                  重新上传
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
