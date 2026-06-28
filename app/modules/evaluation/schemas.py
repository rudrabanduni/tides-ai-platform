from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class Observation(BaseModel):
    observation_id: str = Field(..., description="Unique Observation ID (e.g. OBS-FOUNDER-001)")
    observation: str = Field(..., description="Statement of the domain observation")
    claim_ids: list[str] = Field(default_factory=list, description="IDs of claims supporting this observation")
    evidence_ids: list[str] = Field(default_factory=list, description="IDs of evidence supporting this observation")
    reasoning: str = Field(..., description="Analytical logic linking evidence to the observation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Certainty score (0.0 to 1.0)")


class Risk(BaseModel):
    id: str = Field(..., description="Unique Risk ID (e.g. RISK-FOUNDER-001)")
    description: str = Field(..., description="Description of the risk factor")
    severity: str = Field(..., description="Priority mapping: Critical, High, Medium, or Low")
    likelihood: str = Field(..., description="Probability of occurrence: High, Medium, or Low")
    impact: str = Field(..., description="Impact on viability if occurred: High, Medium, or Low")
    mitigation: str = Field(..., description="Suggested mitigation plan")
    supporting_observations: list[str] = Field(default_factory=list, description="IDs of observations supporting this risk")
    supporting_claims: list[str] = Field(default_factory=list, description="IDs of claims supporting this risk")
    supporting_evidence: list[str] = Field(default_factory=list, description="IDs of evidence supporting this risk")
    risk_id: str | None = Field(None, description="Detailed risk identifier")
    category: str | None = Field(None, description="Risk category: technical, execution, market, competition, financial, regulatory, ip")
    confidence: float | None = Field(None, description="Confidence score for the risk finding")
    reasoning: str | None = Field(None, description="Analysis reasoning explaining the risk")


class Question(BaseModel):
    id: str = Field(..., description="Unique Question ID (e.g. QST-FOUNDER-001)")
    question: str = Field(..., description="The query text directed to the founder")
    purpose: str = Field(..., description="Reason why this question is being asked")
    priority: str = Field(..., description="Priority level: High, Medium, or Low")
    expected_evidence: str = Field(..., description="Proof or document expected to verify the answer")
    blocking: bool = Field(default=False, description="Whether this blocks incubation or funding")
    generated_by: str = Field(..., description="Expert domain that generated this question")


class ConfidenceHierarchy(BaseModel):
    finding_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the correctness of observations")
    evidence_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the availability/reliability of source evidence")
    reasoning_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the logical soundness of deductions")
    overall_domain_confidence: float = Field(..., ge=0.0, le=1.0, description="Composite domain confidence score")


class MissingEvidence(BaseModel):
    description: str = Field(..., description="Description of what document or context is missing")
    importance: str = Field(..., description="Importance level: High, Medium, or Low")
    expected_document: str | None = Field(None, description="Filename or category of expected document")


class AgentAssessment(BaseModel):
    domain: str = Field(..., description="Evaluation domain key (e.g. 'founder')")
    summary: str = Field(..., description="Brief high-level overview of domain assessment")
    observations: list[Observation] = Field(default_factory=list, description="Structured expert observations")
    risks: list[Risk] = Field(default_factory=list, description="Categorized risks")
    questions: list[Question] = Field(default_factory=list, description="Follow-up questions")
    confidence: ConfidenceHierarchy = Field(..., description="Detailed confidence hierarchy")
    reasoning: str = Field(..., description="Overall domain analysis reasoning block")
    missing_evidence: list[MissingEvidence] = Field(default_factory=list, description="List of missing evidence requests")
    
    # Explicit VC assessment fields:
    executive_conclusion: str = Field("", description="Executive conclusion statement")
    strengths: list[str] = Field(default_factory=list, description="List of domain strengths")
    weaknesses: list[str] = Field(default_factory=list, description="List of domain weaknesses")
    investment_implication: str = Field("", description="Investment implication statement")
    missing_information: list[str] = Field(default_factory=list, description="List of missing information items")
    follow_up_questions: list[str] = Field(default_factory=list, description="List of follow-up questions")
    
    # Metadata fields
    prompt_name: str = Field(..., description="Name of the prompt used")
    prompt_version: str = Field(..., description="Version of the prompt used")
    prompt_hash: str = Field(..., description="SHA-256 hash of the prompt text used")
    agent_version: str = Field(..., description="Version of the expert agent used")
    generated_at: datetime = Field(..., description="Timestamp when the assessment was generated")
