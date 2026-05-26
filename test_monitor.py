#!/usr/bin/env python3
"""Test Data Quality Monitor API"""

import sys
sys.path.insert(0, '.')

from datetime import datetime
from app.database import SessionLocal
from app.services.data_monitor import DataQualityMonitor

def main():
    print("=" * 80)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Testing Data Quality Monitor")
    print("=" * 80)

    db = SessionLocal()

    try:
        print("\n[1] Industry Classification Accuracy")
        print("-" * 80)
        industry_result = DataQualityMonitor.check_industry_classification_accuracy()
        print(f"  Total tested: {industry_result['total_tested']}")
        print(f"  Correct: {industry_result['correct']}")
        print(f"  Accuracy: {industry_result['accuracy']}%")
        
        if industry_result['errors']:
            print(f"\n  Errors ({len(industry_result['errors'])}):")
            for err in industry_result['errors']:
                print(f"    - {err['company']}: {err['error']}")

        print("\n[2] News Data Quality")
        print("-" * 80)
        news_result = DataQualityMonitor.check_news_data_quality(db)
        print(f"  Status: {news_result.get('status', 'unknown')}")
        if news_result.get('status') != 'error':
            print(f"  Total articles: {news_result.get('total_articles', 0)}")
            print(f"  Companies with news: {news_result.get('companies_with_news', 0)}")
            print(f"  Avg per company: {news_result.get('avg_per_company', 0)}")
            print(f"  Recent 7 days: {news_result.get('recent_7_days', 0)}")

        print("\n[3] Emotion Data Coverage")
        print("-" * 80)
        emotion_result = DataQualityMonitor.check_emotion_data_coverage(db)
        print(f"  Status: {emotion_result.get('status', 'unknown')}")
        if emotion_result.get('status') != 'error':
            print(f"  Companies tested: {emotion_result.get('total_companies_tested', 0)}")
            print(f"  Companies with data: {emotion_result.get('companies_with_data', 0)}")
            print(f"  Coverage rate: {emotion_result.get('coverage_rate', 0)}%")

        print("\n[4] Financial Reports Quality")
        print("-" * 80)
        reports_result = DataQualityMonitor.check_financial_reports_quality(db)
        print(f"  Status: {reports_result.get('status', 'unknown')}")
        if reports_result.get('status') != 'error':
            print(f"  Total reports: {reports_result.get('total_reports', 0)}")
            print(f"  Success rate: {reports_result.get('success_rate', 0)}%")
            print(f"  Recent 7 days: {reports_result.get('recent_7_days', 0)}")

        print("\n[5] System Health Report")
        print("-" * 80)
        health_result = DataQualityMonitor.generate_system_health_report()
        print(f"  Overall status: {health_result.get('overall_status', 'unknown')}")
        for comp_id, comp_data in health_result.get('components', {}).items():
            status_icon = "OK" if comp_data.get('status') == 'operational' else "!!"
            print(f"  [{status_icon}] {comp_data.get('name', comp_id)}: {comp_data.get('status')}")

        print("\n[6] Comprehensive Dashboard")
        print("-" * 80)
        dashboard = DataQualityMonitor.get_comprehensive_dashboard(db)
        summary = dashboard.get('summary', {})
        print(f"  Overall health: {summary.get('overall_health', 'unknown')}")
        print(f"  Data quality score: {summary.get('data_quality_score', 0)}/100")
        print(f"  Alerts count: {summary.get('alerts_count', 0)}")
        
        if summary.get('alerts'):
            print("\n  Alerts:")
            for alert in summary['alerts'][:3]:
                print(f"    [{alert.get('type', 'INFO').upper()}] {alert.get('message', '')}")

        print("\n" + "=" * 80)
        print("[SUCCESS] All monitoring tests completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

if __name__ == "__main__":
    main()
