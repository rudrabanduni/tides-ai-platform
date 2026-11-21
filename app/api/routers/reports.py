import re
from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response, Path

from app.api.responses import make_response
from app.api.dependencies import get_report_service, ReportService
from app.modules.auth.dependencies import ReadOnlyUser

router = APIRouter(tags=["Reports"])

ReportLookupId = Annotated[str, Path(pattern=r"^[A-Za-z0-9_-]{1,80}$")]


@router.get("/reports/{startup_id}")
def get_report(
    request: Request,
    current_user: ReadOnlyUser,
    startup_id: ReportLookupId,
    report_service: ReportService = Depends(get_report_service)
):
    report = report_service.get_report(startup_id)
    # Serialize to dictionary using model_dump
    report_data = report.model_dump() if hasattr(report, "model_dump") else report.__dict__
    return make_response(request, data=report_data, message="Due diligence report retrieved successfully")


@router.get("/reports/{startup_id}/download")
def download_pdf(
    request: Request,
    current_user: ReadOnlyUser,
    startup_id: ReportLookupId,
    report_service: ReportService = Depends(get_report_service)
):
    pdf_bytes = report_service.download_pdf(startup_id)
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "", startup_id) or "report"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="Due_Diligence_Report_{safe_id}.pdf"'
        }
    )


@router.get("/reports/{startup_id}/markdown")
def get_markdown(
    request: Request,
    current_user: ReadOnlyUser,
    startup_id: ReportLookupId,
    report_service: ReportService = Depends(get_report_service)
):
    md_content = report_service.get_markdown(startup_id)
    return make_response(request, data=md_content, message="Markdown report retrieved successfully")
