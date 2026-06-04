#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财报分析API - V2专业版

新功能：
- 完整PDF文档解析
- 真实AI智能分析（GPT-3.5/4）
- 结构化JSON输出
- 历史对比功能
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
from ..services.professional_report_service import ProfessionalReportService
from ..database import get_db
import os
import uuid
import tempfile
import logging

router = APIRouter(prefix="/api/reports", tags=["reports-v2"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_DIR = tempfile.gettempdir()
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


class ReportUploadResponse(BaseModel):
    """上传响应模型"""
    id: str
    company_name: str
    status: str
    message: str
    upload_time: str
    estimated_time: str = "30秒-2分钟"


class ReportDetailResponse(BaseModel):
    """报告详情响应模型"""
    success: bool
    data: Optional[dict] = None
    message: str = ""


class CompareRequest(BaseModel):
    """对比请求模型"""
    report_ids: List[str]


def process_report_v2_background(report_id: str, file_path: str):
    """
    V2后台处理 - 完整AI分析流程
    """
    from ..database import SessionLocal
    
    db_local = SessionLocal()
    try:
        service = ProfessionalReportService()
        report = service.get_report(db_local, report_id)
        
        if not report:
            logger.error(f"[错误] 报告不存在: {report_id}")
            return
        
        try:
            logger.info(f"[🚀 开始] V2完整分析 | Report ID: {report_id}")
            
            # 执行完整的解析+分析流程
            analysis_result = service.parse_and_analyze_report(report)
            
            if "error" in analysis_result and "fallback_data" not in analysis_result:
                # 分析完全失败
                ProfessionalReportService.update_report_with_analysis(db_local, report_id, {
                    "error": analysis_result.get("error"),
                    "analysis_report": {
                        "executive_summary": f"❌ 分析失败: {analysis_result['error']}"
                    }
                })
                return
            
            # 更新数据库（包含成功和降级的情况）
            success = ProfessionalReportService.update_report_with_analysis(
                db_local, 
                report_id, 
                analysis_result
            )
            
            if success:
                logger.info(f"[✅ 完成] Report ID: {report_id} 分析完成")
            else:
                logger.error(f"[❌ 失败] 数据库更新失败")
                
        except Exception as e:
            logger.error(f"[❌ 异常] 处理过程出错: {str(e)}", exc_info=True)
            
            # 标记失败状态
            try:
                report.status = "failed"
                report.error_message = str(e)
                db_local.commit()
            except:
                pass
                
    finally:
        db_local.close()


@router.post("/upload-v2", response_model=ReportUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_report_v2(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(lambda: {"id": "test_user"})
):
    """
    🚀 V2新版财报上传 - 专业级AI全文档分析
    
    特性：
    ✅ 解析完整PDF（无页数限制）
    ✅ AI智能提取财务数据（GPT-3.5/4）
    ✅ 生成约1000字专业投资分析报告
    ✅ 结构化JSON输出，前端可直接渲染
    
    处理时间：30秒-2分钟（异步后台处理）
    """
    
    # ===== 文件验证 =====
    if not file.filename:
        raise HTTPException(status_code=400, detail="请选择文件")
    
    file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    if file_ext != 'pdf':
        raise HTTPException(
            status_code=400, 
            detail="当前仅支持 PDF 格式。建议从巨潮资讯网下载文字版年报PDF"
        )
    
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"文件过大（最大50MB），当前: {len(content) / 1024 / 1024:.1f}MB"
        )
    
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="文件为空")
    
    # ===== 保存文件 =====
    file_id = str(uuid.uuid4())[:8]
    safe_filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    with open(file_path, 'wb') as f:
        f.write(content)
    
    logger.info(f"[上传] 文件已保存: {safe_filename} ({len(content)/1024/1024:.1f}MB)")
    
    # ===== 创建报告记录 =====
    service = ProfessionalReportService()
    report = service.create_report(
        db=db,
        user_id=current_user["id"],
        file_path=file_path,
        company_name=file.filename.replace('.pdf', '').replace('_', ' ')
    )
    
    # ===== 启动后台处理 =====
    background_tasks.add_task(process_report_v2_background, report.id, file_path)
    
    logger.info(f"[✅ 已接收] Report ID: {report.id} | 后台处理中...")
    
    return ReportUploadResponse(
        id=report.id,
        company_name=report.company_name,
        status="processing",
        message="✅ 文件已接收，正在进行AI智能分析（预计30秒-2分钟）",
        upload_time=report.upload_time.isoformat() if report.upload_time else "",
        estimated_time="30秒-2分钟"
    )


@router.get("/{report_id}", response_model=ReportDetailResponse)
async def get_report_detail_v2(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(lambda: {"id": "test_user"})
):
    """
    获取报告详情 - 包含完整结构化数据
    """
    service = ProfessionalReportService()
    report = service.get_report(db, report_id)
    
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    return ReportDetailResponse(
        success=True,
        data=report.to_dict(),
        message=""
    )


@router.get("/", response_model=dict)
async def list_reports_v2(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(lambda: {"id": "test_user"})
):
    """
    获取用户的报告列表（支持历史查看）
    """
    service = ProfessionalReportService()
    reports = service.get_user_reports(db, current_user["id"])
    
    # 分页
    total = len(reports)
    reports_page = reports[offset:offset+limit]
    
    return {
        "success": True,
        "total": total,
        "items": [r.to_dict() for r in reports_page],
        "message": f"共{total}份报告"
    }


@router.post("/compare", response_model=dict)
async def compare_reports_v2(
    request: CompareRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(lambda: {"id": "test_user"})
):
    """
    📊 历史对比功能 - 对比多期财报
    
    用法：
    POST /api/reports/compare
    {
      "report_ids": ["uuid1", "uuid2"]
    }
    
    返回：关键指标变化趋势、同比分析、改善建议
    """
    if len(request.report_ids) < 2:
        raise HTTPException(status_code=400, detail="至少需要2个报告ID进行对比")
    
    result = ProfessionalReportService.compare_reports_v2(db, request.report_ids)
    
    return {
        "success": "error" not in result,
        **result
    }


@router.delete("/{report_id}", response_model=dict)
async def delete_report_v2(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(lambda: {"id": "test_user"})
):
    """删除报告"""
    service = ProfessionalReportService()
    success = service.delete_report(db, report_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="报告不存在或删除失败")
    
    return {"success": True, "message": "报告已删除"}
