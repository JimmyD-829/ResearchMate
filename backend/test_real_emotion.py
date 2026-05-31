#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实情绪数据集成测试脚本

测试用例:
1. 阿里巴巴(BABA) - Alpha Vantage美股数据
2. 平安银行(000001) - AKShare A股数据
3. 贵州茅台(600519) - AKShare A股数据

运行方式:
  cd backend
  python test_real_emotion.py
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.real_emotion_service import RealEmotionService


async def test_company(company_name: str, stock_code: str = None):
    """测试单个公司的真实情绪数据获取"""
    print(f"\n{'='*60}")
    print(f"🧪 测试公司: {company_name} ({stock_code or '自动识别'})")
    print(f"{'='*60}")
    
    service = RealEmotionService()
    
    try:
        # 测试1: 股票代码映射
        if not stock_code:
            symbol = service.get_stock_symbol(company_name)
        else:
            symbol = stock_code
        
        print(f"\n✅ 股票代码识别: {symbol}")
        
        if not symbol:
            print("❌ 无法识别股票代码，跳过测试")
            return None
        
        # 测试2: 获取完整情绪数据
        print(f"\n⏳ 正在获取{company_name}的真实金融数据...")
        start_time = datetime.now()
        
        result = await service.get_real_emotion_data(company_name, symbol)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        if not result:
            print(f"❌ 获取失败 (耗时: {duration:.2f}秒)")
            return None
        
        # 打印结果摘要
        print(f"\n✅ 获取成功! (耗时: {duration:.2f}秒)")
        print(f"\n📊 情绪分数:")
        score = result['score']
        print(f"   • 当前分数: {score['current_score']} ({score['current_label']})")
        print(f"   • 7日均值:   {score['last_7d_avg']}")
        print(f"   • 30日均值:  {score['last_30d_avg']}")
        print(f"   • 分析依据:  {score.get('reasoning', 'N/A')}")
        
        if score.get('realtime_data'):
            rt = score['realtime_data']
            print(f"\n💹 实时行情:")
            print(f"   • 价格:     ¥{rt.get('price', 'N/A')}")
            print(f"   • 涨跌幅:   {rt.get('change_pct', 'N/A')}%")
            print(f"   • 成交量:   {rt.get('volume', 'N/A')}")
        
        if score.get('indicators'):
            ind = score['indicators']
            print(f"\n📈 技术指标:")
            for key, value in ind.items():
                print(f"   • {key}: {value}")
        
        print(f"\n📚 数据源信息:")
        print(f"   • 来源:      {result['source']}")
        print(f"   • 是否真实:  {'是 ✓' if result['metadata'].get('is_real_data') else '否 ✗'}")
        print(f"   • 数据点数:  {result['metadata'].get('data_points', 0)}")
        print(f"   • 计算方法:  {result['metadata'].get('method', 'N/A')}")
        
        if result.get('trend') and result['trend'].get('trend'):
            trend_len = len(result['trend']['trend'])
            print(f"   • 趋势点数:  {trend_len}")
            
            if trend_len > 0:
                latest = result['trend']['trend'][-1]
                print(f"   • 最新日期: {latest['date']}")
                print(f"   • 最新分数: {latest['daily_score']}")
        
        print(f"\n{'='*60}")
        print(f"✅ {company_name}: 测试通过!")
        print(f"{'='*60}\n")
        
        return result
        
    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        await service.close()


async def main():
    """主测试函数"""
    print("\n" + "🚀".center(60, "="))
    print("  ResearchMate 真实情绪数据集成测试")
    print("  V2.0 - AKShare/Alpha Vantage".center(46))
    print("=".center(60, "="))
    
    test_cases = [
        ("阿里巴巴", "BABA"),           # 美股 - Alpha Vantage
        ("平安银行", "000001"),         # A股 - AKShare
        ("贵州茅台", "600519"),         # A股 - AKShare (热门)
        ("比亚迪", "002594"),           # A股 - AKShare
        ("Microsoft Corp", "MSFT"),     # 美股 - Alpha Vantage
    ]
    
    results = []
    
    for company_name, stock_code in test_cases:
        result = await test_company(company_name, stock_code)
        results.append({
            'company': company_name,
            'stock_code': stock_code,
            'success': result is not None,
            'is_real_data': result.get('metadata', {}).get('is_real_data', False) if result else False,
            'score': result['score']['current_score'] if result else None,
            'source': result.get('source', 'error') if result else 'error'
        })
    
    # 输出汇总报告
    print("\n\n" + "📋".center(60, "="))
    print("  测试结果汇总报告")
    print("=".center(60, "="))
    
    success_count = sum(1 for r in results if r['success'])
    real_data_count = sum(1 for r in results if r.get('is_real_data'))
    
    print(f"\n总测试数: {len(results)}")
    print(f"成功数:   {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
    print(f"真实数据: {real_data_count}/{len(results)} ({real_data_count/len(results)*100:.1f}%)")
    
    print(f"\n详细结果:")
    print(f"{'公司名':<15} {'股票代码':<10} {'状态':<8} {'真实数据':<8} {'分数':<8} {'数据源'}")
    print("-" * 70)
    
    for r in results:
        status_icon = "✅" if r['success'] else "❌"
        real_icon = "✓" if r.get('is_real_data') else "✗"
        score_str = f"{r['score']:.1f}" if r['score'] is not None else "N/A"
        
        print(f"{r['company']:<15} {r['stock_code']:<10} {status_icon:<8} {real_icon:<8} {score_str:<8} {r['source']}")
    
    print("-" * 70)
    
    if real_data_count == len(results):
        print("\n🎉 所有测试用例均成功获取真实金融数据！")
        print("✨ AKShare/Alpha Vantage集成完全正常！")
    elif real_data_count > 0:
        print(f"\n✅ {real_data_count}/{len(results)} 个用例成功获取真实数据")
        print("💡 部分数据源可能不可用或需要配置API Key")
    else:
        print("\n⚠️ 所有测试用例都使用了Fallback模拟数据")
        print("🔍 请检查:")
        print("   1. Alpha Vantage API Key是否已配置 (环境变量: ALPHA_VANTAGE_API_KEY)")
        print("   2. AKShare库是否已安装 (pip install akshare)")
        print("   3. 网络连接是否正常")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ 测试被用户中断")
        sys.exit(1)
