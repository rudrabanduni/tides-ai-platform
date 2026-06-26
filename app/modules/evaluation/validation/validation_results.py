from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    """Encapsulates the complete summary, errors, warnings, and ontology reports of an assessment validation."""

    is_valid: bool = Field(..., description="True if no blocking validation errors were found")
    errors: list[str] = Field(default_factory=list, description="List of blocking validation errors")
    warnings: list[str] = Field(default_factory=list, description="List of non-blocking warnings")
    broken_references: list[str] = Field(default_factory=list, description="Details of broken internal or external references")
    missing_evidence: list[str] = Field(default_factory=list, description="Details of missing evidence/claims traces")
    duplicate_objects: list[str] = Field(default_factory=list, description="Details of duplicate IDs or values")
    confidence_issues: list[str] = Field(default_factory=list, description="Details of out-of-bounds confidence values")
    ontology_violations: list[str] = Field(default_factory=list, description="Violations against TAES core specifications")
