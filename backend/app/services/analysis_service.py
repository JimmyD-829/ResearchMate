from sqlalchemy.orm import Session
from ..models.financial_report import FinancialReport
from ..utils.ai_client import AIClient
import json

class AnalysisService:
    @staticmethod
    def natural_language_query(db: Session, user_id: str, query: str) -> dict:
        ai_client = AIClient()
        result = ai_client.natural_language_query(query)
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"result": result}
    
    @staticmethod
    def analyze_report_with_methodology(db: Session, report_id: str) -> dict:
        report = db.query(FinancialReport).filter(FinancialReport.id == report_id).first()
        if not report:
            return {"error": "报告不存在"}
        
        ai_client = AIClient()
        
        if report.parsed_data:
            parsed_data = json.loads(report.parsed_data)
        else:
            from .report_service import ReportService
            parsed_data = ReportService.parse_report(report)
            if "error" in parsed_data:
                return parsed_data
        
        result = ai_client.analyze_with_methodology(parsed_data)
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"analysis": result}
    
    @staticmethod
    def compare_reports(db: Session, user_id: str, report_ids: list) -> dict:
        reports = []
        for report_id in report_ids:
            report = db.query(FinancialReport).filter(
                FinancialReport.id == report_id,
                FinancialReport.user_id == user_id
            ).first()
            if report and report.parsed_data:
                try:
                    data = json.loads(report.parsed_data)
                    data["report_id"] = report.id
                    data["company_name"] = report.company_name
                    data["upload_time"] = report.created_at.isoformat()
                    reports.append(data)
                except json.JSONDecodeError:
                    pass
        
        if len(reports) < 2:
            return {"error": "需要至少2份财报进行对比"}
        
        ai_client = AIClient()
        result = ai_client.compare_reports(reports)
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"comparison": result}
    
    @staticmethod
    def industry_benchmark(db: Session, user_id: str, company_name: str) -> dict:
        ai_client = AIClient()
        result = ai_client.industry_benchmark(company_name)
        
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {"benchmark": result}
    
    @staticmethod
    def get_financial_health_score(data: dict) -> dict:
        score = 50
        factors = []
        
        if "financial_indicators" in data:
            indicators = data["financial_indicators"]
            
            if "roe" in indicators:
                roe = float(indicators["roe"].replace("%", "")) if isinstance(indicators["roe"], str) else indicators["roe"]
                if roe >= 15:
                    score += 15
                    factors.append("ROE优秀")
                elif roe >= 10:
                    score += 10
                    factors.append("ROE良好")
            
            if "roa" in indicators:
                roa = float(indicators["roa"].replace("%", "")) if isinstance(indicators["roa"], str) else indicators["roa"]
                if roa >= 8:
                    score += 10
                    factors.append("ROA优秀")
            
            if "debt_ratio" in indicators:
                debt_ratio = float(indicators["debt_ratio"].replace("%", "")) if isinstance(indicators["debt_ratio"], str) else indicators["debt_ratio"]
                if debt_ratio < 50:
                    score += 10
                    factors.append("负债率健康")
                elif debt_ratio < 70:
                    score += 5
                    factors.append("负债率适中")
            
            if "current_ratio" in indicators:
                current_ratio = float(indicators["current_ratio"])
                if current_ratio >= 1.5:
                    score += 10
                    factors.append("流动性充足")
                elif current_ratio >= 1:
                    score += 5
                    factors.append("流动性正常")
        
        score = min(100, max(0, score))
        
        level = "A" if score >= 80 else "B" if score >= 60 else "C" if score >= 40 else "D"
        
        return {
            "score": score,
            "level": level,
            "factors": factors,
            "suggestions": AnalysisService._generate_suggestions(score, data)
        }
    
    @staticmethod
    def _generate_suggestions(score: int, data: dict) -> list:
        suggestions = []
        
        if score < 60:
            suggestions.append("建议关注公司财务健康状况，可能存在一定风险")
        
        if "financial_indicators" in data:
            indicators = data["financial_indicators"]
            
            if "debt_ratio" in indicators:
                debt_ratio = float(indicators["debt_ratio"].replace("%", "")) if isinstance(indicators["debt_ratio"], str) else indicators["debt_ratio"]
                if debt_ratio >= 70:
                    suggestions.append(f"资产负债率{debt_ratio}%较高，建议关注偿债能力")
            
            if "current_ratio" in indicators:
                current_ratio = float(indicators["current_ratio"])
                if current_ratio < 1:
                    suggestions.append(f"流动比率{current_ratio}较低，短期偿债压力较大")
        
        if not suggestions:
            suggestions.append("财务状况良好，继续保持关注")
        
        return suggestions