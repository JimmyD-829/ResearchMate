export default function ComplianceNote() {
  return (
    <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4 mb-6">
      <div className="flex items-start space-x-3">
        <span className="text-xl">⚠️</span>
        <div className="text-sm">
          <p className="font-medium text-yellow-800 dark:text-yellow-300">AI生成，仅供参考</p>
          <p className="text-yellow-700 dark:text-yellow-400 mt-1">本分析不构成投资建议。请结合自身实际情况，谨慎做出投资决策。</p>
        </div>
      </div>
    </div>
  );
}
