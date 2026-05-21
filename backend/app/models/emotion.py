from sqlalchemy import Column, String, Date, DECIMAL, Integer
from ..database import Base
import uuid

class EmotionTrend(Base):
    __tablename__ = "emotion_trends"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    daily_score = Column(DECIMAL(5, 2), nullable=False)
    article_count = Column(Integer, default=0)
    positive_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
