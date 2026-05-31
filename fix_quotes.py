#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复JSX结构错误 - 添加缺失的引号和关闭标签
"""

import re

file_path = 'frontend/src/pages/reports.tsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 修复1: 缺少结束单引号的console.log
fixes = [
    # console.log 缺少结束引号
    ("console.log('🎉 点击了示例分析按钮);", "console.log('🎉 点击了示例分析按钮');"),
    ("console.log('✅ 示例分析完成);", "console.log('✅ 示例分析完成');"),
    
    # 其他可能的缺失引号（基于错误行号）
]

count = 0
for old, new in fixes:
    if old in content:
        content = content.replace(old, new)
        count += 1
        print(f'✅ 修复引号: {old[:50]}...')

# 修复2: 使用正则表达式修复所有 console.log 中缺少的结束引号
# 匹配模式: console.log('...内容); 应该是 console.log('...');
pattern = r"console\.log\('([^']*)(?:[^'\n])\);"
def add_closing_quote(match):
    return f"console.log('{match.group(1)}');"

new_content, replacements = re.subn(pattern, add_closing_quote, content)
if replacements > 0:
    content = new_content
    count += replacements
    print(f'✅ 正则修复 {replacements} 处console.log引号')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\n✅ 总共修复 {count} 处')
