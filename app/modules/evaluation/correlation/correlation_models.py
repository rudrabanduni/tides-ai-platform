from datetime import datetime
from app.modules.evaluation.graph.graph_models import GraphNode, NodeType


class CorrelationNode(GraphNode):
    correlation_id: str
    correlation_type: str  # CORROBORATES, CONTRADICTS, DEPENDS_ON, SUPPORTS, WEAKENS, DUPLICATES
    description: str
    confidence: float
    created_at: datetime | str
