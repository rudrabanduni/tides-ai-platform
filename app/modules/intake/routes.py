from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
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
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(
        ...,
        description=(
            ".xlsx file with columns: Startup Name, Founder Name, Founder Email, "
            "Problem Statement, Solution, Target Market, Startup Stage"
        ),
    ),
) -> IntakeUploadSummary:
    content = await file.read()
    # TODO: Restore role-based authentication after Swagger OAuth2 is fixed.
    return ExcelIntakeService(db).import_applications_from_xlsx(
        filename=file.filename or "applications.xlsx",
        content=content,
        actor_id=None,
    )
