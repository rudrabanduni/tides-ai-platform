from datetime import datetime
from typing import List, Optional, Any
from pydantic import Field, BaseModel
from app.modules.evaluation.graph.graph_models import GraphNode, NodeType


class ResolutionNode(GraphNode):
    resolution_id: str
    conflict_id: str
    resolution_type: str  # FACTUAL, NUMERICAL, TEMPORAL, SOURCE_PRIORITY, CONSENSUS, INSUFFICIENT_EVIDENCE
    preferred_observation_id: Optional[str] = None
    confidence: float
    reasoning: str
    supporting_claims: List[str] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    supporting_assessments: List[str] = Field(default_factory=list)
    created_at: Any


class ResolutionEdge(BaseModel):
    source_id: str
    source_type: NodeType
    target_id: str
    target_type: NodeType
    relationship: str  # RESOLVES, PREFERS, SUPPORTED_BY
