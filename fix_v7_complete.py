#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第7次修复续 - 全面修复所有JSX结构和乱码问题
"""

file_path = 'frontend/src/pages/reports.tsx'

print('🔧 全面修复所有问题\n')

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

fixes = {
    # 第509行: 乱码 + 缺少关闭标签
    508: '                        <p className="text-[10px] text-gray-500 dark:text-gray-400">毛利率</p>\n',
    
    # 第530行: p标签缺少关闭
    529: '                          点击展开完整报告 →</p>\n',
    
    # 第537行: div标签缺少关闭
    536: '                        💡 点击上方"失败"标签查看详细原因和解决方案\n                      </div>\n',
    
    # 第543行: 注释乱码
    542: '              {/* 底部分页控件 */}\n',
    
    # 第591行: 注释乱码
    590: '                {/* 可能的失败原因 */}\n',
    
    # 第593行: h4缺少关闭标签
    592: '                    🔍 可能的失败原因\n                  </h4>\n',
    
    # 第596行: span乱码
    595: '                      <span>●</span>\n',
    
    # 第599行: 乱码
    598: '                      <span><strong>文件加密</strong>: PDF设置了密码保护或权限限制</span>\n',
    
    # 第602行: span乱码
    601: '                      <span>●</span>\n',
    
    # 第614行: 注释乱码
    613: '                {/* 解决方案 */}\n',
}

count = 0
for line_num, new_line in sorted(fixes.items()):
    if line_num < len(lines):
        old_line = lines[line_num]
        # 检查是否需要修复（包含乱码或结构错误）
        if any(x in old_line for x in ['姣涘', '璐熷€虹巼', '鈥?', '鏂囦欢鍔犲瘑', '搴曢儴', '鍙兘', '瑙ｅ喅']):
            lines[line_num] = new_line
            count += 1
            print(f'✅ 第{line_num + 1}行已修复')
        elif '可能的原因' in old_line and '</h4>' not in old_line:
            lines[line_num] = new_line
            count += 1
            print(f'✅ 第{line_num + 1}行已修复 (添加关闭标签)')

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f'\n✅ 完成！修复了{count}处')
