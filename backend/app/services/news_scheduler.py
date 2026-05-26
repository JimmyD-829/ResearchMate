import sys
sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.news import NewsArticle
from ..models.follow import UserFollow
from ..utils.news_generator import NewsGenerator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsScheduler:
    @staticmethod
    def daily_news_update():
        logger.info("=" * 60)
        logger.info("Starting Daily News Update")
        logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)

        db = SessionLocal()

        try:
            followed_companies = db.query(UserFollow.company_name).distinct().all()
            company_list = [c[0] for c in followed_companies]

            if not company_list:
                logger.warning("No followed companies found. Using default companies.")
                company_list = ["Microsoft", "Apple", "Tesla", "NVIDIA", "平安银行", "比亚迪", "贵州茅台"]

            total_generated = 0
            total_updated = 0

            for company in company_list:
                try:
                    generated, updated = NewsScheduler._update_company_news(db, company)
                    total_generated += generated
                    total_updated += updated
                    logger.info(f"✅ {company}: Generated {generated}, Updated {updated}")
                except Exception as e:
                    logger.error(f"❌ {company} failed: {e}")

            logger.info("\n" + "=" * 60)
            logger.info(f"Daily Update Complete!")
            logger.info(f"Total: {total_generated} new articles, {total_updated} updated")
            logger.info("=" * 60)

            return {
                "success": True,
                "generated": total_generated,
                "updated": total_updated,
                "companies_processed": len(company_list),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Daily update failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    @staticmethod
    def _update_company_news(db: Session, company_name: str) -> tuple:
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        existing_today = db.query(NewsArticle)\
            .filter(NewsArticle.company_name == company_name)\
            .filter(NewsArticle.publish_time >= datetime.combine(today, datetime.min.time()))\
            .count()

        if existing_today >= 5:
            logger.info(f"   {company_name} already has {existing_today} articles today. Skipping.")
            return 0, 0

        cutoff_date = datetime.combine(yesterday, datetime.max.time())
        old_articles = db.query(NewsArticle)\
            .filter(NewsArticle.company_name == company_name)\
            .filter(NewsArticle.publish_time < cutoff_date)\
            .all()

        for article in old_articles[:10]:
            days_to_add = (today - article.publish_time.date()).days + 1
            new_publish_time = article.publish_time + timedelta(days=days_to_add)

            variation = __import__('random').uniform(-3, 3)
            new_score = max(-30, min(30, article.emotion_score + variation))

            if new_score > 10:
                new_label = "positive"
            elif new_score < -10:
                new_label = "negative"
            else:
                new_label = "neutral"

            article.publish_time = new_publish_time
            article.emotion_score = new_score
            article.emotion_label = new_label

        new_articles_needed = 5 - existing_today
        if new_articles_needed > 0:
            new_articles = NewsGenerator.generate_news(company_name, new_articles_needed)

            for news_item in new_articles:
                article = NewsArticle(
                    company_name=news_item["company_name"],
                    title=news_item["title"],
                    source=news_item["source"],
                    url=news_item["url"],
                    publish_time=datetime.now(),
                    emotion_score=float(news_item.get("emotion_score", 0)),
                    emotion_label=news_item.get("emotion_label", "neutral")
                )
                db.add(article)

        db.commit()

        return new_articles_needed, min(len(old_articles), 10)

    @staticmethod
    def force_update_all():
        logger.info("Starting Force Update for All Companies")
        db = SessionLocal()

        try:
            all_companies = db.query(UserFollow.company_name).distinct().all()
            company_list = [c[0] for c in all_companies]

            results = {}
            for company in company_list:
                try:
                    NewsScheduler._regenerate_company_news(db, company)
                    results[company] = "success"
                    logger.info(f"✅ Regenerated: {company}")
                except Exception as e:
                    results[company] = f"failed: {e}"
                    logger.error(f"❌ Failed: {company} - {e}")

            db.commit()
            return {"success": True, "results": results}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            db.close()

    @staticmethod
    def _regenerate_company_news(db: Session, company_name: str):
        db.query(NewsArticle).filter(NewsArticle.company_name == company_name).delete()

        fresh_news = NewsGenerator.generate_news(company_name, 15)

        for news_item in fresh_news:
            article = NewsArticle(
                company_name=news_item["company_name"],
                title=news_item["title"],
                source=news_item["source"],
                url=news_item["url"],
                publish_time=datetime.strptime(news_item["publish_time"], "%Y-%m-%d %H:%M:%S"),
                emotion_score=float(news_item.get("emotion_score", 0)),
                emotion_label=news_item.get("emotion_label", "neutral")
            )
            db.add(article)

        db.flush()