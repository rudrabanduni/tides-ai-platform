from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class LineageTrace(BaseModel):
    observations: list[dict[str, Any]] = Field(default_factory=list, description="Observations in the lineage path")
    claims: list[dict[str, Any]] = Field(default_factory=list, description="Claims in the lineage path")
    evidence: list[dict[str, Any]] = Field(default_factory=list, description="Evidence in the lineage path")
    documents: list[dict[str, Any]] = Field(default_factory=list, description="Documents in the lineage path")
    assessments: list[dict[str, Any]] = Field(default_factory=list, description="Assessments in the lineage path")


class ExplanationNode(BaseModel):
    explanation_id: str = Field(..., description="Unique explanation ID")
    target_type: str = Field(..., description="Target node type being explained")
    target_id: str = Field(..., description="Target node ID being explained")
    summary: str = Field(..., description="Short summary of the explanation")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0")
    reasoning: str = Field(..., description="Detailed reasoning text")
    generated_at: datetime = Field(..., default_factory=datetime.utcnow, description="Timestamp of generation")
    lineage: LineageTrace = Field(default_factory=LineageTrace, description="Full traceability lineage path")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context metadata")
