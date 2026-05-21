from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from ..models.emotion import EmotionTrend
from ..models.news import NewsArticle
from ..schemas.emotion import EmotionScoreResponse, EmotionTrendResponse, EmotionTrendData
from datetime import date, timedelta

class EmotionService:
    @staticmethod
    def get_emotion_score(db: Session, company_name: str) -> EmotionScoreResponse:
        today = date.today()
        seven_days_ago = today - timedelta(days=7)
        thirty_days_ago = today - timedelta(days=30)
        
        today_score = db.query(func.avg(EmotionTrend.daily_score))\
            .filter(EmotionTrend.company_name == company_name)\
            .filter(EmotionTrend.date == today)\
            .scalar() or 0
        
        last_7d_avg = db.query(func.avg(EmotionTrend.daily_score))\
            .filter(EmotionTrend.company_name == company_name)\
            .filter(EmotionTrend.date >= seven_days_ago)\
            .scalar() or 0
        
        last_30d_avg = db.query(func.avg(EmotionTrend.daily_score))\
            .filter(EmotionTrend.company_name == company_name)\
            .filter(EmotionTrend.date >= thirty_days_ago)\
            .scalar() or 0
        
        if today_score > 20:
            label = "positive"
        elif today_score < -20:
            label = "negative"
        else:
            label = "neutral"
        
        return EmotionScoreResponse(
            company_name=company_name,
            current_score=round(float(today_score), 2),
            current_label=label,
            last_7d_avg=round(float(last_7d_avg), 2),
            last_30d_avg=round(float(last_30d_avg), 2)
        )
    
    @staticmethod
    def get_emotion_trend(db: Session, company_name: str, days: int = 30) -> EmotionTrendResponse:
        start_date = date.today() - timedelta(days=days)
        
        trends = db.query(EmotionTrend)\
            .filter(EmotionTrend.company_name == company_name)\
            .filter(EmotionTrend.date >= start_date)\
            .order_by(EmotionTrend.date)\
            .all()
        
        trend_data = [
            EmotionTrendData(
                date=trend.date,
                daily_score=float(trend.daily_score),
                article_count=trend.article_count
            )
            for trend in trends
        ]
        
        return EmotionTrendResponse(
            company_name=company_name,
            trend=trend_data
        )
    
    @staticmethod
    def update_daily_emotion(db: Session, company_name: str):
        today = date.today()
        
        today_articles = db.query(NewsArticle)\
            .filter(NewsArticle.company_name == company_name)\
            .filter(func.date(NewsArticle.publish_time) == today)\
            .all()
        
        if not today_articles:
            return
        
        scores = [article.emotion_score for article in today_articles if article.emotion_score is not None]
        if scores:
            daily_score = sum(scores) / len(scores)
        else:
            daily_score = 0
        
        positive_count = sum(1 for a in today_articles if a.emotion_label == "positive")
        neutral_count = sum(1 for a in today_articles if a.emotion_label == "neutral")
        negative_count = sum(1 for a in today_articles if a.emotion_label == "negative")
        
        existing = db.query(EmotionTrend)\
            .filter(EmotionTrend.company_name == company_name)\
            .filter(EmotionTrend.date == today)\
            .first()
        
        if existing:
            existing.daily_score = daily_score
            existing.article_count = len(today_articles)
            existing.positive_count = positive_count
            existing.neutral_count = neutral_count
            existing.negative_count = negative_count
        else:
            trend = EmotionTrend(
                company_name=company_name,
                date=today,
                daily_score=daily_score,
                article_count=len(today_articles),
                positive_count=positive_count,
                neutral_count=neutral_count,
                negative_count=negative_count
            )
            db.add(trend)
        
        db.commit()
