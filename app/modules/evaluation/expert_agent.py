from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from app.services.ai.gateway import AIGateway, create_ai_gateway
from app.services.ai.schemas import AICompletionRequest
from app.modules.evaluation.schemas import AgentAssessment
from app.modules.evaluation.prompts.manager import PromptManager


class ExpertAgent(ABC):
    """Abstract base class representing a domain expert agent in the incubation committee."""

    def __init__(self, gateway: AIGateway | None = None) -> None:
        self.gateway = gateway or create_ai_gateway()

    @abstractmethod
    def validate_inputs(
        self,
        profile: Any,
        claims: list[Any],
        evidence: list[Any],
        conflicts: list[Any],
        metadata: dict[str, Any]
    ) -> bool:
        """Verifies that the minimum required claims and context exist for this expert domain."""
        pass

    @abstractmethod
    def get_domain_key(self) -> str:
        """Returns the domain key for this expert (e.g. 'founder', 'product')."""
        pass

    @abstractmethod
    def get_agent_version(self) -> str:
        """Returns the expert agent version string (e.g. '1.0.0')."""
        pass

    def parse_response(self, response: Any) -> AgentAssessment:
        """Casts raw completion result into a structured AgentAssessment."""
        if hasattr(response, "data") and isinstance(response.data, AgentAssessment):
            return response.data
        raise ValueError("AI Gateway response data is not a valid AgentAssessment instance")

    def generate_reasoning(
        self,
        profile: Any,
        claims: list[Any],
        evidence: list[Any],
        conflicts: list[Any],
        metadata: dict[str, Any]
    ) -> str:
        """Serializes validated claims, evidence logs, and conflict histories into structured prompt context."""
        context_lines = []
        profile_id = profile.id if hasattr(profile, "id") else "N/A"
        startup_id = profile.startup_id if hasattr(profile, "startup_id") else "N/A"
        
        context_lines.append(f"Profile ID: {profile_id}")
        context_lines.append(f"Startup ID: {startup_id}")
        
        context_lines.append("\n--- VALIDATED CLAIMS ---")
        for claim in claims:
            fk = claim.field.field_key if (hasattr(claim, "field") and claim.field) else "unknown"
            val = (
                claim.value_string 
                if claim.value_string is not None else (
                    claim.value_number 
                    if claim.value_number is not None else (
                        claim.value_boolean 
                        if claim.value_boolean is not None else (
                            claim.value_json 
                            if claim.value_json is not None else claim.value_date
                        )
                    )
                )
            )
            context_lines.append(
                f"Claim ID: {claim.id} | Field: {fk} | Value: {val} | Confidence: {claim.confidence_score} | Validation: {claim.validation_status}"
            )
            
        context_lines.append("\n--- SUPPORTING EVIDENCE ---")
        for ev in evidence:
            context_lines.append(
                f"Evidence ID: {ev.id} | Claim ID: {ev.claim_id} | Snippet: '{ev.evidence_snippet}' | Section: {ev.section_name} | Page: {ev.page_number}"
            )
            
        context_lines.append("\n--- DATA CONFLICT HISTORY ---")
        for conflict in conflicts:
            fk = conflict.field.field_key if (hasattr(conflict, "field") and conflict.field) else "unknown"
            context_lines.append(
                f"Conflict ID: {conflict.id} | Field: {fk} | Resolved: {conflict.resolved} | Reason: {conflict.resolution_reason}"
            )
            
        return "\n".join(context_lines)

    def evaluate(
        self,
        profile: Any,
        claims: list[Any],
        evidence: list[Any],
        conflicts: list[Any],
        metadata: dict[str, Any]
    ) -> AgentAssessment:
        """Orchestrates validation, prompt loading, gateway completion, and structured validation."""
        from app.modules.evaluation.context.context_registry import context_registry
        from app.modules.evaluation.context.context_builder import ContextBuilder

        try:
            context_filter = context_registry.get_filter(self.__class__)
            context = ContextBuilder.build_context(
                profile=profile,
                all_claims=claims,
                all_evidence=evidence,
                all_conflicts=conflicts,
                metadata=metadata,
                context_filter=context_filter
            )
            claims_to_use = context.claims
            evidence_to_use = context.evidence
            conflicts_to_use = context.conflicts
        except Exception:
            claims_to_use = claims
            evidence_to_use = evidence
            conflicts_to_use = conflicts

        self.validate_inputs(profile, claims_to_use, evidence_to_use, conflicts_to_use, metadata)
        
        # Load prompt template exclusively from PromptManager
        prompt_data = PromptManager.load_prompt(domain=self.get_domain_key(), version="latest")
        system_prompt = prompt_data["system_prompt"]
        context_str = self.generate_reasoning(profile, claims_to_use, evidence_to_use, conflicts_to_use, metadata)
        user_prompt = prompt_data["user_prompt"].format(context=context_str)
        
        request = AICompletionRequest(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            prompt_version=prompt_data["prompt_version"],
            metadata={"domain": "evaluation"}
        )
        
        res = self.gateway.complete_json(request, response_model=AgentAssessment)
        draft = self.parse_response(res)

        # Populate explicit metadata / traceability fields
        draft.domain = self.get_domain_key()
        draft.prompt_name = prompt_data["prompt_name"]
        draft.prompt_version = prompt_data["prompt_version"]
        draft.prompt_hash = prompt_data["prompt_hash"]
        draft.agent_version = self.get_agent_version()
        draft.generated_at = datetime.utcnow()

        # Validate Draft AgentAssessment using the read-only AssessmentValidator
        from app.modules.evaluation.validation.assessment_validator import AssessmentValidator
        validated = AssessmentValidator.validate(draft, claims_to_use, evidence_to_use)
        return validated
