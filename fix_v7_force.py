#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第7次修复 - 强制按行号修复所有问题
"""

file_path = 'frontend/src/pages/reports.tsx'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 强制修复（不检查条件）
fixes = {
    508: '                        <p className="text-[10px] text-gray-500 dark:text-gray-400">毛利率</p>\n',
    529: '                          点击展开完整报告 →</p>\n',
    536: '                        💡 点击上方"失败"标签查看详细原因和解决方案\n                      </div>\n',
    542: '              {/* 底部分页控件 */}\n',
    590: '                {/* 可能的失败原因 */}\n',
    592: '                    🔍 可能的失败原因\n                  </h4>\n',
    595: '                      <span>●</span>\n',
    598: '                      <span><strong>文件加密</strong>: PDF设置了密码保护或权限限制</span>\n',
    601: '                      <span>●</span>\n',
    613: '                {/* 解决方案 */}\n',
}

count = 0
for line_num, new_line in fixes.items():
    if line_num < len(lines):
        lines[line_num] = new_line
        count += 1
        print(f'✅ 第{line_num + 1}行')

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f'\n✅ 强制修复了{count}行')
