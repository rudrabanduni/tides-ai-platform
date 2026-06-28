from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Observation(BaseModel):
    observation_id: str = Field(..., description="Unique Observation ID (e.g. OBS-FOUNDER-001)")
    observation: str = Field(..., description="Statement of the domain observation")
    claim_ids: List[str] = Field(default_factory=list, description="IDs of claims supporting this observation")
    evidence_ids: List[str] = Field(default_factory=list, description="IDs of evidence supporting this observation")
    reasoning: str = Field(..., description="Analytical logic linking evidence to the observation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Certainty score (0.0 to 1.0)")

class Evidence(BaseModel):
    evidence_id: str = Field(..., description="Unique Evidence ID (e.g. EVID-FOUNDER-001)")
    source_claim_id: str = Field(..., description="ID of claim linked to this evidence")
    evidence_snippet: str = Field(..., description="Exact quote/snippet from source document")
    source_document: str = Field(..., description="Document identifier/name")

class ExecutionMetadata(BaseModel):
    model: str = Field(..., description="LLM Model used")
    provider: str = Field(..., description="LLM Provider name")
    latency_ms: float = Field(..., description="Response latency in ms")
    retries: int = Field(..., description="Number of execution retries")
    token_count: int = Field(..., description="Total token consumption")
    prompt_version: str = Field(..., description="Template version identifier")
    timestamp: str = Field(..., description="ISO 8601 generation timestamp")
    execution_status: str = Field(..., description="Status e.g. success, failure")

class AgentAssessment(BaseModel):
    domain: str = Field(..., description="Evaluation domain key e.g. founder, product, market")
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Composite score for the domain")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Domain certainty confidence score")
    summary: str = Field(..., description="Narrative domain summary text")
    strengths: List[str] = Field(default_factory=list, description="Core strengths noted")
    weaknesses: List[str] = Field(default_factory=list, description="Core weaknesses identified")
    opportunities: List[str] = Field(default_factory=list, description="Core growth/market opportunities")
    risks: List[str] = Field(default_factory=list, description="Domain risk factors")
    recommendations: List[str] = Field(default_factory=list, description="Expert advice/action items")
    observations: List[Observation] = Field(default_factory=list, description="Granular analytical observations")
    supporting_evidence: List[Evidence] = Field(default_factory=list, description="Traceable source evidence citations")
    open_questions: List[str] = Field(default_factory=list, description="Remaining validation query items")
    execution_metadata: ExecutionMetadata = Field(..., description="Process metadata block")
