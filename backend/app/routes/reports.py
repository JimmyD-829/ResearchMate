from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from ..schemas.report import FinancialReportResponse, FinancialReportUpdate
from ..services.report_service import ReportService
from ..database import get_db
import os
import uuid

router = APIRouter(prefix="/api/reports", tags=["reports"])

import tempfile
import os

UPLOAD_DIR = tempfile.gettempdir()

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

@router.post("/", response_model=FinancialReportResponse, status_code=status.HTTP_201_CREATED)
async def upload_report(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(lambda: {"id": "test_user"})
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="请选择文件")

    file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
    if file_ext not in ['pdf', 'xlsx', 'xls', 'csv']:
        raise HTTPException(status_code=400, detail="仅支持 PDF、Excel、CSV 格式文件")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件过大（最大支持50MB），当前文件大小: {len(content) / 1024 / 1024:.1f}MB")

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="文件为空，请重新选择")

    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}.{file_ext}")

        with open(file_path, "wb") as f:
            f.write(content)

        report = ReportService.create_report(db, current_user["id"], file_path, file.filename)

        parsed_data = ReportService.parse_report(report)

        if "error" in parsed_data:
            report.status = "failed"
            db.commit()
            error_msg = parsed_data["error"]
            if "扫描件" in error_msg or "OCR" in error_msg:
                raise HTTPException(status_code=400, detail="该PDF为扫描件（图片），暂不支持OCR识别。请使用文字版PDF或Excel格式的财报。")
            elif "无法提取" in error_msg:
                raise HTTPException(status_code=400, detail="无法解析该文件。请确保文件未加密且包含可提取的文字内容。")
            else:
                raise HTTPException(status_code=400, detail=f"解析失败: {error_msg}")

        update_data = FinancialReportUpdate(
            company_name=parsed_data.get("company_name"),
            stock_code=parsed_data.get("stock_code"),
            report_period=parsed_data.get("report_period"),
            revenue=parsed_data.get("revenue"),
            net_profit=parsed_data.get("net_profit"),
            cash_flow=parsed_data.get("cash_flow"),
            debt_ratio=parsed_data.get("debt_ratio"),
            gross_margin=parsed_data.get("gross_margin")
        )

        ReportService.update_report(db, report.id, update_data)

        summary = ReportService.generate_summary(parsed_data)
        ReportService.update_report(db, report.id, FinancialReportUpdate(ai_summary=summary))

        report.status = "success"
        db.commit()
        db.refresh(report)

        return report

    except HTTPException:
        raise
    except Exception as e:
        if 'report' in locals() and report:
            report.status = "failed"
            db.commit()
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")

@router.get("/", response_model=list[FinancialReportResponse])
def get_reports(
    db: Session = Depends(get_db),
    current_user: dict = Depends(lambda: {"id": "test_user"})
):
    return ReportService.get_user_reports(db, current_user["id"])

@router.get("/{report_id}", response_model=FinancialReportResponse)
def get_report(report_id: str, db: Session = Depends(get_db)):
    report = ReportService.get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.put("/{report_id}", response_model=FinancialReportResponse)
def update_report(
    report_id: str,
    update_data: FinancialReportUpdate,
    db: Session = Depends(get_db)
):
    report = ReportService.update_report(db, report_id, update_data)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(report_id: str, db: Session = Depends(get_db)):
    success = ReportService.delete_report(db, report_id)
    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
