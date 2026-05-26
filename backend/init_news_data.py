"""
新闻数据初始化脚本 - 为所有关注的公司抓取新闻数据
使用方法: python init_news_data.py
"""
import requests
import time

API_BASE = "https://researchmate-aznu.onrender.com"

# 需要抓取新闻的公司列表
COMPANIES = [
    "Microsoft",
    "Apple", 
    "Tesla",
    "贵州茅台",
    "比亚迪",
    "字节跳动",
    "腾讯",
]

def fetch_news_for_all_companies():
    print("=" * 60)
    print("📰 ResearchMate 新闻数据初始化")
    print("=" * 60)
    
    total_fetched = 0
    
    for company in COMPANIES:
        print(f"\n📡 正在抓取 {company} 的新闻...")
        
        try:
            response = requests.post(
                f"{API_BASE}/api/news/fetch",
                json={"companies": [company]},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                fetched = data.get("fetched", 0)
                total_fetched += fetched
                print(f"   ✅ 成功: 抓取了 {fetched} 篇新闻")
                
                # 显示结果详情
                for result in data.get("results", []):
                    if result.get("status") == "success":
                        print(f"      📄 {result.get('title', 'N/A')[:50]}...")
                    else:
                        print(f"      ❌ 错误: {result.get('error', 'Unknown')}")
            else:
                print(f"   ❌ 失败: HTTP {response.status_code}")
                print(f"      响应: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ 超时: 请求超时，跳过")
        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")
        
        # 避免触发API限流
        time.sleep(2)
    
    print("\n" + "=" * 60)
    print(f"✨ 初始化完成！共抓取 {total_fetched} 篇新闻")
    print("=" * 60)
    
    # 验证数据
    print("\n📊 验证新闻数据...")
    try:
        response = requests.get(f"{API_BASE}/api/news?limit=100", timeout=30)
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            
            # 统计各公司的新闻数量
            company_counts = {}
            for item in items:
                company = item.get("company_name", "Unknown")
                company_counts[company] = company_counts.get(company, 0) + 1
            
            print("\n📈 各公司新闻统计:")
            for company, count in sorted(company_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   {company}: {count} 篇")
            
            print(f"\n总计: {len(items)} 篇新闻")
        else:
            print(f"❌ 验证失败: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ 验证异常: {e}")

if __name__ == "__main__":
    fetch_news_for_all_companies()
