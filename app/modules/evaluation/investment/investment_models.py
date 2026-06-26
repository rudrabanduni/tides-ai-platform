from enum import Enum
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from app.modules.evaluation.graph.graph_models import GraphNode, NodeType


class InvestmentRecommendation(str, Enum):
    STRONG_INVEST = "STRONG_INVEST"
    INVEST = "INVEST"
    WATCHLIST = "WATCHLIST"
    REVIEW = "REVIEW"
    DO_NOT_INVEST = "DO_NOT_INVEST"


class InvestmentMetrics(BaseModel):
    weighted_score: float
    evidence_strength: float
    graph_confidence: float
    resolved_conflicts: int
    unresolved_conflicts: int
    duplicate_observations: int
    overall_consensus: float
    document_coverage: float


class InvestmentAssessment(GraphNode):
    assessment_id: str
    generated_at: str
    graph_version: str = "1.0.0"
    recommendation: InvestmentRecommendation
    confidence: float
    investment_score: float
    readiness_score: float
    risk_score: float
    technology_score: float
    market_score: float
    founder_score: float
    financial_score: float
    competition_score: float
    ip_score: float
    executive_summary: str
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    major_risks: List[str] = Field(default_factory=list)
    investment_rationale: str
    missing_information: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    traceability: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
