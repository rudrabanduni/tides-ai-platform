from typing import Any
from app.modules.evaluation.expert_agent import ExpertAgent
from app.modules.evaluation.schemas import AgentAssessment
from app.modules.evaluation.events import (
    publish_financial_assessment_started,
    publish_financial_assessment_completed,
    publish_financial_assessment_failed
)
from app.modules.evaluation.registry.metadata import ExpertMetadata


class FinancialExpert(ExpertAgent):
    """Domain expert analyzing revenue model, consistency, ARR, MRR, burn rate, runway, unit economics, gross margins, CAC, funding, and capital efficiency."""

    metadata = ExpertMetadata(
        expert_name="FinancialExpert",
        domain="financial",
        version="1.0.0",
        description="Domain expert analyzing revenue model, consistency, ARR, MRR, burn rate, runway, unit economics, gross margins, CAC, funding, and capital efficiency.",
        supported_claims=[
            "revenue_model", "revenue_consistency", "current_revenue",
            "mrr_arr", "burn_rate", "runway", "cost_structure",
            "unit_economics", "gross_margins", "cac_economics",
            "funding_history", "grants_received", "capital_efficiency",
            "financial_reporting_maturity", "financial_readiness"
        ],
        supported_evidence_types=["financial_statement", "pitch_deck", "business_plan"],
        prompt_name="financial",
        prompt_version="1.0.0",
        agent_version="1.0.0",
        enabled=True,
        tags=["financial", "runway", "economics", "burn-rate"]
    )

    def get_domain_key(self) -> str:
        return "financial"

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
        """Evaluates the startup financial profile, emitting Financial lifecycle events."""
        startup_id = str(profile.startup_id) if (profile and hasattr(profile, "startup_id")) else "unknown"
        publish_financial_assessment_started(startup_id)
        
        try:
            assessment = super().evaluate(profile, claims, evidence, conflicts, metadata)
            publish_financial_assessment_completed(startup_id, {"assessment_id": str(getattr(profile, "id", "unknown"))})
            return assessment
        except Exception as e:
            publish_financial_assessment_failed(startup_id, str(e))
            raise e
