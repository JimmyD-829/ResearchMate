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
      setError('鑾峰彇璐㈡姤鍒楄〃澶辫触');
    } finally {
      setLoading(false);
    }
  };

  // 鍒嗛〉璁＄畻
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
      setError('璇烽€夋嫨鏂囦欢');
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
      setError('浠呮敮鎸?PDF銆丒xcel (xlsx/xls)銆丆SV 鏍煎紡鏂囦欢');
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
    console.log('馃殌 鐐瑰嚮浜嗙ず渚嬪垎鏋愭寜閽?);
    setUploading(true);
    setError('');
    setUploadStep('uploading');
    setUploadProgress(0);
    
    try {
      console.log('寮€濮嬫ā鎷熻繘搴?..');
      await simulateProgress(0, 30, 800, 'uploading');
      console.log('涓婁紶瀹屾垚锛屽紑濮嬭В鏋?..');
      await simulateProgress(30, 60, 1200, 'parsing');
      console.log('瑙ｆ瀽瀹屾垚锛屽紑濮嬪垎鏋?..');
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
        ai_summary: `## 璐靛窞鑼呭彴 (600519) 2025骞村害璐㈠姟鍒嗘瀽鎶ュ憡

### 馃搳 鏍稿績璐㈠姟鎸囨爣

**钀ヤ笟鏀跺叆**: 1,476.99浜垮厓 (+15.2% YoY)
**鍑€鍒╂鼎**: 748.00浜垮厓 (+16.8% YoY)
**缁忚惀鐜伴噾娴?*: 825.00浜垮厓 (+12.3% YoY)
**璧勪骇璐熷€虹巼**: 18.5% (-1.2pp)
**姣涘埄鐜?*: 91.5% (+0.3pp)

### 馃幆 鍏抽敭鍙戠幇

#### 鉁?**浼樺娍浜偣**
1. **鐩堝埄鑳藉姏鍗撹秺**: 姣涘埄鐜囬珮杈?1.5%锛屼綅灞匒鑲℃棣?2. **鐜伴噾娴佸厖娌?*: 缁忚惀鎬х幇閲戞祦/鍑€鍒╂鼎姣旂巼杈?10%锛岀幇閲戝垱閫犺兘鍔涘己
3. **鍝佺墝鎶ゅ煄娌虫繁**: 鑼呭彴鍝佺墝浠峰€兼寔缁彁鍗囷紝瀹氫环鏉冪ǔ鍥?4. **璐㈠姟缁撴瀯鍋ュ悍**: 璧勪骇璐熷€虹巼浠?8.5%锛屽嚑涔庢棤鏈夋伅璐熷€?5. **鍒嗙孩鎱锋叏**: 棰勮2025骞村垎绾㈢巼瓒?2%锛岃偂鎭巼绾?.5%

#### 鈿狅笍 **椋庨櫓鎻愮ず**
1. **浼板€煎亸楂?*: 褰撳墠PE(TTM)绾?5鍊嶏紝楂樹簬鍘嗗彶鍧囧€?2. **澧為€熸斁缂?*: 钀ユ敹澧為€熶粠20%+闄嶈嚦15%锛岄珮鍩烘暟鏁堝簲鏄剧幇
3. **鏀跨瓥椋庨櫓**: 鐧介厭娑堣垂绋庢敼闈╁彲鑳藉奖鍝嶅埄娑︾巼
4. **绔炰簤鍔犲墽**: 楂樼鐧介厭甯傚満绔炰簤鐧界儹鍖栵紝浜旂伯娑层€佸浗绐?573杩借刀
5. **搴撳瓨鍘嬪姏**: 缁忛攢鍟嗗簱瀛樺懆鏈熷欢闀胯嚦45澶╋紙vs 鍘嗗彶骞冲潎30澶╋級

### 馃挕 鎶曡祫寤鸿

**璇勭骇**: 猸愨瓙猸愨瓙 (鎺ㄨ崘鎸佹湁)

**鐩爣浠?*: 1,950-2,050鍏?(鍩轰簬2026骞?2x PE)

**鏍稿績閫昏緫**:
- 鐭湡锛氭槬鑺傛椇瀛?鎻愪环棰勬湡鍌寲鑲′环
- 涓湡锛氱洿閿€娓犻亾鍗犳瘮鎻愬崌鑷?0%+锛屽鍘氬埄娑?- 闀挎湡锛氬浗闄呭寲甯冨眬+i鑼呭彴鏁板瓧鍖栬祴鑳?
**椋庨櫓鏀剁泭姣?*: 鍦ㄥ綋鍓嶄环浣嶅叿澶囬槻寰″睘鎬э紝閫傚悎闀挎湡閰嶇疆`
      };

      console.log('绀轰緥鏁版嵁鐢熸垚瀹屾垚锛屾洿鏂扮姸鎬?..');
      await simulateProgress(90, 100, 300, 'success');
      setReports(prev => [sampleData, ...prev]);
      setUploadStep('success');
      setSelectedFile(null);
      
      setTimeout(() => {
        setUploadStep('idle');
        setUploadProgress(0);
      }, 2000);
      
      console.log('鉁?绀轰緥鍒嗘瀽瀹屾垚锛?);
    } catch (err) {
      console.error('鉂?鍔犺浇绀轰緥鏁版嵁澶辫触:', err);
      setError('鍔犺浇绀轰緥鏁版嵁澶辫触: ' + (err as Error).message);
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
      console.error('涓婁紶閿欒璇︽儏:', err);

      if (err.code === 'ECONNABORTED') {
        setError('璇锋眰瓒呮椂锛屾湇鍔″櫒鍝嶅簲鏃堕棿杩囬暱銆傝绋嶅悗閲嶈瘯鎴栨鏌ョ綉缁滆繛鎺ャ€?);
      } else if (err.response) {
        const status = err.response.status;
        const detail = err.response.data?.detail || err.response.data?.message;

        if (status === 400 && detail) {
          setError(detail);
        } else if (status === 401) {
          setError('鐧诲綍宸茶繃鏈燂紝璇烽噸鏂扮櫥褰曞悗閲嶈瘯');
        } else if (status === 413) {
          setError('鏂囦欢杩囧ぇ锛堟渶澶ф敮鎸?0MB锛夛紝璇峰帇缂╁悗閲嶆柊涓婁紶');
        } else if (status >= 500) {
          setError(`鏈嶅姟鍣ㄥ唴閮ㄩ敊璇?(${status})锛岃绋嶅悗閲嶈瘯`);
        } else {
          setError(`涓婁紶澶辫触: ${detail || `HTTP ${status}`}`);
        }
      } else if (err.message) {
        if (err.message.includes('Network Error')) {
          setError('缃戠粶杩炴帴澶辫触锛岃妫€鏌ョ綉缁滃悗閲嶈瘯');
        } else if (err.message.includes('timeout')) {
          setError('璇锋眰瓒呮椂锛岃绋嶅悗閲嶈瘯');
        } else {
          setError(`涓婁紶澶辫触: ${err.message}`);
        }
      } else {
        setError('涓婁紶澶辫触锛岃妫€鏌ユ枃浠舵牸寮忓拰缃戠粶鍚庨噸璇?);
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
      case 'uploading': return '姝ｅ湪涓婁紶...';
      case 'parsing': return '姝ｅ湪瑙ｆ瀽璐㈡姤...';
      case 'analyzing': return 'AI鍒嗘瀽涓?..';
      case 'success': return '鍒嗘瀽瀹屾垚锛?;
      case 'error': return '鍒嗘瀽澶辫触';
      default: return '';
    }
  };

  if (!user) return null;

  return (
    <Layout>
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">璐㈡姤鏅鸿兘瑙ｈ</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">涓婁紶璐㈡姤PDF锛岃嚜鍔ㄨВ鏋愬叧閿储鍔℃寚鏍?/p>
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
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">涓婁紶璐㈡姤</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">鏀寔 PDF銆丒xcel銆丆SV 鏍煎紡鏂囦欢</p>
            </div>
          </div>
          
          {error && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-red-600 dark:text-red-400 text-sm font-medium">{error}</p>
                  <div className="mt-3 text-xs text-red-500 dark:text-red-400 space-y-1.5">
                    <p>馃攳 **甯歌鍘熷洜鍙婅В鍐虫柟妗?*:</p>
                    <p>鈥?鈴?**鏈嶅姟鍣ㄨ秴鏃?*: Render鍏嶈垂鐗堥娆¤姹傞渶50绉?锛岃鑰愬績绛夊緟鎴栦娇鐢ㄧず渚嬫暟鎹?/p>
                    <p>鈥?馃搫 **PDF鏍煎紡闂**: 鎵弿浠?鍔犲瘑PDF鏃犳硶瑙ｆ瀽锛岃浣跨敤鏂囧瓧鐗圥DF</p>
                    <p>鈥?馃寪 **缃戠粶杩炴帴**: 妫€鏌ョ綉缁滐紝鎴栧皾璇曞埛鏂伴〉闈㈠悗閲嶈瘯</p>
                    <p>鈥?馃摝 **鏂囦欢澶у皬**: 璇风‘淇濇枃浠跺皬浜?0MB</p>
                    <div className="mt-2 pt-2 border-t border-red-200 dark:border-red-700">
                      <p className="font-medium text-red-600 dark:text-red-400">馃挕 鎺ㄨ崘鏂规: 鐐瑰嚮涓嬫柟"鉁?鏌ョ湅绀轰緥鍒嗘瀽"鎸夐挳锛岀珛鍗充綋楠屽畬鏁村姛鑳斤紒</p>
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
                  閲嶈瘯涓婁紶
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
            <p className="text-gray-600 dark:text-gray-400 mb-4">鐐瑰嚮鎴栨嫋鎷戒笂浼犺储鎶DF鏂囦欢</p>
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
                鉁?鏌ョ湅绀轰緥鍒嗘瀽锛堟棤闇€涓婁紶锛?              </button>
            </div>
            <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">浣撻獙瀹屾暣鍒嗘瀽鍔熻兘锛屼簡瑙ｆ姤鍛婃牱寮?/p>
          </div>
          
          {selectedFile && uploadStep === 'idle' && (
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="mt-6 w-full py-3.5 bg-gradient-to-r from-primary-600 to-blue-600 hover:from-primary-500 hover:to-blue-500 disabled:from-gray-400 disabled:to-gray-400 text-white font-semibold rounded-xl transition-all"
            >
              {uploading ? '澶勭悊涓?..' : '寮€濮嬭В鏋愯储鎶?}
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
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">瑙ｆ瀽鍘嗗彶</h2>
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
              <p className="text-gray-600 dark:text-gray-400">鏆傛棤璐㈡姤瑙ｆ瀽璁板綍</p>
              <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">涓婁紶璐㈡姤鎴栫偣鍑?鏌ョ湅绀轰緥鍒嗘瀽"寮€濮嬩綋楠?/p>
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
                        <h3 className="text-base font-semibold text-gray-900 dark:text-white">{report.company_name || report.id?.includes('sample') ? '绀轰緥鍒嗘瀽' : '鏈煡'}</h3>
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
                          title={report.status !== 'success' ? '鐐瑰嚮鏌ョ湅澶辫触鍘熷洜' : ''}
                        >
                          {report.status === 'success' ? '鉁?鎴愬姛' :
                           report.status === 'processing' ? '鈴?澶勭悊涓? : '鉂?澶辫触'}
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
                          鐐瑰嚮灞曞紑瀹屾暣鎶ュ憡 鈫?                        </p>
                      </div>
                    )}

                    {report.status !== 'success' && !report.ai_summary && (
                      <div className="mt-2 p-2 bg-yellow-50 dark:bg-yellow-900/10 rounded text-xs text-yellow-700 dark:text-yellow-400">
                        馃挕 鐐瑰嚮涓婃柟"澶辫触"鏍囩鏌ョ湅璇︾粏鍘熷洜鍜岃В鍐虫柟妗?                      </div>
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

        {/* 澶辫触璇︽儏寮圭獥 */}
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
                    鉂?瑙ｆ瀽澶辫触璇︽儏
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
                  鏂囦欢: {selectedFailedReport.id?.includes('sample') ? '绀轰緥鍒嗘瀽' : (selectedFailedReport.company_name || '鏈煡鏂囦欢')}
                  {selectedFailedReport.upload_time && ` 路 ${formatDate(selectedFailedReport.upload_time)}`}
                </p>
              </div>

              {/* 寮圭獥鍐呭 */}
              <div className="p-6 space-y-4">
                {/* 鍙兘鐨勫師鍥?*/}
                <div className="bg-red-50 dark:bg-red-900/10 rounded-lg p-4 border border-red-200 dark:border-red-800">
                  <h4 className="font-semibold text-red-700 dark:text-red-400 mb-2 flex items-center gap-2">
                    馃攳 鍙兘鐨勫け璐ュ師鍥?                  </h4>
                  <ul className="space-y-2 text-sm text-red-600 dark:text-red-300">
                    <li className="flex items-start gap-2">
                      <span>鈥?/span>
                      <span><strong>PDF鏍煎紡闂</strong>: 鏂囦欢鍙兘鏄壂鎻忎欢锛堝浘鐗囨牸寮忥級锛岀郴缁熸棤娉曟彁鍙栨枃瀛楀唴瀹?/span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>鈥?/span>
                      <span><strong>鏂囦欢鍔犲瘑</strong>: PDF璁剧疆浜嗗瘑鐮佷繚鎶ゆ垨鏉冮檺闄愬埗</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>鈥?/span>
                      <span><strong>鏂囦欢鎹熷潖</strong>: 涓婁紶杩囩▼涓枃浠跺彲鑳藉凡鎹熷潖鎴栦笉瀹屾暣</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>鈥?/span>
                      <span><strong>缃戠粶瓒呮椂</strong>: Render鍏嶈垂鐗堝搷搴旀椂闂磋緝闀匡紝璇锋眰鍙兘瓒呮椂</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>鈥?/span>
                      <span><strong>鏈嶅姟鍣ㄩ敊璇?/strong>: 鍚庣鏈嶅姟鏆傛椂涓嶅彲鐢ㄦ垨姝ｅ湪缁存姢</span>
                    </li>
                  </ul>
                </div>

                {/* 瑙ｅ喅鏂规 */}
                <div className="bg-blue-50 dark:bg-blue-900/10 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                  <h4 className="font-semibold text-blue-700 dark:text-blue-400 mb-2 flex items-center gap-2">
                    馃挕 鎺ㄨ崘瑙ｅ喅鏂规
                  </h4>
                  <ul className="space-y-2 text-sm text-blue-600 dark:text-blue-300">
                    <li className="flex items-start gap-2">
                      <span>鉁?/span>
                      <span><strong>浣跨敤鏂囧瓧鐗圥DF</strong>: 纭繚PDF鍖呭惈鍙€夋嫨鐨勬枃鏈紝鑰岄潪鎵弿鍥剧墖</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>鉁?/span>
                      <span><strong>灏濊瘯Excel鏍煎紡</strong>: 濡傛灉鏈塃xcel鐗堟湰鐨勮储鎶ワ紝瑙ｆ瀽鎴愬姛鐜囨洿楂?/span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>鉁?/span>
                      <span><strong>鍘嬬缉鏂囦欢澶у皬</strong>: 纭繚鏂囦欢灏忎簬50MB锛屽繀瑕佹椂鍘嬬缉鍥剧墖</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>鉁?/span>
                      <span><strong>妫€鏌ョ綉缁滆繛鎺?/strong>: 纭缃戠粶绋冲畾锛屾垨绋嶅悗閲嶈瘯</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span>鉁?/span>
                      <span><strong>浣跨敤绀轰緥鍔熻兘</strong>: 鐐瑰嚮"鉁?鏌ョ湅绀轰緥鍒嗘瀽"浣撻獙瀹屾暣鍔熻兘</span>
                    </li>
                  </ul>
                </div>

                {/* 鎶€鏈粏鑺?*/}
                <div className="bg-gray-50 dark:bg-gray-700/30 rounded-lg p-4">
                  <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                    馃搵 鎶€鏈俊鎭?                  </h4>
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
                      <span className="font-medium">涓婁紶鏃堕棿:</span>
                      <span className="ml-1">{selectedFailedReport.upload_time ? new Date(selectedFailedReport.upload_time).toLocaleString('zh-CN') : '鏈煡'}</span>
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






