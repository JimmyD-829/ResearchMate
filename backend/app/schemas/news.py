from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class NewsArticleResponse:
    id: str
    company_name: str
    title: str
    source: str
    url: str
    publish_time: datetime
    emotion_score: Optional[float]
    emotion_label: Optional[str]
    created_at: datetime

@dataclass
class NewsListResponse:
    total: int
    items: List[NewsArticleResponse]