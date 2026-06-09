from pydantic import BaseModel, Field


class IntakeRowError(BaseModel):
    row_number: int
    startup_name: str | None = None
    field: str | None = None
    message: str


class IntakeUploadSummary(BaseModel):
    total_rows: int = Field(ge=0)
    successful_rows: int = Field(ge=0)
    failed_rows: int = Field(ge=0)
    errors: list[IntakeRowError] = Field(default_factory=list)
