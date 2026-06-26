from typing import Any
from app.modules.evaluation.expert_agent import ExpertAgent
from app.modules.evaluation.schemas import AgentAssessment
from app.modules.evaluation.events import (
    publish_ip_assessment_started,
    publish_ip_assessment_completed,
    publish_ip_assessment_failed
)
from app.modules.evaluation.registry.metadata import ExpertMetadata


class IPExpert(ExpertAgent):
    """Domain expert analyzing intellectual property, patents, trademarks, licensing, assignments, and freedom-to-operate."""

    metadata = ExpertMetadata(
        expert_name="IPExpert",
        domain="ip",
        version="1.0.0",
        description="Domain expert analyzing intellectual property, patents, trademarks, licensing, assignments, and freedom-to-operate.",
        supported_claims=[
            "patents", "patent_applications", "patent_numbers",
            "design_registrations", "trademarks", "copyrights",
            "licensing_agreements", "ownership_declarations",
            "proprietary_technology_claims", "trade_secret_claims",
            "research_publications", "technology_disclosures",
            "defensibility_claims"
        ],
        supported_evidence_types=["patent", "business_plan", "pitch_deck", "licensing_agreement"],
        prompt_name="ip",
        prompt_version="1.0.0",
        agent_version="1.0.0",
        enabled=True,
        tags=["ip", "patent", "licensing", "defensibility"]
    )

    def get_domain_key(self) -> str:
        return "ip"

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
        """Evaluates the startup IP status, emitting IP lifecycle events."""
        startup_id = str(profile.startup_id) if (profile and hasattr(profile, "startup_id")) else "unknown"
        publish_ip_assessment_started(startup_id)
        
        try:
            assessment = super().evaluate(profile, claims, evidence, conflicts, metadata)
            publish_ip_assessment_completed(startup_id, {"assessment_id": str(getattr(profile, "id", "unknown"))})
            return assessment
        except Exception as e:
            publish_ip_assessment_failed(startup_id, str(e))
            raise e
