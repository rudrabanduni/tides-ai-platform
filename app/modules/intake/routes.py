from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import ValidationError
from app.db.session import get_db
from app.modules.auth.dependencies import EvaluatorUser
from app.modules.intake.schemas import IntakeUploadSummary
from app.modules.intake.service import ExcelIntakeService

router = APIRouter(prefix="/intake", tags=["Startup Intake"])


@router.post(
    "/upload-applications",
    response_model=IntakeUploadSummary,
    status_code=status.HTTP_200_OK,
    summary="Upload Accubate startup applications Excel export",
    description=(
        "Accepts a .xlsx file with one startup application per row. "
        "Valid rows create StartupApplication, Founder, StartupProfile, "
        "and StartupProfileVersion records. Invalid rows are reported without stopping the import."
    ),
)
async def upload_applications(
    current_user: EvaluatorUser,
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(
        ...,
        description=(
            ".xlsx file with columns: Startup Name, Founder Name, Founder Email, "
            "Problem Statement, Solution, Target Market, Startup Stage"
        ),
    ),
) -> IntakeUploadSummary:
    settings = get_settings()
    raw_name = (file.filename or "").replace("\\", "/").split("/")[-1]
    safe_filename = Path(raw_name).name
    if not safe_filename.lower().endswith(".xlsx"):
        raise ValidationError("Only .xlsx files are supported")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    chunks: list[bytes] = []
    total_size = 0
    while chunk := await file.read(1024 * 1024):
        total_size += len(chunk)
        if total_size > max_bytes:
            raise ValidationError(f"Uploaded Excel file exceeds {settings.max_upload_size_mb} MB limit")
        chunks.append(chunk)
    content = b"".join(chunks)
    if not content:
        raise ValidationError("Uploaded Excel file is empty")

    return ExcelIntakeService(db).import_applications_from_xlsx(
        filename=safe_filename,
        content=content,
        actor_id=current_user.id,
    )
