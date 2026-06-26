from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator


# --- Base Extracted Field Types with Confidence and Reasoning ---
class ExtractedField(BaseModel):
    why_extracted: str | None = Field(default=None, description="Detailed explanation of why this field was extracted.")
    supporting_evidence: str | None = Field(default=None, description="Exact quotes or evidence snippet supporting the extraction.")
    document_section: str | None = Field(default=None, description="Section or page numbers in the document.")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0.")
    confidence_reason: str | None = Field(default=None, description="Rationale for the assigned confidence score.")


class ExtractedString(ExtractedField):
    value: str | None = Field(default=None, description="The extracted string value.")


class ExtractedInt(ExtractedField):
    value: int | None = Field(default=None, description="The extracted integer value.")


class ExtractedFloat(ExtractedField):
    value: float | None = Field(default=None, description="The extracted float value.")


class ExtractedBoolean(ExtractedField):
    value: bool | None = Field(default=None, description="The extracted boolean value.")


# --- Sub-models for different domains of evaluation ---
class FounderInfo(BaseModel):
    founder_names: ExtractedString = Field(default_factory=ExtractedString)
    leadership_experience: ExtractedString = Field(default_factory=ExtractedString)
    domain_expertise: ExtractedString = Field(default_factory=ExtractedString)
    commitment_level: ExtractedString = Field(default_factory=ExtractedString)


class ProductInfo(BaseModel):
    description: ExtractedString = Field(default_factory=ExtractedString)
    problem_solved: ExtractedString = Field(default_factory=ExtractedString)
    solution_value_prop: ExtractedString = Field(default_factory=ExtractedString)
    customers: ExtractedString = Field(default_factory=ExtractedString)
    business_model: ExtractedString = Field(default_factory=ExtractedString)


class MarketInfo(BaseModel):
    target_market: ExtractedString = Field(default_factory=ExtractedString)
    market_size: ExtractedString = Field(default_factory=ExtractedString)
    competitors: ExtractedString = Field(default_factory=ExtractedString)
    competition_analysis: ExtractedString = Field(default_factory=ExtractedString)


class FinancialInfo(BaseModel):
    revenue_model: ExtractedString = Field(default_factory=ExtractedString)
    funding_received: ExtractedFloat = Field(default_factory=ExtractedFloat)
    current_revenue: ExtractedFloat = Field(default_factory=ExtractedFloat)
    financial_metrics: ExtractedString = Field(default_factory=ExtractedString)


class TechnologyInfo(BaseModel):
    description: ExtractedString = Field(default_factory=ExtractedString)
    trl_level: ExtractedInt = Field(default_factory=ExtractedInt)
    ip_status: ExtractedString = Field(default_factory=ExtractedString)

    @field_validator("trl_level")
    @classmethod
    def validate_trl_level(cls, v: ExtractedInt) -> ExtractedInt:
        if v.value is not None and not (1 <= v.value <= 9):
            raise ValueError("TRL level must be an integer between 1 and 9")
        return v


class RiskInfo(BaseModel):
    major_risks: list[ExtractedString] = Field(default_factory=list)


class ExtractionMetadata(BaseModel):
    document_id: str | None = None
    startup_id: str | None = None
    extraction_timestamp: str | None = None


# --- Combined Document Extraction Output Schema ---
class DocumentExtraction(BaseModel):
    founder: FounderInfo = Field(default_factory=FounderInfo)
    product: ProductInfo = Field(default_factory=ProductInfo)
    market: MarketInfo = Field(default_factory=MarketInfo)
    financial: FinancialInfo = Field(default_factory=FinancialInfo)
    technology: TechnologyInfo = Field(default_factory=TechnologyInfo)
    risk: RiskInfo = Field(default_factory=RiskInfo)
    metadata: ExtractionMetadata = Field(default_factory=ExtractionMetadata)
