#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情绪分析路由 - V2.0 (支持真实金融数据)

新增功能:
- 返回数据源信息 (real/news/fallback)
- 返回技术指标详情
- 返回实时行情快照
- 支持异步处理
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import logging

from ..schemas.emotion import EmotionScoreResponse, EmotionTrendResponse
from ..services.emotion_service import EmotionService
from ..database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/emotion", tags=["emotion"])

class UpdateEmotionRequest(BaseModel):
    company_name: str

class EmotionScoreV2Response(EmotionScoreResponse):
    """V2.0: 增强版情绪分数响应"""
    source: str  # 'real' | 'news' | 'fallback'
    real_source: Optional[str] = None  # 'akshare' | 'alpha_vantage'
    is_real_data: bool = False
    metadata: Dict[str, Any] = {}
    
    class Config:
        from_attributes = True

class EmotionTrendV2Response:
    """V2.0: 增强版趋势响应"""
    def __init__(self, trend_data, source: str, metadata: Dict[str, Any] = {}):
        self.trend = trend_data
        self.source = source
        self.metadata = metadata

@router.get("/{company_name}")
async def get_emotion_score_v2(
    company_name: str,
    stock_code: Optional[str] = Query(None, description="股票代码（可选）"),
    db: Session = Depends(get_db)
):
    """
    V2.0: 获取情绪分数（优先使用真实金融数据）
    
    数据源优先级:
    1. AKShare (A股) / Alpha Vantage (美股) - 真实股价数据
    2. 新闻NLP分析 - 数据库中的新闻情绪
    3. Fallback模拟 - 仅当以上都不可用时（明确标注）
    """
    try:
        result = await EmotionService.get_emotion_score_v2(db, company_name, stock_code)
        
        # 构建增强版响应
        response = {
            "data": result['score'].dict(),
            "source": result['source'],
            "is_real_data": result.get('metadata', {}).get('is_real_data', False),
            "metadata": result.get('metadata', {})
        }
        
        if result.get('real_source'):
            response['real_source'] = result['real_source']
        
        logger.info(f"✅ {company_name} 情绪分数获取成功 (source={result['source']})")
        
        return response
        
    except Exception as e:
        logger.error(f"获取{company_name}情绪分数失败: {e}", exc_info=True)
        # 兜底：返回fallback数据
        fallback = EmotionService._get_fallback_emotion(company_name)
        return {
            "data": fallback['score'].dict(),
            "source": "fallback",
            "is_real_data": False,
            "metadata": fallback['metadata'],
            "error": str(e)
        }

@router.get("/{company_name}/trend")
async def get_emotion_trend_v2(
    company_name: str,
    days: int = Query(30, ge=1, le=365),
    stock_code: Optional[str] = Query(None, description="股票代码（可选）"),
    db: Session = Depends(get_db)
):
    """V2.0: 获取情绪趋势（支持真实数据）"""
    try:
        result = await EmotionService.get_emotion_trend_v2(db, company_name, days, stock_code)
        
        return {
            "data": result['trend'].dict(),
            "source": result['source'],
            "is_real_data": result.get('metadata', {}).get('is_real_data', False),
            "metadata": result.get('metadata', {})
        }
        
    except Exception as e:
        logger.error(f"获取{company_name}趋势失败: {e}", exc_info=True)
        fallback = EmotionService._get_fallback_emotion(company_name)
        return {
            "data": fallback['trend'].dict(),
            "source": "fallback",
            "is_real_data": False,
            "metadata": fallback['metadata'],
            "error": str(e)
        }

@router.post("/update")
def update_emotion_data(request: UpdateEmotionRequest, db: Session = Depends(get_db)):
    """更新每日情绪数据"""
    try:
        EmotionService.update_daily_emotion(db, request.company_name)
        return {
            "message": f"情绪数据已更新: {request.company_name}",
            "success": True,
            "note": "如需使用最新真实金融数据，请等待系统自动刷新或调用 /api/data/refresh"
        }
    except Exception as e:
        logger.error(f"更新{request.company_name}情绪数据失败: {e}")
        return {"message": f"更新失败: {str(e)}", "success": False}

@router.get("/debug/{company_name}")
async def debug_emotion_data(
    company_name: str,
    stock_code: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """调试接口：查看完整的数据源和计算过程"""
    try:
        result = await EmotionService.get_emotion_score_v2(db, company_name, stock_code)
        
        return {
            "company_name": company_name,
            "stock_code": stock_code,
            "data_source": result['source'],
            "is_real_data": result.get('metadata', {}).get('is_real_data', False),
            "score_summary": {
                "current_score": result['score'].current_score,
                "label": result['score'].current_label,
                "7d_avg": result['score'].last_7d_avg,
                "30d_avg": result['score'].last_30d_avg
            },
            "technical_indicators": result.get('metadata', {}).get('indicators', {}),
            "reasoning": result.get('metadata', {}).get('reasoning'),
            "realtime_snapshot": result.get('metadata', {}).get('realtime_data', {}),
            "calculation_metadata": result.get('metadata', {}),
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "company_name": company_name,
            "error": str(e),
            "data_source": "error",
            "is_real_data": False
        }
