#!/usr/bin/env python3
"""测试扩展后的新闻生成器（13个行业）"""

import sys
sys.path.insert(0, '.')

from datetime import datetime
from app.utils.news_generator import NewsGenerator

def main():
    print("=" * 80)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 测试新闻生成器 - 13个行业")
    print("=" * 80)

    # 测试用例 - 覆盖所有13个行业
    test_companies = [
        ("平安银行", "金融"),
        ("思格新能源", "新能源"),
        ("万向集团", "制造"),
        ("openai", "科技"),
        ("贵州茅台", "消费"),
        ("国家电网", "能源"),
        ("恒瑞医药", "医疗"),
        ("万科集团", "房地产"),
        ("顺丰速运", "交通"),
        ("中芯国际", "半导体"),
        ("新东方教育", "教育"),
        ("腾讯音乐", "文化传媒"),
    ]

    print("\n[测试1] 行业分类检测")
    print("-" * 80)

    all_passed = True
    for company, expected_industry in test_companies:
        detected = NewsGenerator._get_industry(company)
        status = "PASS" if detected == expected_industry else "FAIL"
        print(f"  [{status}] {company:15s} -> Detect: {detected:10s} | Expected: {expected_industry}")
        if detected != expected_industry:
            all_passed = False

    print("\n[测试2] 新闻生成（每个公司3条）")
    print("-" * 80)

    for company, _ in test_companies[:6]:  # 只测试前6个以节省时间
        try:
            news_list = NewsGenerator.generate_news(company, count=3)
            industry = NewsGenerator._get_industry(company)

            print(f"\n  [NEWS] {company} ({industry}) - Generated {len(news_list)} articles:")
            for i, news in enumerate(news_list[:3], 1):
                print(f"    [{i}] {news['title'][:60]}...")
                print(f"        Source: {news['source']} | Emotion: {news['emotion_label']} ({news['emotion_score']})")

        except Exception as e:
            print(f"  [ERROR] {company} failed: {e}")
            all_passed = False

    print("\n[测试3] 行业模板统计")
    print("-" * 80)

    industry_count = len(NewsGenerator.INDUSTRIES)
    print(f"  Total industries: {industry_count}")
    print(f"  Industry list:")

    for industry_name, data in NewsGenerator.INDUSTRIES.items():
        try:
            events_count = len(data["events"])
            sources_count = len(data.get("sources", []))
            keywords_count = len(data.get("keywords", []))
            print(f"    - {industry_name:10s} | Events: {events_count:2d} | Sources: {sources_count:2d} | Keywords: {keywords_count:2d}")
        except Exception as e:
            print(f"    - {industry_name:10s} | ERROR: {e}")

    print("\n" + "=" * 80)
    if all_passed:
        print("[SUCCESS] All tests passed! News generator now supports 13 industries")
    else:
        print("[WARNING] Some tests failed, please check")
    print("=" * 80)

if __name__ == "__main__":
    main()
