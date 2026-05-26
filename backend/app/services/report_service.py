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
        pdf_info = PDFParser.get_pdf_info(report.file_path)

        if "error" in pdf_info:
            return {"error": "无法读取PDF文件信息"}

        if pdf_info.get("is_encrypted"):
            return {"error": "该PDF文件已加密，无法解析。请提供未加密的版本。"}

        if PDFParser.is_scanned_pdf(report.file_path):
            return {"error": "该PDF为扫描件（图片格式），暂不支持OCR识别功能。建议使用巨潮资讯网下载的文字版年报PDF或Excel格式的财务报表。"}


        text = PDFParser.extract_text(
            report.file_path,
            max_pages=30,
            max_chars=15000
        )

        if not text:
            return {"error": "无法提取PDF文本内容。请确保文件包含可提取的文字（非纯图片）。"}

        ai_client = AIClient()
        result_dict = ai_client.analyze_financial_report(text)

        if isinstance(result_dict, dict):
            data = result_dict
            data["processing_info"] = {
                "total_pages": pdf_info.get("total_pages", 0),
                "extracted_pages": min(30, pdf_info.get("total_pages", 0)),
                "text_length": len(text),
                "note": f"已提取前{min(30, pdf_info.get('total_pages', 0))}页内容进行分析"
            }
            return data
        else:
            return {"company_name": report.company_name, "raw_text_length": len(text)}
    
    @staticmethod
    def generate_summary(data: dict) -> str:
        ai_client = AIClient()
        return ai_client.generate_summary(data)
