from typing import List, Any, Optional
from app.modules.evaluation.graph.graph_models import ObservationGraph, NodeType
from app.modules.evaluation.committee.committee_models import (
    InvestmentCommitteeDecision, Recommendation, Priority, DueDiligenceCategory,
    CommitteeReport
)



class CommitteeValidator:
    """Validator for Investment Committee Decisions."""

    @staticmethod
    def validate(graph: ObservationGraph, portfolio: Optional[Any] = None) -> List[str]:
        """Validates the committee decision in the graph against all business rules."""
        errors = []
        decision = graph.committee_decision
        if not decision:
            errors.append("Committee Decision node does not exist in the graph.")
            return errors

        # 1. Recommendation enum check
        if not isinstance(decision.recommendation, Recommendation):
            errors.append(f"Invalid recommendation enum value: {decision.recommendation}")

        # 2. Priority enums check
        for prop in ["investment_priority", "incubation_priority", "grant_priority", "pilot_priority"]:
            val = getattr(decision, prop, None)
            if not isinstance(val, Priority):
                errors.append(f"Invalid priority enum for {prop}: {val}")

        # 3. Confidence range check
        if not (0.0 <= decision.decision_confidence <= 1.0):
            errors.append(f"Decision confidence {decision.decision_confidence} is outside valid range [0.0, 1.0].")

        # 4. Executive assessment exists check
        if not graph.executive_assessment:
            errors.append("Executive assessment reference does not exist in graph.")
        else:
            if decision.executive_summary_id != graph.executive_assessment.assessment_id:
                errors.append(f"Executive summary ID mismatch: {decision.executive_summary_id} vs {graph.executive_assessment.assessment_id}")

        # 5. Investment assessment exists check
        if not graph.investment_assessment:
            errors.append("Investment assessment reference does not exist in graph.")
        else:
            if decision.investment_assessment_id != graph.investment_assessment.assessment_id:
                errors.append(f"Investment assessment ID mismatch: {decision.investment_assessment_id} vs {graph.investment_assessment.assessment_id}")

        # 6. Portfolio reference check
        if portfolio:
            if decision.portfolio_hash != portfolio.portfolio_hash:
                errors.append("Portfolio hash reference mismatch.")
        elif decision.portfolio_hash == "N/A" and graph.portfolio_entry is not None:
            errors.append("Portfolio reference is missing or N/A despite portfolio_entry being present.")

        # 7. Graph reference check
        # Temporarily detach committee_decision to calculate clean graph hash
        orig_dec = graph.committee_decision
        graph.committee_decision = None
        from app.modules.evaluation.graph.graph_builder import ObservationGraphBuilder
        clean_hash = ObservationGraphBuilder._compute_hash(graph)
        graph.committee_decision = orig_dec
        if decision.graph_hash != clean_hash:
            errors.append(f"Decision graph hash {decision.graph_hash} does not match current clean graph hash {clean_hash}.")

        # 8. Required documents unique check
        if len(decision.required_documents) != len(set(decision.required_documents)):
            errors.append("Required documents list contains duplicate entries.")

        # 9. DD references valid check
        for idx, item in enumerate(decision.required_due_diligence):
            if not isinstance(item.category, DueDiligenceCategory):
                errors.append(f"Invalid due diligence category at index {idx}: {item.category}")
            if not item.status:
                errors.append(f"Status is empty for due diligence item at index {idx}.")
            if not item.reason:
                errors.append(f"Reason is empty for due diligence item at index {idx}.")

        # 10. Follow-up questions valid check
        if not decision.follow_up_questions:
            errors.append("Follow-up questions list is empty.")
        else:
            for idx, q in enumerate(decision.follow_up_questions):
                if not q or not isinstance(q, str):
                    errors.append(f"Invalid follow-up question at index {idx}.")

        # 11. Reasoning not empty check
        if not decision.decision_reasoning or not decision.decision_reasoning.strip():
            errors.append("Decision reasoning is empty or whitespace.")

        return errors

    @staticmethod
    def validate_report(report: CommitteeReport, graph: Optional[ObservationGraph] = None) -> List[str]:
        errors = []
        
        # 1. workflow reference exists
        if not report.decision.workflow_reference:
            errors.append("Workflow reference is missing or empty.")
            
        # 2. every confidence between 0 and 1
        if not (0.0 <= report.decision.overall_confidence <= 1.0):
            errors.append(f"Overall confidence {report.decision.overall_confidence} is outside [0, 1].")
        for f in report.findings:
            if not (0.0 <= f.confidence <= 1.0):
                errors.append(f"Finding confidence {f.confidence} for {f.finding_id} is outside [0, 1].")
        for c in report.concerns:
            if not (0.0 <= c.confidence <= 1.0):
                errors.append(f"Concern confidence {c.confidence} for {c.concern_id} is outside [0, 1].")
        if not (0.0 <= report.consensus.agreement_level <= 1.0):
            errors.append(f"Consensus agreement level {report.consensus.agreement_level} is outside [0, 1].")
            
        # 3. every concern references risks
        for c in report.concerns:
            if not c.linked_risks:
                errors.append(f"Concern {c.concern_id} does not reference any risks.")
                
        # 4. every recommendation supported
        if not report.recommendations.justification or not report.recommendations.justification.strip():
            errors.append("Recommendation justification is empty.")
            
        # 5. no orphan findings
        for f in report.findings:
            if not f.supporting_observations:
                errors.append(f"Finding {f.finding_id} is an orphan (has no supporting observations).")
                
        # 6. duplicate findings merged
        from app.modules.evaluation.committee.committee_rules import Jaccard_similarity
        for i, f1 in enumerate(report.findings):
            for f2 in report.findings[i+1:]:
                if Jaccard_similarity(f1.title, f2.title) >= 0.8:
                    errors.append(f"Duplicate findings found: {f1.finding_id} and {f2.finding_id} have highly similar titles.")
                    
        # 7. every contradiction linked
        for c in report.consensus.contradictions:
            if not c.get("conflict_id"):
                errors.append("Contradiction does not contain a linked conflict_id.")
                
        # 8. all references resolve
        if graph:
            for f in report.findings:
                for obs_id in f.supporting_observations:
                    if obs_id not in graph.observations:
                        errors.append(f"Supporting observation {obs_id} in finding {f.finding_id} does not exist in graph.")
                for claim_id in f.supporting_claims:
                    if claim_id not in graph.claims:
                        errors.append(f"Supporting claim {claim_id} in finding {f.finding_id} does not exist in graph.")
                for ev_id in f.supporting_evidence:
                    if ev_id not in graph.evidence:
                        errors.append(f"Supporting evidence {ev_id} in finding {f.finding_id} does not exist in graph.")
                        
            for concern in report.concerns:
                for r_id in concern.linked_risks:
                    if r_id not in graph.risks:
                        errors.append(f"Linked risk {r_id} in concern {concern.concern_id} does not exist in graph.")
                        
            # Check if graph hash matches
            orig_dec = graph.committee_decision
            orig_rep = getattr(graph, "committee_report", None)
            graph.committee_decision = None
            if hasattr(graph, "committee_report"):
                graph.committee_report = None
            from app.modules.evaluation.graph.graph_builder import ObservationGraphBuilder
            clean_hash = ObservationGraphBuilder._compute_hash(graph)
            graph.committee_decision = orig_dec
            if hasattr(graph, "committee_report"):
                graph.committee_report = orig_rep
                
            if report.decision.graph_hash != clean_hash:
                errors.append(f"Report graph hash {report.decision.graph_hash} does not match current clean graph hash {clean_hash}.")
                
        return errors

