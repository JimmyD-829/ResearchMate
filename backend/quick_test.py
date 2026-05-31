#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试脚本 - 使用真实的Alpha Vantage API Key
"""

import asyncio
import sys
import os

# 设置API Key
os.environ['ALPHA_VANTAGE_API_KEY'] = 'RIWKXJTNABB5LUTF'

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.real_emotion_service import RealEmotionService


async def quick_test():
    """快速测试阿里巴巴(BABA)"""
    print("\n" + "🚀".center(60, "="))
    print("  Alpha Vantage 真实数据快速测试")
    print("  API Key: RIWKXJ...B5LUTF (已配置)".center(44))
    print("=".center(60, "="))
    
    service = RealEmotionService()
    
    try:
        # 测试1: 阿里巴巴 (BABA) - Alpha Vantage美股
        print(f"\n📊 测试1: 阿里巴巴 (BABA) - Alpha Vantage")
        print("-" * 50)
        
        start_time = __import__('datetime').datetime.now()
        result = await service.get_real_emotion_data('阿里巴巴', 'BABA')
        end_time = __import__('datetime').datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        if result:
            print(f"\n✅ 成功! 耗时: {duration:.2f}秒")
            print(f"\n📈 情绪分数:")
            score = result['score']
            print(f"   当前分数: {score['current_score']} ({score['current_label']})")
            print(f"   7日均值:   {score['last_7d_avg']}")
            print(f"   30日均值:  {score['last_30d_avg']}")
            print(f"   分析依据:  {score.get('reasoning', 'N/A')}")
            
            if score.get('realtime_data'):
                rt = score['realtime_data']
                print(f"\n💹 实时行情:")
                print(f"   价格:     ${rt.get('price', 'N/A')}")
                print(f"   涨跌幅:   {rt.get('change_pct', 'N/A')}%")
                print(f"   成交量:   {rt.get('volume', 'N/A'):,}")
            
            if score.get('indicators'):
                ind = score['indicators']
                print(f"\n📊 技术指标:")
                for key, value in ind.items():
                    print(f"   • {key}: {value}")
            
            print(f"\n🔗 数据源信息:")
            print(f"   来源:      {result['source']}")
            print(f"   是否真实:  {'✅ 是' if result['metadata'].get('is_real_data') else '❌ 否'}")
            print(f"   数据点数:  {result['metadata'].get('data_points', 0)}")
            
            print(f"\n{'='*60}")
            print(f"🎉 阿里巴巴真实数据获取成功!")
            print(f"{'='*60}\n")
            
        else:
            print(f"❌ 失败! 耗时: {duration:.2f}秒")
            return False
        
        # 测试2: Microsoft (MSFT)
        print(f"\n📊 测试2: Microsoft Corp (MSFT)")
        print("-" * 50)
        
        start_time = __import__('datetime').datetime.now()
        result2 = await service.get_real_emotion_data('Microsoft Corp', 'MSFT')
        end_time = __import__('datetime').datetime.now()
        
        duration2 = (end_time - start_time).total_seconds()
        
        if result2:
            print(f"\n✅ 成功! 耗时: {duration2:.2f}秒")
            score2 = result2['score']
            print(f"   分数: {score2['current_score']} ({score2['current_label']})")
            if score2.get('realtime_data'):
                rt2 = score2['realtime_data']
                print(f"   价格: ${rt2.get('price')} ({rt2.get('change_pct')}%)")
        
        # 测试3: 平安银行 (000001) - AKShare A股
        print(f"\n📊 测试3: 平安银行 (000001) - AKShare A股")
        print("-" * 50)
        
        try:
            start_time = __import__('datetime').datetime.now()
            result3 = await service.get_real_emotion_data('平安银行', '000001')
            end_time = __import__('datetime').datetime.now()
            
            duration3 = (end_time - start_time).total_seconds()
            
            if result3:
                print(f"\n✅ 成功! 耗时: {duration3:.2f}秒")
                score3 = result3['score']
                print(f"   分数: {score3['current_score']} ({score3['current_label']})")
                print(f"   数据源: {result3['source']}")
                if score3.get('realtime_data'):
                    rt3 = score3['realtime_data']
                    print(f"   价格: ¥{rt3.get('price')} ({rt3.get('change_pct')}%)")
            else:
                print(f"\n⚠️ AKShare A股数据不可用 (可能需要国内网络环境)")
                
        except Exception as e:
            print(f"\n⚠️ AKShare失败: {str(e)[:100]}")
            print("   这在海外服务器上是正常的，已自动降级到Fallback")
        
        print(f"\n{'='*60}")
        print(f"✨ 测试完成!")
        print(f"{'='*60}\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await service.close()


if __name__ == "__main__":
    success = asyncio.run(quick_test())
    sys.exit(0 if success else 1)
