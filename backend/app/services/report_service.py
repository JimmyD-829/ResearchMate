from sqlalchemy.orm import Session
from ..models.financial_report import FinancialReport
from ..schemas.report import FinancialReportUpdate
from ..utils.pdf_parser import PDFParser
from ..utils.ai_client import AIClient
import json
import os

class ReportService:
    @staticmethod
    def create_report(db: Session, user_id: str, file_path: str, company_name: str = "未知") -> FinancialReport:
        report = FinancialReport(
            user_id=user_id,
            company_name=company_name,
            file_path=file_path,
            status="processing"
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report
    
    @staticmethod
    def get_report(db: Session, report_id: str) -> FinancialReport:
        return db.query(FinancialReport).filter(FinancialReport.id == report_id).first()
    
    @staticmethod
    def get_user_reports(db: Session, user_id: str) -> list:
        return db.query(FinancialReport).filter(FinancialReport.user_id == user_id).all()
    
    @staticmethod
    def update_report(db: Session, report_id: str, update_data: FinancialReportUpdate) -> FinancialReport:
        report = ReportService.get_report(db, report_id)
        if report:
            for key, value in update_data.dict(exclude_unset=True).items():
                setattr(report, key, value)
            db.commit()
            db.refresh(report)
        return report
    
    @staticmethod
    def delete_report(db: Session, report_id: str) -> bool:
        report = ReportService.get_report(db, report_id)
        if report:
            db.delete(report)
            db.commit()
            return True
        return False
    
    @staticmethod
    def parse_report(report: FinancialReport) -> dict:
        if PDFParser.is_scanned_pdf(report.file_path):
            return {"error": "该文件为扫描件，OCR功能将在后续版本支持"}
        
        text = PDFParser.extract_text(report.file_path)
        if not text:
            return {"error": "无法提取PDF文本内容"}
        
        ai_client = AIClient()
        result = ai_client.parse_financial_report(text)
        
        try:
            data = json.loads(result)
            return data
        except json.JSONDecodeError:
            return {"company_name": report.company_name}
    
    @staticmethod
    def generate_summary(data: dict) -> str:
        ai_client = AIClient()
        return ai_client.generate_summary(data)
