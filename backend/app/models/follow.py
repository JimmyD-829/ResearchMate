from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from ..database import Base
import uuid

class UserFollow(Base):
    __tablename__ = "user_follows"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    stock_code = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
