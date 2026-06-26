from typing import Any
from app.modules.evaluation.expert_agent import ExpertAgent
from app.modules.evaluation.schemas import AgentAssessment
from app.modules.evaluation.events import (
    publish_trl_assessment_started,
    publish_trl_assessment_completed,
    publish_trl_assessment_failed
)
from app.modules.evaluation.registry.metadata import ExpertMetadata


class TRLExpert(ExpertAgent):
    """Domain expert analyzing technology readiness levels (TRL 1-9), prototype maturity, laboratory/field validation, engineering/manufacturing readiness, scalability, and validation gaps."""

    metadata = ExpertMetadata(
        expert_name="TRLExpert",
        domain="trl",
        version="1.0.0",
        description="Domain expert analyzing technology readiness levels (TRL 1-9), prototype maturity, laboratory/field validation, engineering/manufacturing readiness, scalability, and validation gaps.",
        supported_claims=[
            "claimed_trl", "trl_evidence", "prototype_maturity",
            "laboratory_validation", "field_validation", "pilot_deployments",
            "production_readiness", "engineering_risks", "manufacturing_readiness",
            "technology_scalability", "technology_dependencies", "validation_gaps"
        ],
        supported_evidence_types=["patent", "research_paper", "pitch_deck", "business_plan"],
        prompt_name="trl",
        prompt_version="1.0.0",
        agent_version="1.0.0",
        enabled=True,
        tags=["trl", "technology", "prototype", "readiness"]
    )

    def get_domain_key(self) -> str:
        return "trl"

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
        """Evaluates the startup TRL profile, emitting TRL lifecycle events."""
        startup_id = str(profile.startup_id) if (profile and hasattr(profile, "startup_id")) else "unknown"
        publish_trl_assessment_started(startup_id)
        
        try:
            assessment = super().evaluate(profile, claims, evidence, conflicts, metadata)
            publish_trl_assessment_completed(startup_id, {"assessment_id": str(getattr(profile, "id", "unknown"))})
            return assessment
        except Exception as e:
            publish_trl_assessment_failed(startup_id, str(e))
            raise e
