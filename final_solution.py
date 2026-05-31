#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终方案 - 智能检测并修复所有乱码和JSX结构错误
"""

import re

file_path = 'frontend/src/pages/reports.tsx'

print('🔧 最终修复方案\n')

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print(f'📄 文件大小: {len(content)} 字符')

# 步骤1: 使用正则表达式找到所有未终止的字符串字面量
# 匹配模式: '...缺少结束引号
pattern_1 = r"'([^']*[\u4e00-\u9fff][^']*)\);"
matches_1 = list(re.finditer(pattern_1, content))
print(f'\n🔍 发现 {len(matches_1)} 处可能的未终止字符串')

# 步骤2: 修复这些字符串 - 在 ); 前添加 '
for match in reversed(matches_1):  # 反向遍历避免位置偏移
    old_str = match.group(0)
    new_str = old_str.replace("');", "');")  # 确保有结束引号
    if old_str != new_str:
        content = content[:match.start()] + new_str + content[match.end():]
        print(f'✅ 修复: {old_str[:50]}...')

# 步骤3: 修复常见的乱码模式（基于之前发现的）
garbled_patterns = [
    (r"setError\('([^']*)'\)", lambda m: f"setError('{m.group(1).replace('涓婁紶澶辫触锛岃妫€鏌ユ枃浠舵牸寮忓拰缃戠粶鍚庨噸璇?', '上传失败，请检查文件格式和网络后重试')}')"),
]

for pattern, replacement in garbled_patterns:
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
        print(f'✅ 修复乱码模式')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('\n✅ 完成！')
