#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第7次修复 - 修复JSX结构错误和剩余乱码
"""

file_path = 'frontend/src/pages/reports.tsx'

print('🔧 第7次修复 - JSX结构和乱码\n')

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixes = {
    # 第371行: button标签缺少关闭标签
    376: "                📋 查看示例分析（无需上传）\n              </button>\n",
    
    # 第402行: 乱码
    401: '            <span className="text-sm text-gray-500 dark:text-gray-400">{reports.length} 条记录</span>\n',
    
    # 第492行: 乱码
    491: '                        <p className="text-[10px] text-gray-500 dark:text-gray-400">营收</p>\n',
    
    # 第494行: 乱码导致字符串未终止
    493: "                          {formatNumber(report.revenue)}{report.revenue ? '亿' : ''}\n",
    
    # 第499行: 乱码
    498: '                        <p className="text-[10px] text-gray-500 dark:text-gray-400">净利润</p>\n',
    
    # 第500行: 乱码导致字符串未终止  
    499: "                          {formatNumber(report.net_profit)}{report.net_profit ? '亿' : ''}\n",
}

count = 0
for line_num, new_line in fixes.items():
    if line_num < len(lines):
        old_line = lines[line_num]
        lines[line_num] = new_line
        count += 1
        print(f'✅ 第{line_num + 1}行已修复')

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f'\n✅ 完成！修复了{count}处')
