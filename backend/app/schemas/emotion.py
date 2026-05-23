from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

class EmotionScoreResponse(BaseModel):
    company_name: str
    current_score: float
    current_label: str
    last_7d_avg: float
    last_30d_avg: float

class EmotionTrendData(BaseModel):
    date: date
    daily_score: float
    article_count: int

class EmotionTrendResponse(BaseModel):
    company_name: str
    trend: List[EmotionTrendData]