#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终极修复 - 完全重写reports.tsx
使用正确的UTF-8编码重写整个文件
"""

import re

file_path = 'frontend/src/pages/reports.tsx'

print('🔧 终极修复开始...\n')

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f'📄 读取了 {len(lines)} 行')

# 创建新内容列表
new_lines = []
fix_count = 0

# 定义所有需要修复的行（基于错误日志）
line_fixes = {
    # 第108行: console.log缺少引号
    107: "  const loadSampleReport = async () => {\n",
    108: "    console.log('🎉 点击了示例分析按钮');\n",

    # 第181行: console.log缺少引号
    180: "      console.log('✅ 示例分析完成');\n",

    # 第217行: setError字符串
    216: "      setError('上传失败，请检查文件格式和网络后重试');\n",

    # 第242行: 另一个setError
    241: "        setError('上传失败');\n",

    # 第263行: 另一个错误消息
    262: "          alert('上传失败，请检查文件格式和网络后重试');\n",
}

# 应用逐行修复
for i, line in enumerate(lines):
    line_num = i + 1

    if line_num in line_fixes:
        new_lines.append(line_fixes[line_num])
        fix_count += 1
        print(f'✅ 第{line_num}行已修复')
    else:
        new_lines.append(line)

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f'\n✅ 完成！修复了 {fix_count} 行')
