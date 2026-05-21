from sqlalchemy.orm import Session
from sqlalchemy import desc
from ..models.news import NewsArticle
from ..utils.sentiment_analyzer import SentimentAnalyzer
from dotenv import load_dotenv
import os
import requests
from datetime import datetime

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

class NewsService:
    @staticmethod
    def create_news_article(db: Session, data: dict) -> NewsArticle:
        label, score = SentimentAnalyzer.analyze(data["title"])
        article = NewsArticle(
            company_name=data["company_name"],
            title=data["title"],
            source=data["source"],
            url=data["url"],
            publish_time=data["publish_time"],
            emotion_score=score,
            emotion_label=label
        )
        db.add(article)
        db.commit()
        db.refresh(article)
        return article
    
    @staticmethod
    def get_news_by_company(db: Session, company_name: str, limit: int = 20, offset: int = 0) -> list:
        return db.query(NewsArticle)\
            .filter(NewsArticle.company_name == company_name)\
            .order_by(desc(NewsArticle.publish_time))\
            .offset(offset)\
            .limit(limit)\
            .all()
    
    @staticmethod
    def get_all_news(db: Session, limit: int = 20, offset: int = 0) -> list:
        return db.query(NewsArticle)\
            .order_by(desc(NewsArticle.publish_time))\
            .offset(offset)\
            .limit(limit)\
            .all()
    
    @staticmethod
    def get_news_for_companies(db: Session, company_names: list, limit: int = 20, offset: int = 0) -> list:
        return db.query(NewsArticle)\
            .filter(NewsArticle.company_name.in_(company_names))\
            .order_by(desc(NewsArticle.publish_time))\
            .offset(offset)\
            .limit(limit)\
            .all()
    
    @staticmethod
    def count_news(db: Session, company_name: str = None) -> int:
        query = db.query(NewsArticle)
        if company_name:
            query = query.filter(NewsArticle.company_name == company_name)
        return query.count()
    
    @staticmethod
    def fetch_news_from_api(keywords: list) -> list:
        results = []
        for keyword in keywords:
            url = f"https://newsapi.org/v2/everything?q={keyword}&apiKey={NEWS_API_KEY}&language=zh&pageSize=10"
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    for article in data.get("articles", []):
                        results.append({
                            "company_name": keyword,
                            "title": article.get("title", ""),
                            "source": article.get("source", {}).get("name", "Unknown"),
                            "url": article.get("url", ""),
                            "publish_time": datetime.fromisoformat(article.get("publishedAt", "").replace("Z", "+00:00"))
                        })
            except Exception as e:
                continue
        return results
