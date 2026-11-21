"""domain_schemas.py - Canonical Typed Output Contracts for 6 Evaluation Domains and Final Supervisory Review.

Follows the LaunchIndex Startup Incubation Application specification.
Fully compatible with existing AgentAssessment conventions and ObservationGraph.
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field

from app.modules.evaluation.schemas import (
    Observation,
    Risk,
    Question,
    ConfidenceHierarchy,
    MissingEvidence,
)


class VerificationStatus(str, enum.Enum):
    """Factual verification grade for individual startup claims and criteria."""
    VERIFIED_DOCUMENTED = "VERIFIED_DOCUMENTED"        # Backed by explicit deck/document evidence
    SELF_REPORTED_ONLY = "SELF_REPORTED_ONLY"          # Claimed by founder without supporting documentation
    PLAUSIBLE_ESTIMATE = "PLAUSIBLE_ESTIMATE"          # Logical inference backed by industry benchmarks
    CONTRADICTED = "CONTRADICTED"                      # Contradicts another slide, document, or established fact
    UNSUPPORTED_ASSUMPTION = "UNSUPPORTED_ASSUMPTION"  # Unsubstantiated leap of faith or critical gap
    MISSING_INFORMATION = "MISSING_INFORMATION"        # Required criterion omitted from application
    NOT_APPLICABLE = "NOT_APPLICABLE"                  # Conditional field legitimately not applicable (e.g. TRL 2 prototype)


class CriterionAssessment(BaseModel):
    """Detailed evaluation of an individual canonical criterion."""
    criterion_id: str = Field(..., description="Canonical ID (e.g. 'PS-01', 'MO-07', 'FT-01')")
    criterion_name: str = Field(..., description="Human-readable title of criterion")
    extracted_startup_response: Optional[str] = Field(None, description="Raw data extracted from application")
    assessment_narrative: str = Field(..., description="Specialist analysis and domain reasoning")
    evidence_ids: list[str] = Field(default_factory=list, description="Linked StartupEvidence IDs")
    source_locations: list[str] = Field(default_factory=list, description="Slide or document sections (e.g. 'Slide 3')")
    verification_status: VerificationStatus = Field(..., description="Factual verification grade")
    strengths: list[str] = Field(default_factory=list, description="Specific identified strengths")
    weaknesses: list[str] = Field(default_factory=list, description="Deficiencies, gaps, or concerns")
    risks: list[str] = Field(default_factory=list, description="Identified risk factors")
    contradictions: list[str] = Field(default_factory=list, description="Contradictions with other criteria")
    confidence_score: float = Field(0.85, ge=0.0, le=1.0, description="Evaluator certainty score (0.0 to 1.0)")
    confidence_limitations: Optional[str] = Field(None, description="Limitations affecting certainty")
    score: Optional[float] = Field(None, description="Optional numerical score when authorized rubric is present")
    external_research_sources: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Verifiable external research evidence items corroborating or providing context for this criterion"
    )


class CompactCriterionResult(BaseModel):
    """Compact structured result for an individual canonical criterion.

    Strictly limits output tokens while maintaining factual verification grade,
    provenance traceability, and criterion-level rationale without echoing full texts.
    """
    criterion_id: str = Field(..., description="Canonical criterion ID (e.g. 'PS-01', 'MO-02')")
    verification_status: VerificationStatus = Field(..., description="Factual verification grade")
    score: Optional[float] = Field(None, ge=0.0, le=10.0, description="Score 0.0-10.0 only where supported by rubric/evidence; otherwise null")
    evidence_ids: list[str] = Field(default_factory=list, description="Relevant evidence IDs (e.g. ['EV-01', 'EV-03'])")
    rationale: str = Field(..., description="Ultra-concise rationale (at most 14 words)")


class BatchCriterionResult(CompactCriterionResult):
    """Extended compact criterion result used by criterion-batched domain execution."""
    missing_information: Optional[str] = Field(None, description="Specific missing data needed if partially verified or missing")
    source_provenance: Optional[str] = Field(None, description="Brief source document/page/sheet reference if known")


class DomainCriterionBatchOutput(BaseModel):
    """Compact structured response model for a single criterion batch call.

    Emits ONLY the criteria explicitly assigned to the batch so output tokens
    stay tightly bounded and truncation-safe under conservative token caps.
    """
    domain: str = Field(..., description="Canonical domain key (e.g. 'problem_solution')")
    batch_index: int = Field(..., ge=0, description="Zero-based batch index within the domain")
    criteria: list[BatchCriterionResult | CompactCriterionResult] = Field(..., description="Evaluations ONLY for criteria assigned to this batch")


class CompactDomainRisk(BaseModel):
    """Compact risk item."""
    id: str = Field(..., description="Risk ID (e.g. 'RISK-PS-01')")
    severity: str = Field("High", description="'Critical', 'High', 'Medium', or 'Low'")
    description: str = Field(..., description="Concise risk description (max 15 words)")
    mitigation: Optional[str] = Field(None, description="Concise mitigation plan (max 12 words)")


class CompactDomainAssessment(BaseModel):
    """Compact structured response model for domain specialist AI completion.

    Guarantees all owned criteria are evaluated with zero duplicated essays or repeated
    evidence blobs, fitting strictly within the 1800-token output budget.
    """
    domain: str = Field(..., description="Canonical domain key (e.g. 'problem_solution')")
    domain_conclusion: str = Field(..., description="Short domain conclusion (at most 25 words)")
    criteria: list[CompactCriterionResult] = Field(..., description="Evaluations for all canonical criteria owned by this domain")
    strengths: list[str] = Field(default_factory=list, max_length=2, description="At most 2 non-duplicative domain strengths")
    risks: list[CompactDomainRisk] = Field(default_factory=list, max_length=2, description="At most 2 material risks")
    information_requests: list[str] = Field(default_factory=list, max_length=3, description="At most 3 priority diligence requests")
    unknowns: list[str] = Field(default_factory=list, max_length=3, description="Short explicit unknowns or gaps; never invent facts")
    contradictions: list[str] = Field(default_factory=list, max_length=2, description="Short explicit discrepancies where material")
    confidence_score: float = Field(0.85, ge=0.0, le=1.0, description="Evaluator certainty score (0.0 to 1.0)")


class DomainAssessmentReport(BaseModel):
    """Standard typed assessment report generated by each of the 6 Canonical Domain Specialists.

    Maintains 100% duck-type compatibility with legacy AgentAssessment so existing
    ObservationGraphBuilder and reporting engines accept it natively.
    """
    domain: str = Field(..., description="Canonical domain key (e.g. 'problem_solution', 'founder_team')")
    domain_key: str = Field(..., description="Canonical domain key identical to domain")
    domain_title: str = Field(..., description="Official domain display name")
    evaluation_id: Optional[str] = Field(None, description="Evaluation run ID sharing cost ledger")
    startup_id: Optional[str] = Field(None, description="Target startup UUID")
    
    # Canonical 87-criteria mapping
    criteria_evaluated: list[str] = Field(default_factory=list, description="List of criteria IDs owned by this domain")
    criteria_evaluations: dict[str, CriterionAssessment] = Field(
        default_factory=dict, description="Map of criterion_id to CriterionAssessment"
    )

    # Narrative summaries
    summary: str = Field(..., description="High-level overview (duck-type compatible with AgentAssessment)")
    executive_summary: str = Field("", description="2-3 paragraph domain synthesis")
    executive_conclusion: str = Field("", description="Executive conclusion statement")
    reasoning: str = Field("", description="Detailed analytical breakdown")
    investment_implication: str = Field("", description="Deal structuring or milestone implication")

    # Structured graph-compatible items
    observations: list[Observation] = Field(default_factory=list, description="Structured graph observation nodes")
    risks: list[Risk] = Field(default_factory=list, description="Categorized risks")
    questions: list[Question] = Field(default_factory=list, description="Follow-up questions")
    missing_evidence: list[MissingEvidence] = Field(default_factory=list, description="Missing evidence records")
    confidence: ConfidenceHierarchy = Field(
        default_factory=lambda: ConfidenceHierarchy(
            finding_confidence=0.85,
            evidence_confidence=0.85,
            reasoning_confidence=0.85,
            overall_domain_confidence=0.85,
        )
    )

    # VC-specific finding collections
    strengths: list[str] = Field(default_factory=list, description="List of domain strengths")
    weaknesses: list[str] = Field(default_factory=list, description="List of domain weaknesses")
    unsupported_claims: list[str] = Field(default_factory=list, description="Claims lacking sufficient documentation")
    contradictions: list[str] = Field(default_factory=list, description="Inconsistencies detected within domain")
    missing_information: list[str] = Field(default_factory=list, description="Missing information items")
    follow_up_questions: list[str] = Field(default_factory=list, description="Flat list of queries for founders")

    # Confidence & Limitations
    composite_domain_confidence: float = Field(0.85, ge=0.0, le=1.0)
    confidence_limitations: Optional[str] = Field(None, description="Explicit caveats (e.g. external research unavailable)")

    # Traceability & Telemetry
    prompt_name: str = Field("Canonical Domain Specialist Prompt", description="Name of prompt template")
    prompt_version: str = Field("2.0.0", description="Prompt version")
    prompt_hash: str = Field("canonical-sha256-v2", description="Hash of prompt template")
    agent_version: str = Field("2.0.0", description="Agent implementation version")
    model_used: Optional[str] = Field(None, description="Model resolved for execution")
    cost_usd: float = Field(0.0, description="Cost reconciled for this domain call")
    external_research_evidence: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Verifiable external research evidence items retaining canonical URL, title, snippet, and provenance"
    )
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TargetedRecheckRequest(BaseModel):
    """Specification for a targeted re-check triggered by the Supervisory Reviewer."""
    recheck_id: str = Field(..., description="Unique re-check transaction ID")
    domain_key: str = Field(..., description="Target specialist domain key")
    criterion_ids: list[str] = Field(default_factory=list, description="Criteria requiring targeted re-evaluation")
    challenge_reason: str = Field(..., description="Why the original finding is challenged (e.g. contradiction, lack of proof)")
    contradiction_details: Optional[str] = Field(None, description="Conflicting evidence or cross-domain discrepancy")
    specific_question: str = Field(..., description="Focused question the specialist must re-evaluate")


class TargetedRecheckResult(BaseModel):
    """Result of a targeted re-check execution by an individual specialist."""
    recheck_id: str = Field(...)
    domain_key: str = Field(...)
    criterion_id: str = Field(...)
    original_verification_status: str = Field(...)
    updated_verification_status: str = Field(...)
    original_finding_summary: str = Field(...)
    updated_finding_summary: str = Field(...)
    recheck_reasoning: str = Field(...)
    evidence_confirmed: bool = Field(False)
    unresolved_disagreement: bool = Field(False)
    cost_usd: float = Field(0.0)
    rechecked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CrossDomainContradiction(BaseModel):
    """Structured record of a cross-domain discrepancy identified during supervisory review."""
    contradiction_id: str = Field(...)
    domain_a: str = Field(..., description="First domain involved")
    criterion_a: str = Field(..., description="Criterion in first domain")
    claim_a_summary: str = Field(..., description="Statement from first domain")
    domain_b: str = Field(..., description="Second domain involved")
    criterion_b: str = Field(..., description="Criterion in second domain")
    claim_b_summary: str = Field(..., description="Statement from second domain")
    nature_of_conflict: str = Field(..., description="e.g. 'REVENUE_TIMING', 'TEAM_CAPABILITY', 'MARKET_OVERLAP'")
    resolution_status: str = Field("UNRESOLVED", description="'RESOLVED', 'PRESERVED_DISAGREEMENT', 'UNRESOLVED'")
    resolution_rationale: Optional[str] = Field(None)


class SupervisoryReviewOutput(BaseModel):
    """Compact structured response model for the metered Supervisory AI Reviewer gateway completion.

    Synthesizes the 6 domain assessments, highlights critical cross-domain contradictions,
    records missing domains, formulates a qualified recommendation, and lists top diligence questions.
    """
    executive_summary: str = Field(..., description="Synthesized due diligence executive summary (max 60 words)")
    recommendation_rationale: str = Field(..., description="Qualified institutional rationale for decision (max 60 words)")
    overall_recommendation: str = Field("CONDITIONAL", description="'INCUBATE', 'DEFER', 'REJECT', or 'CONDITIONAL'")
    identified_contradictions: list[str] = Field(default_factory=list, description="At most 3 critical cross-domain contradictions")
    missing_domains: list[str] = Field(default_factory=list, description="Domains with missing information or assessment failures")
    priority_diligence_questions: list[str] = Field(default_factory=list, description="Top 3-5 prioritized questions for the incubation committee")
    incubation_conditions: list[str] = Field(default_factory=list, description="At most 3 prerequisite conditions before capital disbursement")
    recommended_tranches: list[dict[str, Any]] = Field(default_factory=list, description="Optional tranche structures (institutional defaults used if empty)")
    investment_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    confidence_score: float = Field(0.88, ge=0.0, le=1.0)


class FinalReviewAssessment(BaseModel):
    """Unified Due Diligence Report produced by the Final Supervisory AI Reviewer.

    Critically synthesizes all 6 specialist reports, tracks re-checks, records
    unresolved disagreements, and produces the definitive incubation recommendation.
    """
    report_id: str = Field(..., description="Unique report identifier (e.g. 'DD-TIDES-2026-XXXX')")
    evaluation_id: str = Field(..., description="Shared evaluation budget ledger ID")
    startup_id: str = Field(..., description="Target startup UUID")
    startup_name: str = Field(...)
    sector: str = Field(...)
    stage: str = Field(...)
    
    # Executive & Strategic Synthesis
    executive_summary: str = Field(..., description="Holistic venture assessment synthesized across all domains")
    recommendation_rationale: str = Field(..., description="Detailed institutional rationale for decision")
    overall_recommendation: str = Field(..., description="'INCUBATE', 'DEFER', 'REJECT', or 'CONDITIONAL'")
    incubation_conditions: list[str] = Field(default_factory=list, description="Prerequisite milestones before onboarding")
    recommended_tranches: list[dict[str, Any]] = Field(default_factory=list, description="Milestone-based resource/grant tranches")

    # Domain Reports
    domain_reports: dict[str, DomainAssessmentReport] = Field(
        default_factory=dict, description="Complete 6 canonical domain assessment reports"
    )

    # Cross-Domain Verification Findings
    cross_domain_findings: list[str] = Field(default_factory=list, description="Cross-cutting observations linking domains")
    identified_contradictions: list[CrossDomainContradiction] = Field(default_factory=list)
    material_unsupported_claims: list[str] = Field(default_factory=list, description="Claims challenged for lack of backing proof")
    composite_risk_matrix: list[dict[str, Any]] = Field(default_factory=list, description="Cross-domain risks ranked by severity")
    unresolved_questions: list[str] = Field(default_factory=list, description="Crucial questions left unanswered for committee")

    # Reviewer Audit Trail
    rechecks_triggered: list[TargetedRecheckResult] = Field(default_factory=list, description="Audit log of targeted re-checks executed")
    unresolved_disagreements: list[str] = Field(default_factory=list, description="Explicitly preserved expert disagreements")
    external_research_sources: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Aggregate external independent research evidence citations referenced in due diligence"
    )

    # Scoring & Confidence
    investment_score: Optional[float] = Field(None, ge=0.0, le=100.0, description="Deterministic baseline investment score")
    confidence_score: float = Field(0.85, ge=0.0, le=1.0, description="Overall supervisory confidence score")
    reviewer_agent_version: str = Field("2.0.0")

    # Observability & Budget Telemetry
    cost_summary: dict[str, Any] = Field(default_factory=dict, description="Full cost ledger breakdown")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
