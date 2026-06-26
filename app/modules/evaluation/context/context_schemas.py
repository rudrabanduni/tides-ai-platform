from typing import Any
from pydantic import BaseModel, Field


class EvaluationContext(BaseModel):
    """Container schema for structured evaluation context delivered to a domain expert."""

    model_config = {"arbitrary_types_allowed": True}

    claims: list[Any] = Field(default_factory=list, description="Filtered domain-specific claims")
    evidence: list[Any] = Field(default_factory=list, description="Preserved supporting evidence citations")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Startup and document metadata")
    conflicts: list[Any] = Field(default_factory=list, description="Filtered data conflicts")
    missing_information: list[str] = Field(default_factory=list, description="Missing domain keys identified")
    context_statistics: dict[str, Any] = Field(default_factory=dict, description="Statistics like counts of items")
    source_counts: dict[str, Any] = Field(default_factory=dict, description="Frequency of document source types")
    confidence_summary: dict[str, Any] = Field(default_factory=dict, description="Summarized confidence parameters")
