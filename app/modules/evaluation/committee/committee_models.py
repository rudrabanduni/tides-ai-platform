from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from app.modules.evaluation.graph.graph_models import GraphNode, NodeType


class Recommendation(str, Enum):
    INCUBATE = "INCUBATE"
    INCUBATE_AFTER_DD = "INCUBATE_AFTER_DD"
    PILOT_FIRST = "PILOT_FIRST"
    SEEK_MORE_INFORMATION = "SEEK_MORE_INFORMATION"
    DEFER = "DEFER"
    REJECT = "REJECT"


class Priority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class DueDiligenceCategory(str, Enum):
    FINANCIAL_DD = "Financial DD"
    LEGAL_DD = "Legal DD"
    TECHNICAL_DD = "Technical DD"
    MARKET_DD = "Market DD"
    IP_DD = "IP DD"
    FOUNDER_DD = "Founder DD"


class DueDiligenceItem(BaseModel):
    category: DueDiligenceCategory
    status: str = "PENDING"
    reason: str
    blocking: bool
    documents_required: List[str] = Field(default_factory=list)


class InvestmentCommitteeDecision(GraphNode):
    node_type: NodeType = NodeType.DECISION
    decision_id: str
    startup_id: str
    startup_name: str
    portfolio_rank: int
    recommendation: Recommendation
    decision_confidence: float
    decision_reasoning: str
    investment_priority: Priority
    incubation_priority: Priority
    grant_priority: Priority
    pilot_priority: Priority
    review_window: str
    committee_notes: str
    blocking_risks: List[str] = Field(default_factory=list)
    required_due_diligence: List[DueDiligenceItem] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    graph_hash: str
    portfolio_hash: str
    executive_summary_id: str
    investment_assessment_id: str
    generated_at: str
    engine_version: str = "1.0.0"


from datetime import datetime
from typing import Dict, Any

class CommitteeDecision(BaseModel):
    decision_id: str
    startup_id: str
    startup_name: str
    created_at: datetime
    committee_version: str = "1.0.0"
    overall_confidence: float
    overall_reasoning: str
    executive_summary: str
    graph_hash: str
    workflow_reference: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CommitteeFinding(BaseModel):
    finding_id: str
    title: str
    description: str
    domains: List[str]
    supporting_observations: List[str] = Field(default_factory=list)
    supporting_claims: List[str] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    confidence: float


class CommitteeConcern(BaseModel):
    concern_id: str
    description: str
    affected_domains: List[str]
    severity: str  # e.g., CRITICAL, HIGH, MEDIUM, LOW
    confidence: float
    linked_risks: List[str] = Field(default_factory=list)
    linked_questions: List[str] = Field(default_factory=list)


class CommitteeConsensus(BaseModel):
    agreement_level: float
    corroborated_findings: List[Dict[str, Any]] = Field(default_factory=list)
    contradictions: List[Dict[str, Any]] = Field(default_factory=list)
    unresolved_conflicts: List[str] = Field(default_factory=list)
    cross_domain_dependencies: List[Dict[str, Any]] = Field(default_factory=list)


class CommitteeRecommendation(BaseModel):
    recommendation_id: str
    recommendation: str  # Ready for Incubation, Promising but Requires Clarification, Requires Significant Validation, Not Ready Yet
    justification: str
    required_followups: List[str] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    priority: str  # e.g., CRITICAL, HIGH, MEDIUM, LOW


class CommitteeReport(BaseModel):
    decision: CommitteeDecision
    findings: List[CommitteeFinding]
    concerns: List[CommitteeConcern]
    consensus: CommitteeConsensus
    recommendations: CommitteeRecommendation
    traceability: Dict[str, Any] = Field(default_factory=dict)

