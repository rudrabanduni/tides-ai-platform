from enum import Enum
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    DOCUMENT = "DOCUMENT"
    EVIDENCE = "EVIDENCE"
    CLAIM = "CLAIM"
    OBSERVATION = "OBSERVATION"
    ASSESSMENT = "ASSESSMENT"
    CONFLICT = "CONFLICT"
    RISK = "RISK"
    QUESTION = "QUESTION"
    CORRELATION = "CORRELATION"
    RESOLUTION = "RESOLUTION"
    EXECUTIVE = "EXECUTIVE"
    INVESTMENT = "INVESTMENT"
    REPORT = "REPORT"
    DECISION = "DECISION"




class GraphNode(BaseModel):
    node_id: str = Field(..., description="Unique node ID")
    node_type: NodeType = Field(..., description="Type of graph node")


class DocumentNode(GraphNode):
    document_id: str
    document_name: str
    document_type: str
    uploaded_at: datetime | str


class EvidenceNode(GraphNode):
    evidence_id: str
    excerpt: str
    location: str
    confidence: float


class ClaimNode(GraphNode):
    claim_id: str
    claim_text: str


class ObservationNode(GraphNode):
    observation_id: str
    domain: str
    observation: str
    confidence: float
    consensus_status: str = "independent"


class AssessmentNode(GraphNode):
    assessment_id: str
    domain: str
    expert_name: str
    agent_version: str
    prompt_version: str
    confidence: float
    generated_at: datetime | str


class ConflictNode(GraphNode):
    conflict_id: str
    description: str
    conflict_type: str
    confidence: float
    created_at: datetime | str


class RiskNode(GraphNode):
    risk_id: str
    category: str
    description: str
    confidence: float
    reasoning: str


class QuestionNode(GraphNode):
    question_id: str
    question: str
    purpose: str


class Edge(BaseModel):
    source_id: str
    source_type: NodeType
    target_id: str
    target_type: NodeType
    relationship: str
    state: str | None = None


class GraphStatistics(BaseModel):
    document_count: int = 0
    evidence_count: int = 0
    claim_count: int = 0
    observation_count: int = 0
    assessment_count: int = 0
    conflict_count: int = 0
    risk_count: int = 0
    question_count: int = 0
    correlation_count: int = 0
    edge_count: int = 0
    resolution_count: int = 0
    resolved_conflicts: int = 0
    unresolved_conflicts: int = 0


class ObservationGraph:
    """Central knowledge graph connecting startup evaluation facts and expert assessments."""

    def __init__(self) -> None:
        self.graph_id: str = ""
        self.graph_version: str = "1.0.0"
        self.graph_hash: str = ""
        self.created_at: datetime | str = ""

        # Nodes
        self.documents: dict[str, DocumentNode] = {}
        self.evidence: dict[str, EvidenceNode] = {}
        self.claims: dict[str, ClaimNode] = {}
        self.observations: dict[str, ObservationNode] = {}
        self.assessments: dict[str, AssessmentNode] = {}
        self.conflicts: dict[str, ConflictNode] = {}
        self.risks: dict[str, RiskNode] = {}
        self.questions: dict[str, QuestionNode] = {}
        self.correlations: dict[str, Any] = {}
        self.resolutions: dict[str, Any] = {}
        self.resolution_edges: list[Any] = []

        # Edges
        self.edges: list[Edge] = []
        self.out_edges: dict[str, list[Edge]] = {}
        self.in_edges: dict[str, list[Edge]] = {}

        # Indexes for O(1) domain/category lookups
        self.observations_by_domain: dict[str, list[str]] = {}
        self.assessments_by_domain: dict[str, list[str]] = {}
        self.risks_by_category: dict[str, list[str]] = {}
        self.correlations_by_observation: dict[str, list[Any]] = {}
        self.resolutions_by_conflict: dict[str, list[str]] = {}
        self.resolutions_by_observation: dict[str, list[str]] = {}

        # Statistics
        self.graph_stats: GraphStatistics = GraphStatistics()

        # Cache for O(1) lineage traversals
        self.provenance_cache: dict[str, dict[str, Any]] = {}

        # Executive Intelligence Layer fields
        self.executive_assessment: Optional[Any] = None
        self.executive_indexes: dict[str, Any] = {}
        self.executive_statistics: dict[str, Any] = {}

        # Investment Decision Engine fields
        self.investment_assessment: Optional[Any] = None
        self.investment_indexes: dict[str, Any] = {}
        self.investment_statistics: dict[str, Any] = {}

        # Due Diligence Report fields
        self.report: Optional[Any] = None
        self.report_indexes: dict[str, Any] = {}
        self.report_statistics: dict[str, Any] = {}

        # Portfolio Intelligence fields
        self.portfolio_entry: Optional[Any] = None
        self.portfolio_statistics: Optional[Any] = None
        self.startup_id: str = ""
        self.startup_name: str = ""
        self.category: str = ""
        self.committee_decision: Optional[Any] = None



    def get_node(self, node_id: str) -> GraphNode | None:
        """O(1) retrieval of any node in the graph by ID."""
        if node_id in self.documents:
            return self.documents[node_id]
        if node_id in self.evidence:
            return self.evidence[node_id]
        if node_id in self.claims:
            return self.claims[node_id]
        if node_id in self.observations:
            return self.observations[node_id]
        if node_id in self.assessments:
            return self.assessments[node_id]
        if node_id in self.conflicts:
            return self.conflicts[node_id]
        if node_id in self.risks:
            return self.risks[node_id]
        if node_id in self.questions:
            return self.questions[node_id]
        if node_id in self.correlations:
            return self.correlations[node_id]
        if node_id in self.resolutions:
            return self.resolutions[node_id]
        if self.executive_assessment and self.executive_assessment.node_id == node_id:
            return self.executive_assessment
        if self.investment_assessment and self.investment_assessment.node_id == node_id:
            return self.investment_assessment
        if self.report and self.report.node_id == node_id:
            return self.report
        if self.committee_decision and self.committee_decision.node_id == node_id:
            return self.committee_decision
        return None
