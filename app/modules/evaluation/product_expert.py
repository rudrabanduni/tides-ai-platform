from typing import Any
from app.modules.evaluation.expert_agent import ExpertAgent
from app.modules.evaluation.schemas import AgentAssessment
from app.modules.evaluation.events import (
    publish_product_assessment_started,
    publish_product_assessment_completed,
    publish_product_assessment_failed
)
from app.modules.evaluation.registry.metadata import ExpertMetadata


class ProductExpert(ExpertAgent):
    """Domain expert analyzing product clarity, problem severity, solution quality, innovation, maturity, validation, and adoption."""

    metadata = ExpertMetadata(
        expert_name="ProductExpert",
        domain="product",
        version="1.0.0",
        description="Domain expert analyzing product clarity, problem severity, solution quality, innovation, maturity, validation, and adoption.",
        supported_claims=[
            "problem_clarity", "problem_severity", "solution_quality",
            "product_differentiation", "innovation", "product_maturity",
            "customer_validation", "product_market_fit", "adoption_signals",
            "product_scalability"
        ],
        supported_evidence_types=["pitch_deck", "product_demo", "customer_feedback"],
        prompt_name="product",
        prompt_version="1.0.0",
        agent_version="1.0.0",
        enabled=True,
        tags=["product", "solution", "market-fit"]
    )

    def get_domain_key(self) -> str:
        return "product"

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
        """Evaluates the startup product profile, emitting Product lifecycle events."""
        startup_id = str(profile.startup_id) if (profile and hasattr(profile, "startup_id")) else "unknown"
        publish_product_assessment_started(startup_id)
        
        try:
            assessment = super().evaluate(profile, claims, evidence, conflicts, metadata)
            publish_product_assessment_completed(startup_id, {"assessment_id": str(getattr(profile, "id", "unknown"))})
            return assessment
        except Exception as e:
            publish_product_assessment_failed(startup_id, str(e))
            raise e
