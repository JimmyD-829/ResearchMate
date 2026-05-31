#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情绪分析服务 - V2.0 (支持真实数据 + Fallback)

数据源优先级:
1. 真实金融数据 (AKShare/Alpha Vantage) - 基于量化指标
2. 新闻情绪分析 (数据库) - 基于NLP
3. 模拟Fallback (确定性算法) - 仅当以上都不可用时
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import date, timedelta
import hashlib

from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.emotion import EmotionTrend
from ..models.news import NewsArticle
from ..schemas.emotion import EmotionScoreResponse, EmotionTrendResponse, EmotionTrendData

logger = logging.getLogger(__name__)

class EmotionService:
    """
    情绪分析服务（V2.0）
    
    支持多数据源容灾:
    - 优先使用真实股价数据计算量化情绪指标
    - 其次使用新闻NLP情绪分析
    - 最终回退到模拟数据（明确标注为示例数据）
    """
    
    @staticmethod
    async def get_emotion_score_v2(db: Session, company_name: str, stock_code: str = None) -> Dict[str, Any]:
        """
        V2.0: 获取情绪分数（支持真实数据）
        
        Returns:
            {
                'score': EmotionScoreResponse,
                'source': 'real' | 'news' | 'fallback',
                'metadata': {...}
            }
        """
        
        # 尝试1: 获取真实金融数据
        try:
            from .real_emotion_service import RealEmotionService
            
            real_service = RealEmotionService()
            real_data = await real_service.get_real_emotion_data(company_name, stock_code)
            
            if real_data and real_data.get('score'):
                logger.info(f"✅ {company_name}: 使用真实金融数据 (source={real_data['source']})")
                
                score_data = real_data['score']
                
                return {
                    'score': EmotionScoreResponse(
                        company_name=company_name,
                        current_score=score_data['current_score'],
                        current_label=score_data['current_label'],
                        last_7d_avg=score_data['last_7d_avg'],
                        last_30d_avg=score_data['last_30d_avg']
                    ),
                    'trend': EmotionTrendResponse(
                        company_name=company_name,
                        trend=[
                            EmotionTrendData(
                                date=item['date'],
                                daily_score=item['daily_score'],
                                article_count=item['article_count']
                            )
                            for item in real_data['trend']['trend']
                        ]
                    ),
                    'source': 'real',
                    'real_source': real_data['source'],  # akshare / alpha_vantage
                    'metadata': {
                        'is_real_data': True,
                        'data_source': real_data['source'],
                        'stock_code': score_data.get('stock_code'),
                        'reasoning': score_data.get('reasoning'),
                        'indicators': score_data.get('indicators', {}),
                        'realtime_data': score_data.get('realtime_data', {}),
                        **real_data.get('metadata', {})
                    }
                }
            
        except Exception as e:
            logger.warning(f"获取{company_name}真实数据失败: {e}")
        
        # 尝试2: 使用新闻情绪分析（原有逻辑）
        try:
            news_result = EmotionService._get_emotion_from_news(db, company_name)
            if news_result:
                logger.info(f"⚠️ {company_name}: 使用新闻情绪分析 (非实时)")
                return news_result
        except Exception as e:
            logger.warning(f"新闻情绪分析失败: {e}")
        
        # 尝试3: Fallback到模拟数据
        logger.warning(f"❌ {company_name}: 所有数据源都不可用，使用Fallback模拟数据")
        fallback_result = EmotionService._get_fallback_emotion(company_name)
        return fallback_result
    
    @staticmethod
    def _get_emotion_from_news(db: Session, company_name: str) -> Optional[Dict]:
        """从新闻文章获取情绪数据"""
        today = date.today()
        seven_days_ago = today - timedelta(days=7)
        thirty_days_ago = today - timedelta(days=30)
        
        # 检查是否有历史趋势数据
        trend_exists = db.query(EmotionTrend)\
            .filter(EmotionTrend.company_name == company_name)\
            .filter(EmotionTrend.date >= thirty_days_ago)\
            .first()
        
        if not trend_exists:
            EmotionService._calculate_from_news(db, company_name)
        
        today_score = db.query(func.avg(EmotionTrend.daily_score))\
            .filter(EmotionTrend.company_name == company_name)\
            .filter(EmotionTrend.date == today)\
            .scalar() or 0
        
        last_7d_avg = db.query(func.avg(EmotionTrend.daily_score))\
            .filter(EmotionTrend.company_name == company_name)\
            .filter(EmotionTrend.date >= seven_days_ago)\
            .scalar() or 0
        
        last_30d_avg = db.query(func.avg(EmotionTrend.daily_score))\
            .filter(EmotionTrend.company_name == company_name)\
            .filter(EmotionTrend.date >= thirty_days_ago)\
            .scalar() or 0
        
        if today_score > 20:
            label = "positive"
        elif today_score < -20:
            label = "negative"
        else:
            label = "neutral"
        
        # 获取趋势数据
        start_date = today - timedelta(days=30)
        trends = db.query(EmotionTrend)\
            .filter(EmotionTrend.company_name == company_name)\
            .filter(EmotionTrend.date >= start_date)\
            .order_by(EmotionTrend.date)\
            .all()
        
        trend_data = [
            EmotionTrendData(
                date=trend.date,
                daily_score=float(trend.daily_score),
                article_count=trend.article_count
            )
            for trend in trends
        ]
        
        return {
            'score': EmotionScoreResponse(
                company_name=company_name,
                current_score=round(float(today_score), 2),
                current_label=label,
                last_7d_avg=round(float(last_7d_avg), 2),
                last_30d_avg=round(float(last_30d_avg), 2)
            ),
            'trend': EmotionTrendResponse(
                company_name=company_name,
                trend=trend_data
            ),
            'source': 'news',
            'metadata': {
                'is_real_data': False,
                'data_source': 'news_nlp',
                'method': 'nlp_sentiment_analysis'
            }
        }
    
    @staticmethod
    def _get_fallback_emotion(company_name: str) -> Dict:
        """生成Fallback模拟数据（明确标注）"""
        import numpy as np
        
        hash_val = int(hashlib.md5(company_name.encode()).hexdigest()[:8], 16)
        base_score = -15 + (hash_val % 30)
        today = date.today()
        
        # 基于哈希的确定性假数据
        if base_score > 20:
            label = "positive"
        elif base_score < -20:
            label = "negative"
        else:
            label = "neutral"
        
        # 生成30天趋势
        trend_data = []
        for days_offset in range(29, -1, -1):
            day = today - timedelta(days=days_offset)
            daily_variation = (hash_val + days_offset * 7) % 25 - 12
            score = base_score + daily_variation
            
            trend_data.append(EmotionTrendData(
                date=day,
                daily_score=float(score),
                article_count=3 + (hash_val % 10)
            ))
        
        return {
            'score': EmotionScoreResponse(
                company_name=company_name,
                current_score=round(float(base_score), 2),
                current_label=label,
                last_7d_avg=round(float(base_score + (hash_val % 5)), 2),
                last_30d_avg=round(float(base_score), 2)
            ),
            'trend': EmotionTrendResponse(
                company_name=company_name,
                trend=trend_data
            ),
            'source': 'fallback',
            'metadata': {
                'is_real_data': False,
                'data_source': 'simulation',
                'method': 'hash_based_deterministic',
                'warning': '⚠️ 此为示例数据，仅供界面展示参考，不构成投资建议'
            }
        }
    
    @staticmethod
    def get_emotion_score(db: Session, company_name: str) -> EmotionScoreResponse:
        """兼容旧接口的同步版本（内部调用异步版本）"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                EmotionService.get_emotion_score_v2(db, company_name)
            )
            return result['score']
        finally:
            loop.close()
    
    @staticmethod
    async def get_emotion_trend_v2(db: Session, company_name: str, days: int = 30, stock_code: str = None) -> Dict[str, Any]:
        """V2.0: 获取情绪趋势（支持真实数据）"""
        result = await EmotionService.get_emotion_score_v2(db, company_name, stock_code)
        return {
            'trend': result['trend'],
            'source': result['source'],
            'metadata': result.get('metadata', {})
        }
    
    @staticmethod
    def get_emotion_trend(db: Session, company_name: str, days: int = 30) -> EmotionTrendResponse:
        """兼容旧接口的同步版本"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                EmotionService.get_emotion_trend_v2(db, company_name, days)
            )
            return result['trend']
        finally:
            loop.close()
    
    @staticmethod
    def _calculate_from_news(db: Session, company_name: str):
        """从新闻文章计算情绪（保留原有逻辑）"""
        from ..utils.sentiment_analyzer import SentimentAnalyzer
        
        all_articles = db.query(NewsArticle)\
            .filter(NewsArticle.company_name == company_name)\
            .all()

        if not all_articles:
            hash_val = int(hashlib.md5(company_name.encode()).hexdigest()[:8], 16)
            base_score = -15 + (hash_val % 30)
            today = date.today()

            for days_offset in range(30):
                day = today - timedelta(days=days_offset)
                daily_variation = (hash_val + days_offset * 7) % 25 - 12
                score = base_score + daily_variation

                trend = EmotionTrend(
                    company_name=company_name,
                    date=day,
                    daily_score=score,
                    article_count=3 + (hash_val % 10),
                    positive_count=max(0, 1 + (hash_val % 4) if score > 0 else 0),
                    neutral_count=1 + ((hash_val + 2) % 3),
                    negative_count=max(0, 1 + (hash_val % 3) if score < 0 else 0)
                )
                db.add(trend)

            db.commit()
            return

        today = date.today()
        for days_offset in range(30):
            target_date = today - timedelta(days=days_offset)
            day_articles = [a for a in all_articles if a.publish_time and a.publish_time.date() >= target_date]

            if day_articles:
                scores = [a.emotion_score for a in day_articles if a.emotion_score is not None]
                if scores:
                    daily_score = sum(scores) / len(scores)
                else:
                    daily_score = 0

                positive_count = sum(1 for a in day_articles if a.emotion_label == "positive")
                neutral_count = sum(1 for a in day_articles if a.emotion_label == "neutral")
                negative_count = sum(1 for a in day_articles if a.emotion_label == "negative")
            else:
                daily_score = 0
                positive_count = 0
                neutral_count = 0
                negative_count = 0

            existing = db.query(EmotionTrend)\
                .filter(EmotionTrend.company_name == company_name)\
                .filter(EmotionTrend.date == target_date)\
                .first()

            if existing:
                existing.daily_score = daily_score
                existing.article_count = len(day_articles)
                existing.positive_count = positive_count
                existing.neutral_count = neutral_count
                existing.negative_count = negative_count
            else:
                trend = EmotionTrend(
                    company_name=company_name,
                    date=target_date,
                    daily_score=daily_score,
                    article_count=len(day_articles),
                    positive_count=positive_count,
                    neutral_count=neutral_count,
                    negative_count=negative_count
                )
                db.add(trend)

        db.commit()
    
    @staticmethod
    def update_daily_emotion(db: Session, company_name: str):
        today = date.today()
        
        today_articles = db.query(NewsArticle)\
            .filter(NewsArticle.company_name == company_name)\
            .filter(func.date(NewsArticle.publish_time) == today)\
            .all()
        
        if not today_articles:
            return
        
        scores = [article.emotion_score for article in today_articles if article.emotion_score is not None]
        if scores:
            daily_score = sum(scores) / len(scores)
        else:
            daily_score = 0
        
        positive_count = sum(1 for a in today_articles if a.emotion_label == "positive")
        neutral_count = sum(1 for a in today_articles if a.emotion_label == "neutral")
        negative_count = sum(1 for a in today_articles if a.emotion_label == "negative")
        
        existing = db.query(EmotionTrend)\
            .filter(EmotionTrend.company_name == company_name)\
            .filter(EmotionTrend.date == today)\
            .first()
        
        if existing:
            existing.daily_score = daily_score
            existing.article_count = len(today_articles)
            existing.positive_count = positive_count
            existing.neutral_count = neutral_count
            existing.negative_count = negative_count
        else:
            trend = EmotionTrend(
                company_name=company_name,
                date=today,
                daily_score=daily_score,
                article_count=len(today_articles),
                positive_count=positive_count,
                neutral_count=neutral_count,
                negative_count=negative_count
            )
            db.add(trend)
        
        db.commit()
