import json
from datetime import datetime
from enum import Enum
from typing import Any
from app.modules.evaluation.graph.graph_models import (
    ObservationGraph, DocumentNode, EvidenceNode, ClaimNode,
    ObservationNode, AssessmentNode, ConflictNode, RiskNode,
    QuestionNode, Edge, GraphStatistics, NodeType
)


def fast_dump(node: Any, graph: ObservationGraph) -> Any:
    """Serializes a graph node recursively into JSON-safe dictionaries using local dump caching for performance.

    Args:
        node: The node model (e.g. DocumentNode, EvidenceNode, ClaimNode) or a standard python object.
        graph: The active ObservationGraph instance hosting the dump_cache.

    Returns:
        A JSON-serializable dictionary representation of the node.
        
    Complexity:
        - O(1) if the node's cached dump is already present in graph.dump_cache.
        - O(N) where N is the number of fields/relationships for a cache miss.
    """
    if isinstance(node, datetime):
        return node.isoformat() + "Z"
    if isinstance(node, Enum):
        return node.value
    if isinstance(node, dict):
        return {k: fast_dump(v, graph) for k, v in node.items()}
    if isinstance(node, list):
        return [fast_dump(x, graph) for x in node]

    node_type = getattr(node, "node_type", None)
    node_id_val = getattr(node, "node_id", None) or id(node)
    
    if not hasattr(graph, "dump_cache"):
        graph.dump_cache = {}
        
    if node_id_val in graph.dump_cache:
        return graph.dump_cache[node_id_val]
        
    if node_type in (
        NodeType.DOCUMENT, NodeType.EVIDENCE, NodeType.CLAIM, NodeType.OBSERVATION, 
        NodeType.RISK, NodeType.QUESTION, NodeType.CORRELATION, NodeType.RESOLUTION, NodeType.CONFLICT
    ):
        res = {k: v for k, v in node.__dict__.items() if not k.startswith("_")}
        for k, v in list(res.items()):
            if isinstance(v, (datetime, Enum, dict, list)):
                res[k] = fast_dump(v, graph)
    elif hasattr(node, "model_dump"):
        res = node.model_dump(mode="json")
    elif hasattr(node, "__dict__"):
        res = {k: v for k, v in node.__dict__.items() if not k.startswith("_")}
        for k, v in list(res.items()):
            if isinstance(v, (datetime, Enum, dict, list)):
                res[k] = fast_dump(v, graph)
    else:
        return node
    # Also handle key_observations, major_risks, and summary if it's an ExecutiveAssessment
    if "summary" in res and hasattr(res["summary"], "model_dump"):
        res["summary"] = res["summary"].model_dump()
    if "key_observations" in res:
        res["key_observations"] = [o.model_dump() if hasattr(o, "model_dump") else o for o in res["key_observations"]]
    if "major_risks" in res:
        res["major_risks"] = [r.model_dump() if hasattr(r, "model_dump") else r for r in res["major_risks"]]
    if "traceability" in res:
        trace_memo = {}
        def format_trace(item):
            item_id = id(item)
            if item_id in trace_memo:
                return trace_memo[item_id]
            if isinstance(item, list):
                ret = [format_trace(x) for x in item]
                trace_memo[item_id] = ret
                return ret
            if isinstance(item, dict):
                ret = {k: format_trace(v) for k, v in item.items()}
                trace_memo[item_id] = ret
                return ret
            if isinstance(item, Enum):
                return item.value
            if isinstance(item, (str, int, float, bool, type(None))):
                return item
            if hasattr(item, "__dict__"):
                ret = fast_dump(item, graph)
                trace_memo[item_id] = ret
                return ret
            return item
        res["traceability"] = format_trace(res["traceability"])
        
    # Only cache static nodes that are inside graph collections and are immutable
    if node_type in (NodeType.DOCUMENT, NodeType.EVIDENCE, NodeType.CLAIM, NodeType.OBSERVATION, NodeType.ASSESSMENT, NodeType.RISK, NodeType.QUESTION, NodeType.CORRELATION, NodeType.RESOLUTION, NodeType.CONFLICT):
        graph.dump_cache[node_id_val] = res
        
    return res


def to_json(graph: ObservationGraph) -> str:
    """Serializes the graph metadata, nodes, and typed edges to a structured JSON string."""
    if not hasattr(graph, "dump_cache"):
        graph.dump_cache = {}

    data = {
        "graph_id": graph.graph_id,
        "graph_version": graph.graph_version,
        "graph_hash": graph.graph_hash,
        "created_at": graph.created_at.isoformat() + "Z" if isinstance(graph.created_at, datetime) else graph.created_at,
        "documents": {nid: fast_dump(node, graph) for nid, node in graph.documents.items()},
        "evidence": {nid: fast_dump(node, graph) for nid, node in graph.evidence.items()},
        "claims": {nid: fast_dump(node, graph) for nid, node in graph.claims.items()},
        "observations": {nid: fast_dump(node, graph) for nid, node in graph.observations.items()},
        "assessments": {nid: fast_dump(node, graph) for nid, node in graph.assessments.items()},
        "conflicts": {nid: fast_dump(node, graph) for nid, node in graph.conflicts.items()},
        "risks": {nid: fast_dump(node, graph) for nid, node in graph.risks.items()},
        "questions": {nid: fast_dump(node, graph) for nid, node in graph.questions.items()},
        "correlations": {nid: fast_dump(node, graph) for nid, node in graph.correlations.items()},
        "resolutions": {nid: fast_dump(node, graph) for nid, node in graph.resolutions.items()},
        "edges": [edge.__dict__ for edge in graph.edges],
        "resolution_edges": [edge.__dict__ for edge in graph.resolution_edges],
        "graph_stats": graph.graph_stats.__dict__,
        "executive_assessment": fast_dump(graph.executive_assessment, graph) if graph.executive_assessment else None,
        "executive_indexes": graph.executive_indexes,
        "executive_statistics": graph.executive_statistics,
        "investment_assessment": fast_dump(graph.investment_assessment, graph) if graph.investment_assessment else None,
        "investment_indexes": graph.investment_indexes,
        "investment_statistics": graph.investment_statistics,
        "report": fast_dump(graph.report, graph) if graph.report else None,
        "report_indexes": graph.report_indexes,
        "report_statistics": graph.report_statistics,
        "portfolio_entry": fast_dump(graph.portfolio_entry, graph) if graph.portfolio_entry else None,
        "portfolio_statistics": fast_dump(graph.portfolio_statistics, graph) if graph.portfolio_statistics else None,
        "committee_decision": fast_dump(graph.committee_decision, graph) if graph.committee_decision else None,
        "startup_id": graph.startup_id,
        "startup_name": graph.startup_name,
        "category": graph.category
    }
    return json.dumps(data)



def from_json(json_str: str) -> ObservationGraph:
    """Reconstructs the ObservationGraph (including edge lookups, indexes, and cache) from JSON."""
    data = json.loads(json_str)
    graph = ObservationGraph()
    graph.graph_id = data.get("graph_id", "")
    graph.graph_version = data.get("graph_version", "1.0.0")
    graph.graph_hash = data.get("graph_hash", "")
    graph.created_at = data.get("created_at", "")

    # Lazy import to avoid circular dependency
    from app.modules.evaluation.correlation.correlation_models import CorrelationNode
    from app.modules.evaluation.conflict_resolution.conflict_models import ResolutionNode, ResolutionEdge

    # Instantiate nodes
    for nid, payload in data.get("documents", {}).items():
        graph.documents[nid] = DocumentNode(**payload)
    for nid, payload in data.get("evidence", {}).items():
        graph.evidence[nid] = EvidenceNode(**payload)
    for nid, payload in data.get("claims", {}).items():
        graph.claims[nid] = ClaimNode(**payload)
    for nid, payload in data.get("observations", {}).items():
        graph.observations[nid] = ObservationNode(**payload)
    for nid, payload in data.get("assessments", {}).items():
        graph.assessments[nid] = AssessmentNode(**payload)
    for nid, payload in data.get("conflicts", {}).items():
        graph.conflicts[nid] = ConflictNode(**payload)
    for nid, payload in data.get("risks", {}).items():
        graph.risks[nid] = RiskNode(**payload)
    for nid, payload in data.get("questions", {}).items():
        graph.questions[nid] = QuestionNode(**payload)
    for nid, payload in data.get("correlations", {}).items():
        graph.correlations[nid] = CorrelationNode(**payload)
    for nid, payload in data.get("resolutions", {}).items():
        graph.resolutions[nid] = ResolutionNode(**payload)

    # Instantiate edges
    for edge_payload in data.get("edges", []):
        edge = Edge(**edge_payload)
        graph.edges.append(edge)
        graph.out_edges.setdefault(edge.source_id, []).append(edge)
        graph.in_edges.setdefault(edge.target_id, []).append(edge)

    # Instantiate resolution edges
    for edge_payload in data.get("resolution_edges", []):
        res_edge = ResolutionEdge(**edge_payload)
        graph.resolution_edges.append(res_edge)

    # Instantiate stats
    graph.graph_stats = GraphStatistics(**data.get("graph_stats", {}))

    # Rebuild indexes
    for obs_id, obs in graph.observations.items():
        graph.observations_by_domain.setdefault(obs.domain, []).append(obs_id)
    for asm_id, asm in graph.assessments.items():
        graph.assessments_by_domain.setdefault(asm.domain, []).append(asm_id)
    for risk_id, risk in graph.risks.items():
        graph.risks_by_category.setdefault(risk.category, []).append(risk_id)
    for corr_id, corr in graph.correlations.items():
        for edge in graph.out_edges.get(corr_id, []):
            if edge.relationship == "RELATED_TO" and edge.target_type == NodeType.OBSERVATION:
                graph.correlations_by_observation.setdefault(edge.target_id, []).append(corr)

    # Rebuild resolution indexes
    for res_id, res in graph.resolutions.items():
        graph.resolutions_by_conflict.setdefault(res.conflict_id, []).append(res_id)
        if res.preferred_observation_id:
            graph.resolutions_by_observation.setdefault(res.preferred_observation_id, []).append(res_id)

    # Deserialize Executive Layer
    exec_data = data.get("executive_assessment")
    if exec_data:
        from app.modules.evaluation.executive.executive_models import ExecutiveAssessment, ExecutiveSummary, ExecutiveFinding
        summary_payload = exec_data.get("summary")
        summary = ExecutiveSummary(**summary_payload) if summary_payload else None
        key_obs = [ExecutiveFinding(**f) for f in exec_data.get("key_observations", [])]
        major_risks = [ExecutiveFinding(**f) for f in exec_data.get("major_risks", [])]
        
        exec_node = ExecutiveAssessment(
            node_id=exec_data["node_id"],
            node_type=exec_data["node_type"],
            assessment_id=exec_data["assessment_id"],
            generated_at=exec_data["generated_at"],
            graph_version=exec_data.get("graph_version", "1.0.0"),
            summary=summary,
            key_observations=key_obs,
            major_risks=major_risks,
            unresolved_conflicts=exec_data.get("unresolved_conflicts", []),
            evidence_strength=exec_data.get("evidence_strength", 0.0),
            confidence=exec_data.get("confidence", 0.0),
            readiness_level=exec_data.get("readiness_level", "TRL-1"),
            traceability=exec_data.get("traceability", {}),
            metadata=exec_data.get("metadata", {})
        )
        graph.executive_assessment = exec_node
        
    graph.executive_indexes = data.get("executive_indexes", {})
    graph.executive_statistics = data.get("executive_statistics", {})

    # Deserialize Investment Layer
    inv_data = data.get("investment_assessment")
    if inv_data:
        from app.modules.evaluation.investment.investment_models import InvestmentAssessment, InvestmentRecommendation
        graph.investment_assessment = InvestmentAssessment(
            node_id=inv_data["node_id"],
            node_type=inv_data["node_type"],
            assessment_id=inv_data["assessment_id"],
            generated_at=inv_data["generated_at"],
            graph_version=inv_data.get("graph_version", "1.0.0"),
            recommendation=InvestmentRecommendation(inv_data["recommendation"]),
            confidence=inv_data.get("confidence", 0.0),
            investment_score=inv_data.get("investment_score", 0.0),
            readiness_score=inv_data.get("readiness_score", 0.0),
            risk_score=inv_data.get("risk_score", 0.0),
            technology_score=inv_data.get("technology_score", 0.0),
            market_score=inv_data.get("market_score", 0.0),
            founder_score=inv_data.get("founder_score", 0.0),
            financial_score=inv_data.get("financial_score", 0.0),
            competition_score=inv_data.get("competition_score", 0.0),
            ip_score=inv_data.get("ip_score", 0.0),
            executive_summary=inv_data.get("executive_summary", ""),
            strengths=inv_data.get("strengths", []),
            weaknesses=inv_data.get("weaknesses", []),
            major_risks=inv_data.get("major_risks", []),
            investment_rationale=inv_data.get("investment_rationale", ""),
            missing_information=inv_data.get("missing_information", []),
            follow_up_questions=inv_data.get("follow_up_questions", []),
            traceability=inv_data.get("traceability", {}),
            metadata=inv_data.get("metadata", {})
        )
    graph.investment_indexes = data.get("investment_indexes", {})
    graph.investment_statistics = data.get("investment_statistics", {})

    # Deserialize Report Layer
    rep_data = data.get("report")
    if rep_data:
        from app.modules.evaluation.report.report_models import DueDiligenceReport, ReportSection, Appendix
        
        def make_section(name):
            payload = rep_data.get(name)
            if not payload:
                return None
            return ReportSection(**payload)
            
        executive_summary = make_section("executive_summary")
        investment_recommendation = make_section("investment_recommendation") or make_section("investment_summary")
        founder_assessment = make_section("founder_assessment") or make_section("founder_analysis")
        product_technology = make_section("product_technology") or make_section("product_analysis") or make_section("trl_analysis")
        market_opportunity = make_section("market_opportunity") or make_section("market_analysis")
        business_model = make_section("business_model") or make_section("product_analysis")
        competition = make_section("competition") or make_section("competition_analysis")
        financial_overview = make_section("financial_overview") or make_section("financial_analysis")
        risks = make_section("risks") or make_section("risk_analysis")
        investment_thesis = make_section("investment_thesis") or make_section("investment_summary")
        follow_up_questions = make_section("follow_up_questions")
        
        investment_summary = make_section("investment_summary")
        founder_analysis = make_section("founder_analysis")
        product_analysis = make_section("product_analysis")
        trl_analysis = make_section("trl_analysis")
        market_analysis = make_section("market_analysis")
        competition_analysis = make_section("competition_analysis")
        financial_analysis = make_section("financial_analysis")
        ip_analysis = make_section("ip_analysis")
        risk_analysis = make_section("risk_analysis")
        observations = make_section("observations")
        conflicts = make_section("conflicts")
        resolutions = make_section("resolutions")
        missing_information = make_section("missing_information")
        
        appendices = [Appendix(**a) for a in rep_data.get("appendices", [])]
        
        graph.report = DueDiligenceReport(
            node_id=rep_data["node_id"],
            node_type=rep_data["node_type"],
            report_id=rep_data["report_id"],
            generated_at=rep_data["generated_at"],
            graph_version=rep_data.get("graph_version", "1.0.0"),
            executive_summary=executive_summary,
            investment_recommendation=investment_recommendation,
            founder_assessment=founder_assessment,
            product_technology=product_technology,
            market_opportunity=market_opportunity,
            business_model=business_model,
            competition=competition,
            financial_overview=financial_overview,
            risks=risks,
            investment_thesis=investment_thesis,
            follow_up_questions=follow_up_questions,
            investment_summary=investment_summary,
            founder_analysis=founder_analysis,
            product_analysis=product_analysis,
            trl_analysis=trl_analysis,
            market_analysis=market_analysis,
            competition_analysis=competition_analysis,
            financial_analysis=financial_analysis,
            ip_analysis=ip_analysis,
            risk_analysis=risk_analysis,
            observations=observations,
            conflicts=conflicts,
            resolutions=resolutions,
            missing_information=missing_information,
            appendices=appendices,
            traceability=rep_data.get("traceability", {}),
            metadata=rep_data.get("metadata", {})
        )
    graph.report_indexes = data.get("report_indexes", {})
    graph.report_statistics = data.get("report_statistics", {})

    # Deserialize Portfolio Layer
    port_entry_data = data.get("portfolio_entry")
    if port_entry_data:
        from app.modules.evaluation.portfolio.portfolio_models import PortfolioEntry
        graph.portfolio_entry = PortfolioEntry(**port_entry_data)
        
    port_stats_data = data.get("portfolio_statistics")
    if port_stats_data:
        from app.modules.evaluation.portfolio.portfolio_models import PortfolioStatistics
        graph.portfolio_statistics = PortfolioStatistics(**port_stats_data)
        
    # Deserialize Committee Layer
    comm_data = data.get("committee_decision")
    if comm_data:
        from app.modules.evaluation.committee.committee_models import InvestmentCommitteeDecision
        graph.committee_decision = InvestmentCommitteeDecision(**comm_data)
        
    graph.startup_id = data.get("startup_id", "")
    graph.startup_name = data.get("startup_name", "")
    graph.category = data.get("category", "")

    # Rebuild cache
    from app.modules.evaluation.graph.graph_builder import ObservationGraphBuilder
    ObservationGraphBuilder._populate_provenance_cache(graph)

    return graph


def export_traceability(graph: ObservationGraph) -> dict:
    """Compiles a flat traceability map grouping nodes by type for auditing."""
    exec_node = graph.executive_assessment
    inv_node = graph.investment_assessment
    return {
        "document": [node.model_dump() for node in graph.documents.values()],
        "evidence": [node.model_dump() for node in graph.evidence.values()],
        "claim": [node.model_dump() for node in graph.claims.values()],
        "observation": [node.model_dump() for node in graph.observations.values()],
        "assessment": [node.model_dump() for node in graph.assessments.values()],
        "risk": [node.model_dump() for node in graph.risks.values()],
        "resolution": [node.model_dump() for node in graph.resolutions.values()],
        "executive_assessment": exec_node.model_dump() if exec_node else None,
        "investment_assessment": inv_node.model_dump() if inv_node else None,
        "report": graph.report.model_dump() if graph.report else None,
        "committee_decision": graph.committee_decision.model_dump() if graph.committee_decision else None
    }

