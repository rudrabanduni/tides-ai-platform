from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.modules.evaluation.graph.graph_models import GraphNode, NodeType


class ExecutiveFinding(BaseModel):
    finding_id: str
    finding_type: str  # "OBSERVATION" or "RISK"
    description: str
    confidence: float
    supporting_observations: List[str] = Field(default_factory=list)


class ExecutiveSummary(BaseModel):
    overview: str
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    threats: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)


class ExecutiveMetrics(BaseModel):
    total_documents: int = 0
    total_claims: int = 0
    total_evidence: int = 0
    total_observations: int = 0
    total_assessments: int = 0
    total_correlations: int = 0
    total_conflicts: int = 0
    total_resolutions: int = 0
    graph_confidence: float = 0.0


class ExecutiveAssessment(GraphNode):
    assessment_id: str
    generated_at: str
    graph_version: str = "1.0.0"
    summary: ExecutiveSummary
    key_observations: List[ExecutiveFinding] = Field(default_factory=list)
    major_risks: List[ExecutiveFinding] = Field(default_factory=list)
    unresolved_conflicts: List[str] = Field(default_factory=list)
    evidence_strength: float = 0.0
    confidence: float = 0.0
    readiness_level: str = "TRL-1"
    traceability: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
