from typing import Any
from app.modules.evaluation.graph.graph_models import (
    ObservationGraph, DocumentNode, EvidenceNode, ClaimNode,
    ObservationNode, AssessmentNode, ConflictNode, RiskNode,
    QuestionNode, NodeType
)


# --- Basic O(1) Getters ---

def get_document(graph: ObservationGraph, doc_id: str) -> DocumentNode | None:
    return graph.documents.get(doc_id)


def get_evidence(graph: ObservationGraph, ev_id: str) -> EvidenceNode | None:
    return graph.evidence.get(ev_id)


def get_claim(graph: ObservationGraph, claim_id: str) -> ClaimNode | None:
    return graph.claims.get(claim_id)


def get_observation(graph: ObservationGraph, obs_id: str) -> ObservationNode | None:
    return graph.observations.get(obs_id)


def get_assessment(graph: ObservationGraph, asm_id: str) -> AssessmentNode | None:
    return graph.assessments.get(asm_id)


def get_conflict(graph: ObservationGraph, conflict_id: str) -> ConflictNode | None:
    return graph.conflicts.get(conflict_id)


def get_risk(graph: ObservationGraph, risk_id: str) -> RiskNode | None:
    return graph.risks.get(risk_id)


def get_question(graph: ObservationGraph, qst_id: str) -> QuestionNode | None:
    return graph.questions.get(qst_id)


def get_resolution(graph: ObservationGraph, res_id: str) -> Any | None:
    return graph.resolutions.get(res_id)


# --- Provenance Traversal with Cache & Recursion Guards ---

def trace_evidence(graph: ObservationGraph, evidence_id: str, visited: set[str] | None = None) -> dict[str, Any]:
    if visited is None:
        visited = set()
    if evidence_id in visited:
        return {}
    if evidence_id in graph.provenance_cache:
        return graph.provenance_cache[evidence_id]
    
    visited.add(evidence_id)
    ev = graph.evidence.get(evidence_id)
    doc = None
    
    # Trace Evidence -> Document (DERIVED_FROM)
    for edge in graph.out_edges.get(evidence_id, []):
        if edge.relationship == "DERIVED_FROM" and edge.target_type == NodeType.DOCUMENT:
            doc = graph.documents.get(edge.target_id)
            break
            
    res = {
        "evidence": ev,
        "document": doc
    }
    graph.provenance_cache[evidence_id] = res
    return res


def trace_claim(graph: ObservationGraph, claim_id: str, visited: set[str] | None = None) -> dict[str, Any]:
    if visited is None:
        visited = set()
    if claim_id in visited:
        return {}
    if claim_id in graph.provenance_cache:
        return graph.provenance_cache[claim_id]
    
    visited.add(claim_id)
    claim = graph.claims.get(claim_id)
    evidence_traces = []
    
    # Trace Claim -> Evidence (SUPPORTED_BY)
    for edge in graph.out_edges.get(claim_id, []):
        if edge.relationship == "SUPPORTED_BY" and edge.target_type == NodeType.EVIDENCE:
            evidence_traces.append(trace_evidence(graph, edge.target_id, visited))
            
    res = {
        "claim": claim,
        "evidence": evidence_traces
    }
    graph.provenance_cache[claim_id] = res
    return res


def trace_observation(graph: ObservationGraph, observation_id: str, visited: set[str] | None = None) -> dict[str, Any]:
    if visited is None:
        visited = set()
    if observation_id in visited:
        return {}
    if observation_id in graph.provenance_cache:
        return graph.provenance_cache[observation_id]
        
    visited.add(observation_id)
    obs = graph.observations.get(observation_id)
    claim_traces = []
    
    # Trace Observation -> Claim (SUPPORTED_BY)
    for edge in graph.out_edges.get(observation_id, []):
        if edge.relationship == "SUPPORTED_BY" and edge.target_type == NodeType.CLAIM:
            claim_traces.append(trace_claim(graph, edge.target_id, visited))
            
    res = {
        "observation": obs,
        "claims": claim_traces
    }
    graph.provenance_cache[observation_id] = res
    return res


def trace_assessment(graph: ObservationGraph, assessment_id: str, visited: set[str] | None = None) -> dict[str, Any]:
    if visited is None:
        visited = set()
    if assessment_id in visited:
        return {}
    if assessment_id in graph.provenance_cache:
        return graph.provenance_cache[assessment_id]
        
    visited.add(assessment_id)
    asm = graph.assessments.get(assessment_id)
    observation_traces = []
    
    # Trace Assessment -> Observation (GENERATED)
    for edge in graph.out_edges.get(assessment_id, []):
        if edge.relationship == "GENERATED" and edge.target_type == NodeType.OBSERVATION:
            observation_traces.append(trace_observation(graph, edge.target_id, visited))
            
    res = {
        "assessment": asm,
        "observations": observation_traces
    }
    graph.provenance_cache[assessment_id] = res
    return res


def trace_risk(graph: ObservationGraph, risk_id: str, visited: set[str] | None = None) -> dict[str, Any]:
    if visited is None:
        visited = set()
    if risk_id in visited:
        return {}
    if risk_id in graph.provenance_cache:
        return graph.provenance_cache[risk_id]
        
    visited.add(risk_id)
    risk = graph.risks.get(risk_id)
    observation_traces = []
    
    # Trace Risk -> Observation (REFERENCES)
    for edge in graph.out_edges.get(risk_id, []):
        if edge.relationship == "REFERENCES" and edge.target_type == NodeType.OBSERVATION:
            observation_traces.append(trace_observation(graph, edge.target_id, visited))
            
    res = {
        "risk": risk,
        "observations": observation_traces
    }
    graph.provenance_cache[risk_id] = res
    return res


def trace_question(graph: ObservationGraph, question_id: str, visited: set[str] | None = None) -> dict[str, Any]:
    if visited is None:
        visited = set()
    if question_id in visited:
        return {}
    if question_id in graph.provenance_cache:
        return graph.provenance_cache[question_id]
        
    visited.add(question_id)
    qst = graph.questions.get(question_id)
    observation_traces = []
    risk_traces = []
    
    # Trace Question -> Observation/Risk (QUESTIONS)
    for edge in graph.out_edges.get(question_id, []):
        if edge.relationship == "QUESTIONS":
            if edge.target_type == NodeType.OBSERVATION:
                observation_traces.append(trace_observation(graph, edge.target_id, visited))
            elif edge.target_type == NodeType.RISK:
                risk_traces.append(trace_risk(graph, edge.target_id, visited))
                
    res = {
        "question": qst,
        "observations": observation_traces,
        "risks": risk_traces
    }
    graph.provenance_cache[question_id] = res
    return res


# --- Output Query API ---

def get_assessment_outputs(graph: ObservationGraph, assessment_id: str) -> dict[str, list[Any]]:
    """Traverses AssessmentNode --GENERATED--> * edges to return generated outputs."""
    outputs = {
        "observations": [],
        "risks": [],
        "questions": [],
        "conflicts": []
    }
    for edge in graph.out_edges.get(assessment_id, []):
        if edge.relationship == "GENERATED":
            tid = edge.target_id
            if edge.target_type == NodeType.OBSERVATION:
                outputs["observations"].append(graph.observations[tid])
            elif edge.target_type == NodeType.RISK:
                outputs["risks"].append(graph.risks[tid])
            elif edge.target_type == NodeType.QUESTION:
                outputs["questions"].append(graph.questions[tid])
            elif edge.target_type == NodeType.CONFLICT:
                outputs["conflicts"].append(graph.conflicts[tid])
    return outputs


def get_executive_assessment(graph: ObservationGraph) -> Any:
    from app.modules.evaluation.executive.executive_queries import get_executive_assessment as get_exec_asm
    return get_exec_asm(graph)


def get_executive_summary(graph: ObservationGraph) -> Any:
    from app.modules.evaluation.executive.executive_queries import get_executive_summary as get_exec_sum
    return get_exec_sum(graph)


def get_key_risks(graph: ObservationGraph) -> Any:
    from app.modules.evaluation.executive.executive_queries import get_key_risks as get_kr
    return get_kr(graph)


def get_unresolved_conflicts(graph: ObservationGraph) -> Any:
    from app.modules.evaluation.executive.executive_queries import get_unresolved_conflicts as get_uc
    return get_uc(graph)


def trace_executive_finding(graph: ObservationGraph, finding_id: str) -> Any:
    from app.modules.evaluation.executive.executive_queries import trace_executive_finding as trace_ef
    return trace_ef(graph, finding_id)


def get_readiness_level(graph: ObservationGraph) -> Any:
    from app.modules.evaluation.executive.executive_queries import get_readiness_level as get_rl
    return get_rl(graph)


def get_investment_assessment(graph: ObservationGraph) -> Any:
    from app.modules.evaluation.investment.investment_queries import get_investment_assessment as get_inv_asm
    return get_inv_asm(graph)


def get_investment_score(graph: ObservationGraph) -> Any:
    from app.modules.evaluation.investment.investment_queries import get_investment_score as get_inv_score
    return get_inv_score(graph)


def get_recommendation(graph: ObservationGraph) -> Any:
    from app.modules.evaluation.investment.investment_queries import get_recommendation as get_rec
    return get_rec(graph)


def get_strengths(graph: ObservationGraph) -> Any:
    from app.modules.evaluation.investment.investment_queries import get_strengths as get_str
    return get_str(graph)


def get_major_risks(graph: ObservationGraph) -> Any:
    from app.modules.evaluation.investment.investment_queries import get_major_risks as get_mr
    return get_mr(graph)


def trace_investment_decision(graph: ObservationGraph) -> Any:
    from app.modules.evaluation.investment.investment_queries import trace_investment_decision as trace_id
    return trace_id(graph)


def get_report(graph: ObservationGraph) -> Any:
    from app.modules.evaluation.report.report_queries import get_report as get_rep
    return get_rep(graph)


def get_summary(graph: ObservationGraph) -> Any:
    from app.modules.evaluation.report.report_queries import get_summary as get_sum
    return get_sum(graph)


def get_section(graph: ObservationGraph, section_id: str) -> Any:
    from app.modules.evaluation.report.report_queries import get_section as get_sec
    return get_sec(graph, section_id)


def get_appendices(graph: ObservationGraph) -> Any:
    from app.modules.evaluation.report.report_queries import get_appendices as get_app
    return get_app(graph)


def trace_report_section(graph: ObservationGraph, section_id: str) -> Any:
    from app.modules.evaluation.report.report_queries import trace_report_section as trace_sec
    return trace_sec(graph, section_id)


def get_portfolio_entry(graph: ObservationGraph) -> Any:
    return graph.portfolio_entry


def get_portfolio_statistics(graph: ObservationGraph) -> Any:
    return graph.portfolio_statistics


def get_committee_decision(graph: ObservationGraph) -> Any:
    return graph.committee_decision


