#!/usr/bin/env python3
"""
ResearchMate News Scheduler

Usage:
    python run_scheduler.py daily     # Run daily update (incremental)
    python run_scheduler.py force     # Force full regeneration
    python run_scheduler.py status    # Check last update time

Schedule with cron (Linux/Mac):
    0 8 * * * cd /path/to/backend && python run_scheduler.py daily >> /var/log/researchmate.log 2>&1

Schedule with Task Scheduler (Windows):
    Create task to run: python C:\path\to\backend\run_scheduler.py daily
    Trigger: Daily at 8:00 AM
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from app.services.news_scheduler import NewsScheduler
from app.database import SessionLocal
from app.models.news import NewsArticle

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()

    if command == "daily":
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting daily news update...")
        result = NewsScheduler.daily_news_update()
        print(f"\nResult: {result}")

    elif command == "force":
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting force update...")
        result = NewsScheduler.force_update_all()
        print(f"\nResult: {result}")

    elif command == "status":
        db = SessionLocal()
        try:
            total_articles = db.query(NewsArticle).count()
            latest_article = db.query(NewsArticle).order_by(NewsArticle.publish_time.desc()).first()

            print(f"\n{'='*60}")
            print("News Database Status")
            print(f"{'='*60}")
            print(f"Total Articles: {total_articles}")

            if latest_article:
                print(f"Latest Article: {latest_article.title[:50]}...")
                print(f"Latest Date: {latest_article.publish_time}")

                companies = db.query(NewsArticle.company_name).distinct().all()
                print(f"Companies Covered: {[c[0] for c in companies]}")
            else:
                print("No articles in database. Run 'python run_scheduler.py force' to initialize.")

            print(f"{'='*60}\n")
        finally:
            db.close()

    else:
        print(f"Unknown command: {command}")
        print("Use: daily, force, or status")

if __name__ == "__main__":
    main()