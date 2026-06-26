from typing import Any
from app.modules.evaluation.context.context_filters import BaseContextFilter, FounderContextFilter, CompetitionContextFilter, IPContextFilter, RiskContextFilter
from app.modules.evaluation.founder_expert import FounderExpert
from app.modules.evaluation.competition_expert import CompetitionExpert
from app.modules.evaluation.ip_expert import IPExpert
from app.modules.evaluation.risk_expert import RiskExpert


class ContextRegistry:
    """Registry coordinating mappings between evaluation expert agents and their relevant context filters."""

    def __init__(self) -> None:
        self._mappings: dict[str, BaseContextFilter] = {}

    def register(self, expert: Any, filter_instance: BaseContextFilter) -> None:
        """Register a context filter for a specific expert name or class type."""
        name = expert if isinstance(expert, str) else expert.__name__
        self._mappings[name.lower()] = filter_instance

    def get_filter(self, expert: Any) -> BaseContextFilter:
        """Retrieves the context filter registered for the given expert name or class."""
        name = expert if isinstance(expert, str) else expert.__name__
        expert_key = name.lower()
        if expert_key not in self._mappings:
            raise ValueError(f"No context filter registered for expert '{name}'")
        return self._mappings[expert_key]


# Global context registry instance
context_registry = ContextRegistry()

# Register reference mapping
context_registry.register(FounderExpert, FounderContextFilter())
context_registry.register(CompetitionExpert, CompetitionContextFilter())
context_registry.register(IPExpert, IPContextFilter())
context_registry.register(RiskExpert, RiskContextFilter())

