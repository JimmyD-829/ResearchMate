from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class FollowCreate:
    company_name: str
    stock_code: Optional[str] = None

@dataclass
class FollowResponse:
    id: str
    user_id: str
    company_name: str
    stock_code: Optional[str]
    created_at: datetime