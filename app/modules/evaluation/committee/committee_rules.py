from typing import Any, Dict, List, Set, Tuple
from app.modules.evaluation.graph.graph_models import ObservationGraph, NodeType, RiskNode


class DecisionCategory:
    READY_FOR_INCUBATION = "Ready for Incubation"
    PROMISING_BUT_CLARIFICATION = "Promising but Requires Clarification"
    REQUIRES_SIGNIFICANT_VALIDATION = "Requires Significant Validation"
    NOT_READY_YET = "Not Ready Yet"


def classify_decision(
    investment_score: float,
    active_risk_count: int,
    unresolved_conflicts: int,
    overall_confidence: float
) -> Tuple[str, str]:
    """Classify the startup application into one of the four committee categories."""
    if (
        investment_score >= 75.0
        and active_risk_count <= 2
        and unresolved_conflicts == 0
        and overall_confidence >= 0.7
    ):
        category = DecisionCategory.READY_FOR_INCUBATION
        justification = (
            f"Startup shows high preparedness with a score of {investment_score:.1f}, "
            f"minimal active risks ({active_risk_count}), zero unresolved conflicts, "
            f"and robust overall confidence of {overall_confidence:.2f}."
        )
    elif (
        investment_score >= 60.0
        and active_risk_count <= 4
        and unresolved_conflicts <= 2
        and overall_confidence >= 0.5
    ):
        category = DecisionCategory.PROMISING_BUT_CLARIFICATION
        justification = (
            f"Startup is promising with a score of {investment_score:.1f}, but requires "
            f"clarification on {active_risk_count} active risks and {unresolved_conflicts} unresolved conflicts."
        )
    elif (
        investment_score >= 45.0
        or active_risk_count >= 5
        or unresolved_conflicts >= 3
    ):
        category = DecisionCategory.REQUIRES_SIGNIFICANT_VALIDATION
        justification = (
            f"Startup has critical gaps: score of {investment_score:.1f}, elevated risk "
            f"density ({active_risk_count} active risks), or substantial conflicts ({unresolved_conflicts})."
        )
    else:
        category = DecisionCategory.NOT_READY_YET
        justification = (
            f"Startup is not ready for incubation at this time. Overall score of {investment_score:.1f} "
            f"or confidence of {overall_confidence:.2f} lies below acceptable thresholds."
        )

    return category, justification


def detect_dependencies(graph: ObservationGraph) -> List[Dict[str, Any]]:
    """Identifies and models cross-domain dependencies in the evaluation graph."""
    dependencies = []

    # Helper: Check if a domain has active observations or risks
    def has_domain_observations(domain: str) -> bool:
        return any(o.domain == domain for o in graph.observations.values())

    # 1. TRL depends on Product maturity
    if has_domain_observations("trl") and has_domain_observations("product"):
        # Look for TRL observations suggesting prototype/maturation status
        trl_obs = [o for o in graph.observations.values() if o.domain == "trl"]
        prod_obs = [o for o in graph.observations.values() if o.domain == "product"]
        
        avg_trl_conf = sum(o.confidence for o in trl_obs) / len(trl_obs) if trl_obs else 1.0
        avg_prod_conf = sum(o.confidence for o in prod_obs) / len(prod_obs) if prod_obs else 1.0
        
        dependencies.append({
            "source_domain": "trl",
            "target_domain": "product",
            "dependency_type": "requires_maturity",
            "description": "Technology Readiness Level (TRL) depends on product maturity and laboratory/field validations.",
            "impact_score": round(abs(avg_trl_conf - avg_prod_conf), 2)
        })

    # 2. Financial runway depends on Market traction
    if has_domain_observations("financial") and has_domain_observations("market"):
        dependencies.append({
            "source_domain": "financial",
            "target_domain": "market",
            "dependency_type": "revenue_validation",
            "description": "Financial model projections and capital runway depend directly on market traction and demand size validations.",
            "impact_score": 0.5
        })

    # 3. Product differentiation/competition depends on IP barriers
    if has_domain_observations("competition") and has_domain_observations("ip"):
        dependencies.append({
            "source_domain": "competition",
            "target_domain": "ip",
            "dependency_type": "moat_validation",
            "description": "Competitive differentiation and defensive moats depend on patent filings and proprietary IP ownership.",
            "impact_score": 0.4
        })

    return dependencies


def Jaccard_similarity(text1: str, text2: str) -> float:
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 and not words2:
        return 1.0
    return len(words1 & words2) / len(words1 | words2)


def merge_risks_logic(risks: List[RiskNode], out_edges: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
    """Merges duplicate or related risks while preserving complete provenance."""
    merged_risks: List[Dict[str, Any]] = []
    visited: Set[str] = set()

    for i, r1 in enumerate(risks):
        if r1.risk_id in visited:
            continue

        current_risk = {
            "risk_id": r1.risk_id,
            "category": r1.category,
            "description": r1.description,
            "confidence": r1.confidence,
            "reasoning": getattr(r1, "reasoning", ""),
            "supporting_observations": set(),
            "supporting_claims": set(),
            "supporting_evidence": set()
        }

        # Populate initial provenance from out_edges
        for edge in out_edges.get(r1.risk_id, []):
            if edge.target_type == NodeType.OBSERVATION:
                current_risk["supporting_observations"].add(edge.target_id)
            elif edge.target_type == NodeType.CLAIM:
                current_risk["supporting_claims"].add(edge.target_id)
            elif edge.target_type == NodeType.EVIDENCE:
                current_risk["supporting_evidence"].add(edge.target_id)

        visited.add(r1.risk_id)

        # Look for duplicate or highly similar risks in the remaining list
        for r2 in risks[i + 1:]:
            if r2.risk_id in visited:
                continue

            # Merge if same category and Jaccard similarity >= 0.5
            if r1.category == r2.category and Jaccard_similarity(r1.description, r2.description) >= 0.5:
                # Merge descriptions
                if r2.description not in current_risk["description"]:
                    current_risk["description"] += f" | Also: {r2.description}"
                # Confidence is max
                current_risk["confidence"] = max(current_risk["confidence"], r2.confidence)
                # Combine reasoning
                r2_reason = getattr(r2, "reasoning", "")
                if r2_reason and r2_reason not in current_risk["reasoning"]:
                    current_risk["reasoning"] += f" | {r2_reason}"

                # Combine provenance
                for edge in out_edges.get(r2.risk_id, []):
                    if edge.target_type == NodeType.OBSERVATION:
                        current_risk["supporting_observations"].add(edge.target_id)
                    elif edge.target_type == NodeType.CLAIM:
                        current_risk["supporting_claims"].add(edge.target_id)
                    elif edge.target_type == NodeType.EVIDENCE:
                        current_risk["supporting_evidence"].add(edge.target_id)

                visited.add(r2.risk_id)

        # Convert sets back to sorted lists
        current_risk["supporting_observations"] = sorted(list(current_risk["supporting_observations"]))
        current_risk["supporting_claims"] = sorted(list(current_risk["supporting_claims"]))
        current_risk["supporting_evidence"] = sorted(list(current_risk["supporting_evidence"]))

        merged_risks.append(current_risk)

    return merged_risks
