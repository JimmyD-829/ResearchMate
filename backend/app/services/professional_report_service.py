import json
import time
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from ..models.financial_report import FinancialReport
from ..utils.advanced_pdf_parser import AdvancedPDFParser
from ..utils.professional_ai_client import ProfessionalAIClient

logger = logging.getLogger(__name__)

class ProfessionalReportService:
    """
    专业级财报分析服务 - V2
    
    完整流程：
    1. PDF完整解析（全文档+智能分块）
    2. AI结构化提取（GPT-3.5/4）
    3. 专业分析报告生成
    4. JSON标准化输出
    """
    
    def __init__(self):
        self.pdf_parser = AdvancedPDFParser()
        self.ai_client = ProfessionalAIClient()
    
    @staticmethod
    def create_report(db: Session, user_id: str, file_path: str, company_name: str = "未知") -> FinancialReport:
        """创建财报记录"""
        report = FinancialReport(
            user_id=user_id,
            company_name=company_name,
            file_path=file_path,
            status="processing",
            version="v2.0"
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        
        logger.info(f"[创建报告] ID={report.id}, 公司={company_name}")
        return report
    
    @staticmethod
    def get_report(db: Session, report_id: str) -> Optional[FinancialReport]:
        """获取单个报告"""
        return db.query(FinancialReport).filter(FinancialReport.id == report_id).first()
    
    @staticmethod
    def get_user_reports(db: Session, user_id: str) -> list:
        """获取用户的所有报告（按时间倒序）"""
        return db.query(FinancialReport)\
            .filter(FinancialReport.user_id == user_id)\
            .order_by(FinancialReport.upload_time.desc())\
            .all()
    
    @staticmethod
    def delete_report(db: Session, report_id: str) -> bool:
        """删除报告"""
        report = ProfessionalReportService.get_report(db, report_id)
        if report:
            db.delete(report)
            db.commit()
            return True
        return False
    
    def parse_and_analyze_report(self, report: FinancialReport) -> Dict[str, Any]:
        """
        核心方法：完整的财报解析与分析流程
        
        Args:
            report: FinancialReport对象
            
        Returns:
            包含完整分析结果的字典
        """
        start_time = time.time()
        
        try:
            # ========== 阶段1: PDF解析 ==========
            logger.info(f"[阶段1] 开始解析PDF: {report.file_path}")
            
            # 检查文件基本信息
            pdf_info = self.pdf_parser.get_pdf_info(report.file_path)
            if "error" in pdf_info:
                raise Exception(f"无法读取PDF: {pdf_info['error']}")
            
            # 检查是否加密
            if pdf_info.get("is_encrypted"):
                raise Exception("PDF已加密，请提供未加密版本")
            
            # 检查是否扫描版
            if self.pdf_parser.is_scanned_pdf(report.file_path):
                raise Exception("该PDF为扫描件(图片格式)，暂不支持OCR识别。建议使用文字版年报PDF。")
            
            # 提取完整文本
            full_text = self.pdf_parser.extract_full_text(report.file_path)
            if not full_text or len(full_text.strip()) < 100:
                raise Exception("无法提取足够的文本内容。请确保PDF包含可提取的文字。")
            
            # 智能分块（用于长文档）
            chunks = self.pdf_parser.extract_with_smart_chunks(report.file_path)
            chunks_metadata = {
                "total_chunks": len(chunks),
                "total_chars": len(full_text),
                "pdf_pages": pdf_info.get("total_pages", 0),
                "file_size_mb": pdf_info.get("file_size_mb", 0)
            }
            
            logger.info(f"[阶段1完成] PDF解析成功 | {chunks_metadata['pdf_pages']}页, {len(full_text)}字符, {len(chunks)}个分块")
            
            # ========== 阶段2: AI结构化提取 + 分析 ==========
            logger.info("[阶段2] 开始AI智能分析...")
            
            analysis_result = self.ai_client.analyze_financial_report_v2(
                pdf_text=full_text,
                chunks_info=chunks_metadata
            )
            
            if "error" in analysis_result and "fallback_data" in analysis_result:
                # AI失败但有降级数据
                logger.warning(f"[⚠️ 警告] AI分析部分失败，使用降级数据")
                final_result = analysis_result["fallback_data"]
                final_result["warning"] = f"AI分析遇到问题: {analysis_result['error']}"
            elif "error" in analysis_result:
                # 完全失败
                raise Exception(f"AI分析失败: {analysis_result['error']}")
            else:
                final_result = analysis_result
            
            # ========== 阶段3: 后处理与标准化 ==========
            processing_time = round(time.time() - start_time, 2)
            
            final_result["processing_info"] = {
                "processing_time_seconds": processing_time,
                "pdf_pages_analyzed": chunks_metadata["pdf_pages"],
                "file_size_mb": chunks_metadata["file_size_mb"],
                "text_extracted_chars": len(full_text),
                "method": "full_document_ai_analysis_v2"
            }
            
            logger.info(f"[✅ 完成] 财报分析总耗时: {processing_time}秒")
            
            return final_result
            
        except Exception as e:
            processing_time = round(time.time() - start_time, 2)
            error_result = {
                "error": str(e),
                "processing_time": processing_time,
                "stage": "failed",
                "suggestion": "请检查PDF文件是否为有效的文字版年报（非扫描件）"
            }
            logger.error(f"[❌ 失败] 分析过程出错: {str(e)}", exc_info=True)
            return error_result
    
    @staticmethod
    def update_report_with_analysis(db: Session, report_id: str, analysis_data: Dict) -> bool:
        """
        将分析结果更新到数据库
        
        Args:
            db: 数据库会话
            report_id: 报告ID
            analysis_data: AI分析结果JSON
        """
        try:
            report = ProfessionalReportService.get_report(db, report_id)
            if not report:
                logger.error(f"[错误] 报告不存在: {report_id}")
                return False
            
            # 更新基础字段（从分析结果中提取）
            metadata = analysis_data.get("report_metadata", {})
            financials = analysis_data.get("financial_statements", {})
            income_stmt = financials.get("income_statement", {})
            metrics = analysis_data.get("key_metrics", {})
            profitability = metrics.get("profitability", {})
            
            report.company_name = metadata.get("company_name", report.company_name)
            report.stock_code = metadata.get("stock_code", report.stock_code)
            
            # 转换并存储数值字段
            try:
                revenue_str = income_stmt.get("total_revenue")
                if revenue_str:
                    report.revenue = float(str(revenue_str).replace(",", "").replace("亿", ""))
                
                profit_str = income_stmt.get("net_profit")
                if profit_str:
                    report.net_profit = float(str(profit_str).replace(",", "").replace("亿", ""))
                
                cash_flow_data = financials.get("cash_flow", {})
                ocf_str = cash_flow_data.get("operating_cash_flow")
                if ocf_str:
                    report.cash_flow = float(str(ocf_str).replace(",", "").replace("亿", ""))
                
                solvency = metrics.get("solvency", {})
                debt_str = solvency.get("debt_ratio")
                if debt_str:
                    report.debt_ratio = float(str(debt_str).replace("%", ""))
                
                gross_margin_str = profitability.get("gross_margin")
                if gross_margin_str:
                    report.gross_margin = float(str(gross_margin_str).replace("%", ""))
                    
            except (ValueError, TypeError) as e:
                logger.warning(f"[警告] 数值转换失败: {e}")
            
            # 存储完整JSON数据
            report.parsed_data_json = analysis_data
            
            # 生成摘要（从分析报告中提取）
            analysis_report = analysis_data.get("analysis_report", {})
            if analysis_report:
                summary_parts = [
                    analysis_report.get("executive_summary", ""),
                    "\n\n【投资建议】\n",
                    json.dumps(analysis_report.get("investment_recommendation", {}), ensure_ascii=False, indent=2)
                ]
                report.ai_summary = "\n".join(summary_parts)
            
            # 更新元数据
            meta = analysis_data.get("metadata", {})
            report.status = "success"
            report.analysis_model = meta.get("analysis_model", "unknown")
            report.confidence_score = meta.get("confidence_score", 0)
            report.processing_time_seconds = analysis_data.get("processing_info", {}).get("processing_time_seconds", 0)
            report.pdf_pages_analyzed = analysis_data.get("processing_info", {}).get("pdf_pages_analyzed", 0)
            report.error_message = None
            
            db.commit()
            
            logger.info(f"[✅ 成功] 报告已更新 | ID={report_id}, 置信度={report.confidence_score}%")
            return True
            
        except Exception as e:
            logger.error(f"[❌ 错误] 数据库更新失败: {e}", exc_info=True)
            
            # 标记为失败
            try:
                report.status = "failed"
                report.error_message = str(e)
                db.commit()
            except:
                pass
            
            return False
    
    @staticmethod
    def compare_reports_v2(db: Session, report_ids: list) -> Dict[str, Any]:
        """
        历史对比功能 - 对比多份财报
        
        Args:
            report_ids: 要对比的报告ID列表
            
        Returns:
            对比分析结果
        """
        reports_data = []
        
        for rid in report_ids:
            report = ProfessionalReportService.get_report(db, rid)
            if report and report.parsed_data_json:
                reports_data.append({
                    "report_id": report.id,
                    "company_name": report.company_name,
                    "upload_time": report.upload_time.isoformat() if report.upload_time else None,
                    "data": report.parsed_data_json
                })
        
        if len(reports_data) < 2:
            return {"error": "需要至少2份报告进行对比"}
        
        # 使用AI进行对比分析
        ai_client = ProfessionalAIClient()
        comparison_prompt = f"""作为专业分析师，请对比以下{len(reports_data)}期财报的关键变化：

{json.dumps(reports_data, ensure_ascii=False, indent=2)[:5000]}

请生成对比分析报告，包含：
1. 关键指标变化趋势表
2. 增长/下降原因分析
3. 改善建议

返回JSON格式。"""

        try:
            result = ai_client.client.chat.completions.create(
                model=ai_client.model,
                messages=[{"role": "user", "content": comparison_prompt}],
                temperature=0.5,
                max_tokens=2000
            )
            
            comparison_analysis = json.loads(result.choices[0].message.content)
            
            return {
                "success": True,
                "reports_compared": len(reports_data),
                "comparison_data": comparison_analysis,
                "raw_reports": reports_data
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "reports_compared": len(reports_data),
                "note": "AI对比分析失败，但原始数据可用"
            }


# 兼容旧接口
ReportService = ProfessionalReportService
