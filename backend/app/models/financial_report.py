from sqlalchemy import Column, String, DateTime, Float, DECIMAL
from sqlalchemy.sql import func
from ..database import Base
import uuid

class FinancialReport(Base):
    __tablename__ = "financial_reports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    stock_code = Column(String)
    report_period = Column(DateTime(timezone=True))
    revenue = Column(DECIMAL(18, 2))
    net_profit = Column(DECIMAL(18, 2))
    cash_flow = Column(DECIMAL(18, 2))
    debt_ratio = Column(DECIMAL(5, 2))
    gross_margin = Column(DECIMAL(5, 2))
    ai_summary = Column(String)
    file_path = Column(String, nullable=False)
    status = Column(String, default="processing")
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
