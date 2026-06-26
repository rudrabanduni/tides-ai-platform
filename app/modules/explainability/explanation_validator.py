from typing import Any
from app.modules.evaluation.graph.graph_models import ObservationGraph
from app.modules.explainability.explanation_models import ExplanationNode


class ExplanationValidationError(ValueError):
    """Exception raised when an explanation fails validation."""
    pass


class ExplanationValidator:
    """Validates the structure, integrity, references, and lineage of ExplanationNodes."""

    @staticmethod
    def validate_explanation(explanation: ExplanationNode, graph: ObservationGraph) -> dict[str, list[str]]:
        errors: list[str] = []
        warnings: list[str] = []

        # 1. Validate confidence bounds
        if not (0.0 <= explanation.confidence <= 1.0):
            errors.append(f"Confidence score {explanation.confidence} is out of bounds [0.0, 1.0]")

        # 2. Check orphan explanation (does the target exist in the graph/metadata?)
        target_exists = False
        target_id = explanation.target_id
        target_type = explanation.target_type.upper()

        if graph.get_node(target_id) is not None:
            target_exists = True
        elif target_id in graph.correlations or target_id in graph.resolutions:
            target_exists = True
        elif target_type in ("PORTFOLIO", "PORTFOLIO_RANK", "INVESTMENT", "INVESTMENT_DECISION", "EXECUTIVE", "EXECUTIVE_SUMMARY", "DECISION", "COMMITTEE_DECISION"):
            # Check domain elements
            if target_type in ("PORTFOLIO", "PORTFOLIO_RANK") and graph.portfolio_entry is not None:
                target_exists = True
            elif target_type in ("INVESTMENT", "INVESTMENT_DECISION") and graph.investment_assessment is not None:
                target_exists = True
            elif target_type in ("EXECUTIVE", "EXECUTIVE_SUMMARY") and graph.executive_assessment is not None:
                target_exists = True
            elif target_type in ("DECISION", "COMMITTEE_DECISION") and graph.committee_decision is not None:
                target_exists = True

        if not target_exists:
            errors.append(f"Orphan Explanation: target_id '{target_id}' of type '{target_type}' not found in graph")

        # 3. Check lineage integrity (no missing lineage for graph node targets)
        if target_type in ("OBSERVATION", "RISK", "QUESTION", "CONFLICT"):
            lineage = explanation.lineage
            if not lineage.documents and not lineage.assessments:
                errors.append(f"Missing Lineage: Explanation has no documents or assessments in its lineage path")

        # 4. Check broken references (do the nodes in lineage actually exist in the graph?)
        for obs in explanation.lineage.observations:
            obs_id = obs.get("node_id")
            if obs_id not in graph.observations:
                errors.append(f"Broken Reference: Lineage observation '{obs_id}' does not exist in graph")

        for claim in explanation.lineage.claims:
            claim_id = claim.get("node_id")
            if claim_id not in graph.claims:
                errors.append(f"Broken Reference: Lineage claim '{claim_id}' does not exist in graph")

        for ev in explanation.lineage.evidence:
            ev_id = ev.get("node_id")
            if ev_id not in graph.evidence:
                errors.append(f"Broken Reference: Lineage evidence '{ev_id}' does not exist in graph")

        for doc in explanation.lineage.documents:
            doc_id = doc.get("node_id")
            if doc_id not in graph.documents:
                errors.append(f"Broken Reference: Lineage document '{doc_id}' does not exist in graph")

        for asm in explanation.lineage.assessments:
            asm_id = asm.get("node_id")
            if asm_id not in graph.assessments:
                errors.append(f"Broken Reference: Lineage assessment '{asm_id}' does not exist in graph")

        # Warnings for missing details
        if not explanation.reasoning:
            warnings.append("Explanation has empty reasoning text")
        if not explanation.summary:
            warnings.append("Explanation has empty summary text")

        return {"errors": errors, "warnings": warnings}

    @staticmethod
    def validate_and_raise(explanation: ExplanationNode, graph: ObservationGraph) -> None:
        result = ExplanationValidator.validate_explanation(explanation, graph)
        if result["errors"]:
            raise ExplanationValidationError(f"Explanation validation failed: {'; '.join(result['errors'])}")
