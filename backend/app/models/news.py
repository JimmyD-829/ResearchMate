from sqlalchemy import Column, String, DateTime, DECIMAL
from sqlalchemy.sql import func
from ..database import Base
import uuid

class NewsArticle(Base):
    __tablename__ = "news_articles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = Column(String, nullable=False)
    title = Column(String, nullable=False)
    source = Column(String, nullable=False)
    url = Column(String, nullable=False)
    publish_time = Column(DateTime(timezone=True), nullable=False)
    emotion_score = Column(DECIMAL(5, 2))
    emotion_label = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
