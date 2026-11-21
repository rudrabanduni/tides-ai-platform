"""Fallback observation graph helper for offline bootstrapping/mock runs.

Extracted from test fixtures into a production-safe module so API dependencies
never import from ``tests.*``.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.modules.evaluation.executive.executive_models import ExecutiveAssessment, ExecutiveSummary
from app.modules.evaluation.graph.graph_builder import ObservationGraphBuilder
from app.modules.evaluation.graph.graph_models import (
    AssessmentNode,
    ClaimNode,
    ConflictNode,
    DocumentNode,
    Edge,
    EvidenceNode,
    NodeType,
    ObservationGraph,
    ObservationNode,
    QuestionNode,
    RiskNode,
)
from app.modules.evaluation.investment.investment_models import InvestmentAssessment, InvestmentRecommendation
from app.modules.evaluation.portfolio.portfolio_models import PortfolioEntry


def create_fallback_observation_graph(
    startup_id: str,
    name: str,
    category: str,
    investment_score: float,
    confidence: float,
    overall_consensus: float = 0.8,
    active_risks_count: int = 1,
    evidence_count: int = 5,
    executive_confidence: float = 0.9,
    evidence_strength: float = 0.9,
    question_count: int = 2,
    unresolved_conflicts: int = 0,
) -> ObservationGraph:
    """Build a schema-complete fallback ObservationGraph when no claims are available."""
    graph = ObservationGraph()
    graph.startup_id = startup_id
    graph.graph_id = startup_id
    graph.startup_name = name
    graph.category = category

    now_dt = datetime.now(timezone.utc)
    now_iso = now_dt.isoformat().replace("+00:00", "Z")
    graph.created_at = now_iso

    # 1. Documents
    graph.documents["doc-1"] = DocumentNode(
        node_id="doc-1",
        node_type=NodeType.DOCUMENT,
        document_id="doc-1",
        document_name="Pitch Deck",
        document_type="PDF",
        uploaded_at=now_dt,
    )

    # 2. Evidence
    for i in range(evidence_count):
        ev_id = f"ev-{i}"
        graph.evidence[ev_id] = EvidenceNode(
            node_id=ev_id,
            node_type=NodeType.EVIDENCE,
            evidence_id=ev_id,
            excerpt="Excerpt",
            location="p.1",
            confidence=evidence_strength,
        )
        graph.edges.append(
            Edge(
                source_id=ev_id,
                source_type=NodeType.EVIDENCE,
                target_id="doc-1",
                target_type=NodeType.DOCUMENT,
                relationship="DERIVED_FROM",
            )
        )

    # 3. Claims
    graph.claims["claim-1"] = ClaimNode(
        node_id="claim-1",
        node_type=NodeType.CLAIM,
        claim_id="claim-1",
        claim_text="Detail",
    )

    # 4. Observations
    total_obs = 10
    corroborated_target = int(total_obs * overall_consensus)
    for i in range(total_obs):
        obs_id = f"obs-{i}"
        status = "corroborated" if i < corroborated_target else "independent"
        graph.observations[obs_id] = ObservationNode(
            node_id=obs_id,
            node_type=NodeType.OBSERVATION,
            observation_id=obs_id,
            domain="product",
            observation=f"Obs {i}",
            confidence=confidence,
            consensus_status=status,
        )
        graph.edges.append(
            Edge(
                source_id=obs_id,
                source_type=NodeType.OBSERVATION,
                target_id="claim-1",
                target_type=NodeType.CLAIM,
                relationship="SUPPORTED_BY",
            )
        )

    # 5. Risks
    for i in range(active_risks_count):
        r_id = f"risk-{i}"
        graph.risks[r_id] = RiskNode(
            node_id=r_id,
            node_type=NodeType.RISK,
            risk_id=r_id,
            category="technical",
            description=f"Risk {i}",
            confidence=0.7,
            reasoning="Reason",
        )

    # 6. Questions
    for i in range(question_count):
        q_id = f"qst-{i}"
        graph.questions[q_id] = QuestionNode(
            node_id=q_id,
            node_type=NodeType.QUESTION,
            question_id=q_id,
            question=f"Follow up {i}?",
            purpose="Audit",
        )

    # 7. Conflicts
    for i in range(unresolved_conflicts):
        conf_id = f"conf-{i}"
        graph.conflicts[conf_id] = ConflictNode(
            node_id=conf_id,
            node_type=NodeType.CONFLICT,
            conflict_id=conf_id,
            description=f"Conflict {i}",
            conflict_type="FACTUAL",
            confidence=0.8,
            created_at=now_dt,
        )

    # 8. Executive Assessment
    exec_summary = ExecutiveSummary(
        overview="Exec Overview",
        strengths=[],
        weaknesses=[],
        opportunities=[],
        threats=[],
        missing_information=[],
    )
    graph.executive_assessment = ExecutiveAssessment(
        node_id="exec-assessment",
        node_type=NodeType.EXECUTIVE,
        assessment_id="exec-assessment",
        generated_at=now_iso,
        summary=exec_summary,
        confidence=executive_confidence,
    )

    # 9. Investment Assessment
    if investment_score < 40:
        rec = InvestmentRecommendation.DO_NOT_INVEST
    elif investment_score < 55:
        rec = InvestmentRecommendation.REVIEW
    elif investment_score < 70:
        rec = InvestmentRecommendation.WATCHLIST
    elif investment_score < 85:
        rec = InvestmentRecommendation.INVEST
    else:
        rec = InvestmentRecommendation.STRONG_INVEST

    metrics = {
        "overall_consensus": overall_consensus,
        "evidence_strength": evidence_strength,
        "document_coverage": 1.0,
        "graph_confidence": confidence,
    }

    graph.investment_assessment = InvestmentAssessment(
        node_id="inv-assessment",
        node_type=NodeType.INVESTMENT,
        assessment_id="inv-assessment",
        generated_at=now_iso,
        recommendation=rec,
        confidence=confidence,
        investment_score=investment_score,
        readiness_score=80.0,
        risk_score=40.0,
        technology_score=75.0,
        market_score=75.0,
        founder_score=75.0,
        financial_score=75.0,
        competition_score=75.0,
        ip_score=75.0,
        executive_summary="Summary",
        strengths=[],
        weaknesses=[],
        major_risks=[],
        investment_rationale="Rationale",
        metadata={"metrics": metrics, "evaluation_mode": "MOCK_SIMULATED_OFFLINE"},
    )
    graph.investment_statistics = {
        "active_risks_count": active_risks_count,
        "overall_consensus": overall_consensus,
    }

    port_entry = PortfolioEntry(
        startup_id=startup_id,
        startup_name=name,
        category=category,
        rank=1,
        ranking_reason="Top performer",
        investment_assessment_id="inv-assessment",
        executive_summary_id="exec-assessment",
        overall_consensus=overall_consensus,
        graph_confidence=confidence,
        evidence_strength=evidence_strength,
        document_coverage=1.0,
        active_risk_count=active_risks_count,
        corroborated_observation_count=corroborated_target,
        disputed_observation_count=0,
        created_at=graph.created_at,
        investment_score=investment_score,
        recommendation=rec.value,
        confidence=confidence,
        percentile=100.0,
        strengths=[],
        risks=[],
        executive_summary="Summary",
        graph_hash="clean_hash",
    )
    object.__setattr__(port_entry, "portfolio_hash", "mock_portfolio_hash")
    graph.portfolio_entry = port_entry

    ObservationGraphBuilder._update_statistics(graph)
    graph.graph_hash = ObservationGraphBuilder._compute_hash(graph)
    port_entry.graph_hash = graph.graph_hash
    return graph
