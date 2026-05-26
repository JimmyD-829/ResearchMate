"""
情绪数据初始化脚本 - 为所有公司计算并填充每日情绪趋势
"""
import requests
import json

API_BASE = "https://researchmate-aznu.onrender.com"

def init_emotion_data():
    print("=" * 60)
    print("📊 初始化情绪分析数据")
    print("=" * 60)

    # 获取所有新闻
    print("\n📰 获取所有新闻数据...")
    try:
        response = requests.get(f"{API_BASE}/api/news?limit=500", timeout=30)
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])
            print(f"   ✅ 获取到 {len(items)} 篇新闻")

            # 统计各公司
            companies = set(item["company_name"] for item in items)
            print(f"   📊 涉及 {len(companies)} 家公司: {', '.join(companies)}")

            # 为每家公司更新情绪数据
            for company in companies:
                print(f"\n🔄 更新 {company} 的情绪数据...")
                try:
                    update_response = requests.post(
                        f"{API_BASE}/api/emotion/update",
                        json={"company_name": company},
                        timeout=30
                    )
                    if update_response.status_code == 200:
                        print(f"   ✅ {company} 情绪数据已更新")
                    else:
                        print(f"   ⚠️ {company}: HTTP {update_response.status_code}")
                except Exception as e:
                    print(f"   ❌ {company}: {e}")

            print("\n✨ 情绪数据初始化完成！")

        else:
            print(f"❌ 获取新闻失败: HTTP {response.status_code}")

    except Exception as e:
        print(f"❌ 异常: {e}")

if __name__ == "__main__":
    init_emotion_data()
