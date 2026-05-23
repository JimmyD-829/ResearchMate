from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, List

@dataclass
class EmotionScoreResponse:
    company_name: str
    current_score: float
    current_label: str
    last_7d_avg: float
    last_30d_avg: float

@dataclass
class EmotionTrendData:
    date: date
    daily_score: float
    article_count: int

@dataclass
class EmotionTrendResponse:
    company_name: str
    trend: List[EmotionTrendData]