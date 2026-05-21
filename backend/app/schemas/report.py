from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FinancialReportResponse(BaseModel):
    id: str
    user_id: str
    company_name: str
    stock_code: Optional[str]
    report_period: Optional[datetime]
    revenue: Optional[float]
    net_profit: Optional[float]
    cash_flow: Optional[float]
    debt_ratio: Optional[float]
    gross_margin: Optional[float]
    ai_summary: Optional[str]
    status: str
    upload_time: datetime

    class Config:
        from_attributes = True

class FinancialReportUpdate(BaseModel):
    company_name: Optional[str] = None
    stock_code: Optional[str] = None
    report_period: Optional[datetime] = None
    revenue: Optional[float] = None
    net_profit: Optional[float] = None
    cash_flow: Optional[float] = None
    debt_ratio: Optional[float] = None
    gross_margin: Optional[float] = None
    ai_summary: Optional[str] = None
