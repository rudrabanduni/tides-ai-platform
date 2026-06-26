from typing import Any
from app.modules.evaluation.expert_agent import ExpertAgent
from app.modules.evaluation.schemas import AgentAssessment
from app.modules.evaluation.events import (
    publish_founder_assessment_started,
    publish_founder_assessment_completed,
    publish_founder_assessment_failed
)
from app.modules.evaluation.registry.metadata import ExpertMetadata


class FounderExpert(ExpertAgent):
    """Domain expert analyzing founding team capabilities, domain expertise, commitment levels, and execution track record."""

    metadata = ExpertMetadata(
        expert_name="FounderExpert",
        domain="founder",
        version="1.0.0",
        description="Domain expert analyzing founding team capabilities, domain expertise, commitment levels, and execution track record.",
        supported_claims=["founder_names", "leadership_experience", "commitment_level"],
        supported_evidence_types=["cv", "incorporation", "linkedin"],
        prompt_name="founder",
        prompt_version="1.0.0",
        agent_version="1.0.0",
        enabled=True,
        tags=["founder", "team", "incubation"]
    )

    def get_domain_key(self) -> str:
        return "founder"

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
        """Evaluates the startup founder profile, emitting Founder lifecycle events."""
        startup_id = str(profile.startup_id) if (profile and hasattr(profile, "startup_id")) else "unknown"
        publish_founder_assessment_started(startup_id)
        
        try:
            assessment = super().evaluate(profile, claims, evidence, conflicts, metadata)
            publish_founder_assessment_completed(startup_id, {"assessment_id": str(getattr(profile, "id", "unknown"))})
            return assessment
        except Exception as e:
            publish_founder_assessment_failed(startup_id, str(e))
            raise e
