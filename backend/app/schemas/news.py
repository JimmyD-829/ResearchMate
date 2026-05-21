from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class NewsArticleResponse(BaseModel):
    id: str
    company_name: str
    title: str
    source: str
    url: str
    publish_time: datetime
    emotion_score: Optional[float]
    emotion_label: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True

class NewsListResponse(BaseModel):
    total: int
    items: List[NewsArticleResponse]
