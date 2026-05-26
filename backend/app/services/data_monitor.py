import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from ..models.news import NewsArticle
from ..models.emotion import EmotionTrend
from ..models.financial_report import FinancialReport
from ..utils.ai_client import AIClient


class DataQualityMonitor:
    """数据质量监控系统"""

    # 测试用例 - 覆盖所有13个行业
    TEST_COMPANIES = [
        ("平安银行", "金融服务业"),
        ("思格新能源", "新能源与储能行业"),
        ("万向集团", "高端制造业"),
        ("腾讯控股", "科技互联网行业"),
        ("贵州茅台", "消费品与零售"),
        ("国家电网", "传统能源行业"),
        ("恒瑞医药", "医疗健康产业"),
        ("万科企业", "房地产与建筑"),
        ("顺丰控股", "交通运输与物流"),
        ("中芯国际", "半导体与电子信息"),
        ("新东方在线", "教育培训行业"),
        ("腾讯音乐娱乐", "文化传媒"),
        ("中国平安", "金融服务业"),  # 重复测试
        ("比亚迪股份", "新能源与储能行业"),  # 重复测试
    ]

    @staticmethod
    def check_industry_classification_accuracy() -> Dict:
        """检查行业分类准确率"""
        from ..utils.news_generator import NewsGenerator

        total = len(DataQualityMonitor.TEST_COMPANIES)
        correct = 0
        results = []
        errors = []

        for company, expected_industry in DataQualityMonitor.TEST_COMPANIES:
            try:
                # 使用新闻生成器的行业检测（13个行业）
                detected_industry_news = NewsGenerator._get_industry(company)

                # 映射到完整的行业名称
                industry_mapping = {
                    "金融": "金融服务业",
                    "新能源": "新能源与储能行业",
                    "制造": "高端制造业",
                    "科技": "科技互联网行业",
                    "消费": "消费品与零售",
                    "能源": "传统能源行业",
                    "医疗": "医疗健康产业",
                    "房地产": "房地产与建筑",
                    "交通": "交通运输与物流",
                    "半导体": "半导体与电子信息",
                    "教育": "教育培训行业",
                    "文化传媒": "文化传媒"
                }

                detected_full_name = industry_mapping.get(detected_industry_news, detected_industry_news)

                is_correct = detected_full_name == expected_industry or detected_industry_news in expected_industry
                if is_correct:
                    correct += 1

                results.append({
                    "company": company,
                    "expected": expected_industry,
                    "detected": detected_full_name,
                    "is_correct": is_correct
                })

            except Exception as e:
                errors.append({
                    "company": company,
                    "error": str(e)
                })

        accuracy = (correct / total * 100) if total > 0 else 0

        return {
            "total_tested": total,
            "correct": correct,
            "accuracy": round(accuracy, 2),
            "details": results,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }

    @staticmethod
    def check_news_data_quality(db: Session) -> Dict:
        """检查新闻数据质量"""
        try:
            total_news = db.query(NewsArticle).count()
            
            if total_news == 0:
                return {
                    "total_articles": 0,
                    "companies_with_news": 0,
                    "avg_per_company": 0,
                    "emotion_distribution": {},
                    "recent_7_days": 0,
                    "status": "no_data"
                }

            companies_with_news = db.query(
                NewsArticle.company_name
            ).distinct().count()

            avg_per_company = round(total_news / companies_with_news, 2) if companies_with_news > 0 else 0

            emotion_dist = {}
            emotions = db.query(NewsArticle.emotion_label, 
                              NewsArticle.id).all()
            for label, _ in emotions:
                emotion_dist[label] = emotion_dist.get(label, 0) + 1

            week_ago = datetime.now() - timedelta(days=7)
            recent_count = db.query(NewsArticle).filter(
                NewsArticle.publish_time >= week_ago
            ).count()

            return {
                "total_articles": total_news,
                "companies_with_news": companies_with_news,
                "avg_per_company": avg_per_company,
                "emotion_distribution": emotion_dist,
                "recent_7_days": recent_count,
                "status": "healthy"
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    @staticmethod
    def check_emotion_data_coverage(db: Session) -> Dict:
        """检查情绪数据覆盖率"""
        try:
            sample_companies = ["Microsoft", "Apple", "Tesla", "NVIDIA", 
                              "平安银行", "比亚迪", "贵州茅台"]
            
            coverage_results = []
            covered = 0
            
            for company in sample_companies:
                trend_count = db.query(EmotionTrend).filter(
                    EmotionTrend.company_name == company
                ).count()

                has_data = trend_count > 0
                if has_data:
                    covered += 1

                coverage_results.append({
                    "company": company,
                    "has_data": has_data,
                    "data_points": trend_count
                })

            coverage_rate = (covered / len(sample_companies) * 100) if sample_companies else 0

            return {
                "total_companies_tested": len(sample_companies),
                "companies_with_data": covered,
                "coverage_rate": round(coverage_rate, 2),
                "details": coverage_results,
                "status": "healthy" if coverage_rate >= 80 else "warning"
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    @staticmethod
    def check_financial_reports_quality(db: Session) -> Dict:
        """检查财报数据质量"""
        try:
            total_reports = db.query(FinancialReport).count()
            success_reports = db.query(FinancialReport).filter(
                FinancialReport.status == "success"
            ).count()

            success_rate = (success_reports / total_reports * 100) if total_reports > 0 else 0

            recent_reports = db.query(FinancialReport).filter(
                FinancialReport.upload_time >= datetime.now() - timedelta(days=7)
            ).count()

            return {
                "total_reports": total_reports,
                "successful_reports": success_reports,
                "success_rate": round(success_rate, 2),
                "recent_7_days": recent_reports,
                "status": "healthy" if success_rate >= 90 else "warning"
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    @staticmethod
    def generate_system_health_report() -> Dict:
        """生成系统健康报告"""
        report_time = datetime.now()
        
        health_status = {
            "timestamp": report_time.isoformat(),
            "system_uptime": "unknown",
            "components": {},
            "overall_status": "healthy"
        }

        components_to_check = [
            ("industry_classification", "Industry Classification"),
            ("news_generator", "News Generator"),
            ("ai_client", "AI Client"),
            ("database", "Database Connection")
        ]

        for component_id, component_name in components_to_check:
            try:
                if component_id == "industry_classification":
                    from ..utils.news_generator import NewsGenerator
                    test_result = NewsGenerator._get_industry("平安银行")
                    status = "operational" if test_result == "金融" else "degraded"
                    
                elif component_id == "news_generator":
                    from ..utils.news_generator import NewsGenerator
                    test_news = NewsGenerator.generate_news("TestCompany", count=1)
                    status = "operational" if len(test_news) > 0 else "degraded"
                    
                elif component_id == "ai_client":
                    ai_client = AIClient()
                    test_benchmark = ai_client.industry_benchmark("Test")
                    status = "operational" if test_benchmark else "degraded"
                    
                elif component_id == "database":
                    from ..database import SessionLocal
                    test_db = SessionLocal()
                    try:
                        test_db.execute("SELECT 1")
                        status = "operational"
                    except:
                        status = "degraded"
                    finally:
                        test_db.close()
                    
                else:
                    status = "unknown"

                health_status["components"][component_id] = {
                    "name": component_name,
                    "status": status,
                    "last_check": datetime.now().isoformat()
                }

            except Exception as e:
                health_status["components"][component_id] = {
                    "name": component_name,
                    "status": "error",
                    "error": str(e),
                    "last_check": datetime.now().isoformat()
                }
                health_status["overall_status"] = "degraded"

        return health_status

    @staticmethod
    def get_comprehensive_dashboard(db: Session) -> Dict:
        """获取综合监控面板数据"""
        dashboard = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "overall_health": "unknown",
                "data_quality_score": 0,
                "alerts_count": 0,
                "alerts": []
            },
            "metrics": {},
            "recommendations": []
        }

        try:
            industry_check = DataQualityMonitor.check_industry_classification_accuracy()
            news_check = DataQualityMonitor.check_news_data_quality(db)
            emotion_check = DataQualityMonitor.check_emotion_data_coverage(db)
            reports_check = DataQualityMonitor.check_financial_reports_quality(db)
            system_health = DataQualityMonitor.generate_system_health_report()

            dashboard["metrics"] = {
                "industry_classification": industry_check,
                "news_data_quality": news_check,
                "emotion_coverage": emotion_check,
                "financial_reports": reports_check,
                "system_health": system_health
            }

            scores = []
            alerts = []

            scores.append(industry_check.get("accuracy", 0))
            
            if news_check.get("status") == "healthy":
                scores.append(90 if news_check.get("avg_per_company", 0) >= 10 else 70)
            else:
                scores.append(50)
                alerts.append({
                    "type": "warning",
                    "message": "News data quality needs attention",
                    "detail": f"Only {news_check.get('avg_per_company', 0)} articles per company on average"
                })

            scores.append(emotion_check.get("coverage_rate", 0))
            
            if reports_check.get("status") == "healthy":
                scores.append(reports_check.get("success_rate", 0))
            else:
                scores.append(50)
                alerts.append({
                    "type": "warning",
                    "message": "Financial report processing has issues",
                    "detail": f"Success rate: {reports_check.get('success_rate', 0)}%"
                })

            if system_health.get("overall_status") != "healthy":
                alerts.append({
                    "type": "error",
                    "message": "System health check failed",
                    "detail": "Some components are not operational"
                })

            avg_score = sum(scores) / len(scores) if scores else 0

            dashboard["summary"]["data_quality_score"] = round(avg_score, 2)
            dashboard["summary"]["alerts_count"] = len(alerts)
            dashboard["summary"]["alerts"] = alerts

            if avg_score >= 90:
                dashboard["summary"]["overall_health"] = "excellent"
            elif avg_score >= 75:
                dashboard["summary"]["overall_health"] = "good"
            elif avg_score >= 60:
                dashboard["summary"]["overall_health"] = "fair"
            else:
                dashboard["summary"]["overall_health"] = "poor"

            if avg_score < 80:
                dashboard["summary"]["recommendations"].append(
                    "Review and improve data quality in underperforming modules"
                )
            if len(alerts) > 3:
                dashboard["summary"]["recommendations"].append(
                    "Multiple alerts detected - immediate attention required"
                )

        except Exception as e:
            dashboard["summary"]["overall_health"] = "error"
            dashboard["error"] = str(e)

        return dashboard
