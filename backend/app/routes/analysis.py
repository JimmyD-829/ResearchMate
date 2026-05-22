from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.analysis_service import AnalysisService
from ..utils.auth import get_current_user
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

class NaturalQueryRequest(BaseModel):
    query: str

class ReportCompareRequest(BaseModel):
    report_ids: List[str]

class IndustryBenchmarkRequest(BaseModel):
    company_name: str

@router.post("/natural-query")
async def natural_language_query(
    request: NaturalQueryRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    result = AnalysisService.natural_language_query(db, user_id, request.query)
    return {"success": True, "data": result}

@router.get("/methodology/{report_id}")
async def analyze_with_methodology(
    report_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    result = AnalysisService.analyze_report_with_methodology(db, report_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "data": result}

@router.post("/compare")
async def compare_reports(
    request: ReportCompareRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    result = AnalysisService.compare_reports(db, user_id, request.report_ids)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"success": True, "data": result}

@router.post("/benchmark")
async def industry_benchmark(
    request: IndustryBenchmarkRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    result = AnalysisService.industry_benchmark(db, user_id, request.company_name)
    return {"success": True, "data": result}

@router.post("/health-score")
async def get_health_score(
    data: dict,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user)
):
    result = AnalysisService.get_financial_health_score(data)
    return {"success": True, "data": result}