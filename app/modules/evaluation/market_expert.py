from typing import Any
from app.modules.evaluation.expert_agent import ExpertAgent
from app.modules.evaluation.schemas import AgentAssessment
from app.modules.evaluation.events import (
    publish_market_assessment_started,
    publish_market_assessment_completed,
    publish_market_assessment_failed
)
from app.modules.evaluation.registry.metadata import ExpertMetadata


class MarketExpert(ExpertAgent):
    """Domain expert analyzing TAM, SAM, SOM, market growth, timing, customer segments, demand signals, trends, expansion, barriers, acquisition, and validation."""

    metadata = ExpertMetadata(
        expert_name="MarketExpert",
        domain="market",
        version="1.0.0",
        description="Domain expert analyzing TAM, SAM, SOM, market growth, timing, customer segments, demand signals, trends, expansion, barriers, acquisition, and validation.",
        supported_claims=[
            "tam", "sam", "som", "market_growth", "market_timing",
            "customer_segments", "demand_signals", "industry_trends",
            "geographic_expansion", "market_barriers",
            "acquisition_assumptions", "market_validation"
        ],
        supported_evidence_types=["pitch_deck", "business_plan", "market_research", "financial_statement"],
        prompt_name="market",
        prompt_version="1.0.0",
        agent_version="1.0.0",
        enabled=True,
        tags=["market", "opportunity", "segments", "growth"]
    )

    def get_domain_key(self) -> str:
        return "market"

    def get_agent_version(self) -> str:
        return "1.0.0"

    def validate_inputs(
        self,
        profile: Any,
        claims: list[Any],
        evidence: list[Any],
        conflicts: list[Any],
        metadata: dict[str, Any]
    ) -> bool:
        """Verifies that the profile is not None and matches basic validation rules."""
        if not profile:
            raise ValueError("Startup Intelligence Profile is missing or empty")
        
        # Ensure we have claims list (can be empty but must be a list)
        if claims is None:
            raise ValueError("Claims context must be provided as a list")
            
        return True

    def evaluate(
        self,
        profile: Any,
        claims: list[Any],
        evidence: list[Any],
        conflicts: list[Any],
        metadata: dict[str, Any]
    ) -> AgentAssessment:
        """Evaluates the startup market profile, emitting Market lifecycle events."""
        startup_id = str(profile.startup_id) if (profile and hasattr(profile, "startup_id")) else "unknown"
        publish_market_assessment_started(startup_id)
        
        try:
            assessment = super().evaluate(profile, claims, evidence, conflicts, metadata)
            publish_market_assessment_completed(startup_id, {"assessment_id": str(getattr(profile, "id", "unknown"))})
            return assessment
        except Exception as e:
            publish_market_assessment_failed(startup_id, str(e))
            raise e
