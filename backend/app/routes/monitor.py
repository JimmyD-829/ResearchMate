from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.data_monitor import DataQualityMonitor

router = APIRouter()


@router.get("/monitor/dashboard")
async def get_monitoring_dashboard(db: Session = Depends(get_db)):
    """获取综合监控面板数据"""
    try:
        dashboard = DataQualityMonitor.get_comprehensive_dashboard(db)
        return {
            "success": True,
            "data": dashboard
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate dashboard: {str(e)}")


@router.get("/monitor/industry-accuracy")
async def check_industry_classification_accuracy():
    """检查行业分类准确率"""
    try:
        result = DataQualityMonitor.check_industry_classification_accuracy()
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitor/news-quality")
async def check_news_data_quality(db: Session = Depends(get_db)):
    """检查新闻数据质量"""
    try:
        result = DataQualityMonitor.check_news_data_quality(db)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitor/emotion-coverage")
async def check_emotion_data_coverage(db: Session = Depends(get_db)):
    """检查情绪数据覆盖率"""
    try:
        result = DataQualityMonitor.check_emotion_data_coverage(db)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitor/reports-quality")
async def check_financial_reports_quality(db: Session = Depends(get_db)):
    """检查财报数据质量"""
    try:
        result = DataQualityMonitor.check_financial_reports_quality(db)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitor/system-health")
async def get_system_health():
    """获取系统健康状态"""
    try:
        result = DataQualityMonitor.generate_system_health_report()
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
