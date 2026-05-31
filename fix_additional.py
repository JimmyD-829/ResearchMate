#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充修复 - 处理剩余的乱码
"""

file_path = 'frontend/src/pages/reports.tsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 补充的乱码映射
additional_fixes = {
    '点击浜嗙ず示例分析按钮閽?': '点击了示例分析按钮',
    '涓婁紶澶辫触锛岃妫€鏌ユ枃浠舵牸寮忓拰缃戠粶鍚庨噸璇?': '上传失败，请检查文件格式和网络后重试',
    '涓婁紶澶辫触:': '上传失败:',
}

count = 0
for garbled, correct in additional_fixes.items():
    if garbled in content:
        content = content.replace(garbled, correct)
        count += 1
        print(f'✅ 修复: {garbled[:40]}... → {correct}')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\n✅ 补充修复 {count} 处')
