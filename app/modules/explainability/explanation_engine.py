from app.modules.evaluation.graph.graph_models import ObservationGraph
from app.modules.explainability.explanation_models import ExplanationNode
from app.modules.explainability.explanation_builder import ExplanationBuilder


class ExplanationEngine:
    """Core engine to generate explanations for evaluation graph items."""

    def __init__(self) -> None:
        pass

    def explain_observation(self, graph: ObservationGraph, observation_id: str) -> ExplanationNode:
        return ExplanationBuilder.build_explanation(
            graph=graph,
            target_id=observation_id,
            target_type="OBSERVATION",
            summary=f"Explain Observation: {observation_id}"
        )

    def explain_assessment(self, graph: ObservationGraph, assessment_id: str) -> ExplanationNode:
        return ExplanationBuilder.build_explanation(
            graph=graph,
            target_id=assessment_id,
            target_type="ASSESSMENT",
            summary=f"Explain Assessment: {assessment_id}"
        )

    def explain_risk(self, graph: ObservationGraph, risk_id: str) -> ExplanationNode:
        return ExplanationBuilder.build_explanation(
            graph=graph,
            target_id=risk_id,
            target_type="RISK",
            summary=f"Explain Risk: {risk_id}"
        )

    def explain_question(self, graph: ObservationGraph, question_id: str) -> ExplanationNode:
        return ExplanationBuilder.build_explanation(
            graph=graph,
            target_id=question_id,
            target_type="QUESTION",
            summary=f"Explain Question: {question_id}"
        )

    def explain_correlation(self, graph: ObservationGraph, correlation_id: str) -> ExplanationNode:
        return ExplanationBuilder.build_explanation(
            graph=graph,
            target_id=correlation_id,
            target_type="CORRELATION",
            summary=f"Explain Correlation: {correlation_id}"
        )

    def explain_committee_decision(self, graph: ObservationGraph, decision_id: str) -> ExplanationNode:
        return ExplanationBuilder.build_explanation(
            graph=graph,
            target_id=decision_id,
            target_type="DECISION",
            summary="Explain Investment Committee Incubation Decision"
        )

    def explain_investment_decision(self, graph: ObservationGraph, investment_id: str) -> ExplanationNode:
        return ExplanationBuilder.build_explanation(
            graph=graph,
            target_id=investment_id,
            target_type="INVESTMENT",
            summary="Explain Investment Recommendation and Domain Scores"
        )

    def explain_portfolio_ranking(self, graph: ObservationGraph, startup_id: str) -> ExplanationNode:
        return ExplanationBuilder.build_explanation(
            graph=graph,
            target_id=startup_id,
            target_type="PORTFOLIO",
            summary=f"Explain Portfolio Ranking for Startup {startup_id}"
        )

    def explain_executive_summary(self, graph: ObservationGraph, executive_id: str) -> ExplanationNode:
        return ExplanationBuilder.build_explanation(
            graph=graph,
            target_id=executive_id,
            target_type="EXECUTIVE",
            summary="Explain Executive Intelligence Findings and Readiness"
        )

    def generate_explanation(self, graph: ObservationGraph, target_id: str, target_type: str) -> ExplanationNode:
        """Main dispatcher entry point to generate explanations dynamically."""
        ttype = target_type.upper()
        if "OBSERVATION" in ttype:
            return self.explain_observation(graph, target_id)
        if "ASSESSMENT" in ttype:
            return self.explain_assessment(graph, target_id)
        if "RISK" in ttype:
            return self.explain_risk(graph, target_id)
        if "QUESTION" in ttype:
            return self.explain_question(graph, target_id)
        if "CORRELATION" in ttype:
            return self.explain_correlation(graph, target_id)
        if "DECISION" in ttype or "COMMITTEE" in ttype:
            return self.explain_committee_decision(graph, target_id)
        if "INVESTMENT" in ttype:
            return self.explain_investment_decision(graph, target_id)
        if "PORTFOLIO" in ttype:
            return self.explain_portfolio_ranking(graph, target_id)
        if "EXECUTIVE" in ttype:
            return self.explain_executive_summary(graph, target_id)

        # Fallback generic explanation builder
        return ExplanationBuilder.build_explanation(graph, target_id, target_type)
