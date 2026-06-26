import json
from typing import Any
from app.modules.explainability.explanation_models import ExplanationNode


class ExplanationSerializer:
    """Handles round-trip JSON serialization and audit-trail exports of ExplanationNodes."""

    @staticmethod
    def to_json(explanation: ExplanationNode) -> str:
        """Serialize an ExplanationNode to a formatted JSON string."""
        if hasattr(explanation, "model_dump_json"):
            return explanation.model_dump_json(indent=2)
        if hasattr(explanation, "json"):
            return explanation.json(indent=2)
        return json.dumps(explanation, default=str)

    @staticmethod
    def from_json(json_str: str) -> ExplanationNode:
        """Deserialize a JSON string back into an ExplanationNode."""
        if hasattr(ExplanationNode, "model_validate_json"):
            return ExplanationNode.model_validate_json(json_str)
        if hasattr(ExplanationNode, "parse_raw"):
            return ExplanationNode.parse_raw(json_str)
        
        data = json.loads(json_str)
        return ExplanationNode(**data)

    @staticmethod
    def to_audit_format(explanation: ExplanationNode) -> dict[str, Any]:
        """Generate an audit-ready, flat tracing dictionary representing the explanation chain."""
        return {
            "explanation_id": explanation.explanation_id,
            "target_id": explanation.target_id,
            "target_type": explanation.target_type,
            "summary": explanation.summary,
            "confidence": explanation.confidence,
            "reasoning": explanation.reasoning,
            "generated_at": explanation.generated_at.isoformat() if hasattr(explanation.generated_at, "isoformat") else str(explanation.generated_at),
            "traced_nodes_count": explanation.metadata.get("traced_nodes_count", 0),
            "documents_referenced": [doc.get("document_name", doc.get("document_id", "unnamed")) for doc in explanation.lineage.documents],
            "evidence_snippets": [ev.get("excerpt", "No snippet") for ev in explanation.lineage.evidence],
            "claims": [claim.get("claim_text", "No text") for claim in explanation.lineage.claims],
            "observations": [obs.get("observation", "No observation") for obs in explanation.lineage.observations],
            "assessments": [
                {
                    "expert": asm.get("expert_name", "UnknownExpert"),
                    "agent_version": asm.get("agent_version", "1.0.0"),
                    "prompt_version": asm.get("prompt_version", "1.0.0"),
                }
                for asm in explanation.lineage.assessments
            ],
            "metadata": explanation.metadata,
        }
