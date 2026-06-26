from app.modules.evaluation.correlation.correlation_models import CorrelationNode
from app.modules.evaluation.correlation.correlation_engine import CorrelationEngine
from app.modules.evaluation.correlation.correlation_validator import CorrelationValidator
from app.modules.evaluation.correlation.correlation_queries import (
    get_correlation, get_observation_correlations, get_corroborations,
    get_contradictions, get_dependencies
)
from app.modules.evaluation.correlation.correlation_serializer import to_json, from_json, export_traceability
