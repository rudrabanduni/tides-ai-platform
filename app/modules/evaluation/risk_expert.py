from typing import Any
from app.modules.evaluation.expert_agent import ExpertAgent
from app.modules.evaluation.schemas import AgentAssessment
from app.modules.evaluation.events import (
    publish_risk_assessment_started,
    publish_risk_assessment_completed,
    publish_risk_assessment_failed
)
from app.modules.evaluation.registry.metadata import ExpertMetadata


class RiskExpert(ExpertAgent):
    """Domain expert identifying, classifying, linking, and validating risks across all startup domains."""

    metadata = ExpertMetadata(
        expert_name="RiskExpert",
        domain="risk",
        version="1.0.0",
        description="Domain expert identifying, classifying, linking, and validating risks across all startup domains.",
        supported_claims=[
            "technical_risk_claims", "market_risk_claims", "regulatory_risk_claims",
            "execution_risk_claims", "founder_dependency_risks",
            "customer_concentration_risks", "supply_chain_risks",
            "financial_runway_risks", "evidence_gaps", "unresolved_conflicts"
        ],
        supported_evidence_types=[
            "pitch_deck", "business_plan", "financial_statement", "patent",
            "licensing_agreement", "customer_feedback", "regulatory_document"
        ],
        prompt_name="risk",
        prompt_version="1.0.0",
        agent_version="1.0.0",
        enabled=True,
        tags=["risk", "technical", "market", "regulatory", "execution", "financial"]
    )

    def get_domain_key(self) -> str:
        return "risk"

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
        """Evaluates startup risks, emitting Risk assessment events."""
        startup_id = str(profile.startup_id) if (profile and hasattr(profile, "startup_id")) else "unknown"
        publish_risk_assessment_started(startup_id)
        
        try:
            assessment = super().evaluate(profile, claims, evidence, conflicts, metadata)
            publish_risk_assessment_completed(startup_id, {"assessment_id": str(getattr(profile, "id", "unknown"))})
            return assessment
        except Exception as e:
            publish_risk_assessment_failed(startup_id, str(e))
            raise e
