from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FollowCreate(BaseModel):
    company_name: str
    stock_code: Optional[str] = None

class FollowResponse(BaseModel):
    id: str
    user_id: str
    company_name: str
    stock_code: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True