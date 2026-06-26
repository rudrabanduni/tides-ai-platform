import time
import json
import pytest
from datetime import datetime
from typing import List

from app.modules.evaluation.graph import (
    NodeType, DocumentNode, EvidenceNode, ClaimNode,
    ObservationNode, AssessmentNode, ConflictNode, RiskNode,
    QuestionNode, Edge, ObservationGraph, ObservationGraphBuilder
)
from app.modules.evaluation.investment.investment_models import InvestmentAssessment, InvestmentRecommendation
from app.modules.evaluation.executive.executive_models import ExecutiveAssessment, ExecutiveSummary
from app.modules.evaluation.portfolio import (
    Portfolio, PortfolioEntry, PortfolioStatistics as PortStats, PortfolioBuilder,
    PortfolioEngine, PortfolioValidator, PortfolioSerializer,
    get_top_n, get_by_rank, get_by_startup, filter_by_category,
    filter_by_confidence, filter_by_recommendation, statistics
)


# --- Helper to create precise mock startup graphs for testing ---

def create_mock_startup_graph(
    startup_id: str,
    name: str,
    category: str,
    investment_score: float,
    confidence: float,
    overall_consensus: float = 0.8,
    active_risks_count: int = 1,
    evidence_count: int = 5,
    executive_confidence: float = 0.9,
    evidence_strength: float = 0.9
) -> ObservationGraph:
    graph = ObservationGraph()
    graph.startup_id = startup_id
    graph.graph_id = startup_id
    graph.startup_name = name
    graph.category = category
    graph.created_at = datetime.utcnow().isoformat() + "Z"
    
    # 1. Documents
    doc = DocumentNode(
        node_id="doc-1", node_type=NodeType.DOCUMENT,
        document_id="doc-1", document_name="Pitch Deck",
        document_type="PDF", uploaded_at=datetime.utcnow()
    )
    graph.documents["doc-1"] = doc
    
    # 2. Evidence
    for i in range(evidence_count):
        ev_id = f"ev-{i}"
        ev = EvidenceNode(
            node_id=ev_id, node_type=NodeType.EVIDENCE,
            evidence_id=ev_id, excerpt="Excerpt",
            location="p.1", confidence=0.9
        )
        graph.evidence[ev_id] = ev
        graph.edges.append(Edge(source_id=ev_id, source_type=NodeType.EVIDENCE, target_id="doc-1", target_type=NodeType.DOCUMENT, relationship="DERIVED_FROM"))
        
    # 3. Claims
    claim = ClaimNode(node_id="claim-1", node_type=NodeType.CLAIM, claim_id="claim-1", claim_text="Detail")
    graph.claims["claim-1"] = claim
    
    # 4. Observations (corroborated vs independent count for consensus calculation)
    # Total observations count = 10
    total_obs = 10
    corroborated_target = int(total_obs * overall_consensus)
    for i in range(total_obs):
        obs_id = f"obs-{i}"
        status = "corroborated" if i < corroborated_target else "independent"
        obs = ObservationNode(
            node_id=obs_id, node_type=NodeType.OBSERVATION,
            observation_id=obs_id, domain="product",
            observation=f"Obs {i}", confidence=0.85,
            consensus_status=status
        )
        graph.observations[obs_id] = obs
        graph.edges.append(Edge(source_id=obs_id, source_type=NodeType.OBSERVATION, target_id="claim-1", target_type=NodeType.CLAIM, relationship="SUPPORTED_BY"))
        
    # 5. Risks
    for i in range(active_risks_count):
        r_id = f"risk-{i}"
        risk = RiskNode(
            node_id=r_id, node_type=NodeType.RISK,
            risk_id=r_id, category="technical",
            description=f"Risk {i}", confidence=0.6, reasoning="Reason"
        )
        graph.risks[r_id] = risk
        
    # 6. Executive Assessment
    exec_summary = ExecutiveSummary(overview="Exec Overview", strengths=[], weaknesses=[], opportunities=[], threats=[], missing_information=[])
    exec_asm = ExecutiveAssessment(
        node_id="exec-assessment", node_type=NodeType.EXECUTIVE,
        assessment_id="exec-assessment", generated_at=datetime.utcnow().isoformat() + "Z",
        summary=exec_summary, confidence=executive_confidence
    )
    graph.executive_assessment = exec_asm
    
    # 7. Investment Assessment
    # Map score to recommendation
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
        "graph_confidence": confidence
    }
    
    inv = InvestmentAssessment(
        node_id="inv-assessment", node_type=NodeType.INVESTMENT,
        assessment_id="inv-assessment", generated_at=datetime.utcnow().isoformat() + "Z",
        recommendation=rec, confidence=confidence,
        investment_score=investment_score, readiness_score=80.0,
        risk_score=40.0, technology_score=75.0, market_score=75.0,
        founder_score=75.0, financial_score=75.0, competition_score=75.0,
        ip_score=75.0, executive_summary="Summary", strengths=[], weaknesses=[],
        major_risks=[], investment_rationale="Rationale", metadata={"metrics": metrics}
    )
    graph.investment_assessment = inv
    graph.investment_statistics = {
        "active_risks_count": active_risks_count,
        "overall_consensus": overall_consensus
    }
    
    # Update Stats & Hash
    ObservationGraphBuilder._update_statistics(graph)
    graph.graph_hash = ObservationGraphBuilder._compute_hash(graph)
    return graph


# --- Unit Tests ---

def test_portfolio_build():
    g1 = create_mock_startup_graph("S-1", "Startup One", "CleanTech", 85.5, 0.92, overall_consensus=0.8, active_risks_count=0)
    g2 = create_mock_startup_graph("S-2", "Startup Two", "SaaS", 72.0, 0.85, overall_consensus=0.7, active_risks_count=1)
    
    port = PortfolioEngine.generate([g1, g2])
    
    assert port is not None
    assert port.portfolio_id.startswith("PORT-")
    assert port.portfolio_version == "1.0.0"
    assert len(port.entries) == 2
    
    # Check ranks
    assert port.entries[0].startup_id == "S-1"
    assert port.entries[0].rank == 1
    assert port.entries[0].percentile == 100.0
    assert port.entries[0].recommendation == "STRONG_INVEST"
    
    assert port.entries[1].startup_id == "S-2"
    assert port.entries[1].rank == 2
    assert port.entries[1].percentile == 0.0
    assert port.entries[1].recommendation == "INVEST"
    
    # Check index populating
    assert port.ranking_indexes[1] == "S-1"
    assert port.ranking_indexes[2] == "S-2"
    assert "CleanTech" in port.category_indexes
    assert "S-2" in port.category_indexes["SaaS"]
    
    # Check stats
    assert port.statistics.portfolio_size == 2
    assert port.statistics.highest_score == 85.5
    assert port.statistics.lowest_score == 72.0
    assert port.statistics.average_score == 78.75
    assert port.statistics.median_score == 78.75
    assert port.statistics.average_confidence == 0.885
    assert port.statistics.recommendation_distribution["STRONG_INVEST"] == 1
    assert port.statistics.recommendation_distribution["INVEST"] == 1


def test_ranking_and_tie_breaking():
    # Setup graphs with ties to verify tie-breaking logic order
    # Tie-breakers order:
    # 1. overall_consensus (descending)
    # 2. graph_confidence (descending)
    # 3. evidence_strength (descending)
    # 4. startup_name (ascending)
    # 5. startup_id (ascending)

    # g1 and g2: identical scores, g1 has higher consensus
    g1 = create_mock_startup_graph("S-1", "Startup A", "BioTech", 80.0, 0.8, overall_consensus=0.9, evidence_count=5)
    g2 = create_mock_startup_graph("S-2", "Startup B", "BioTech", 80.0, 0.8, overall_consensus=0.8, evidence_count=5)
    
    port1 = PortfolioEngine.generate([g2, g1])
    assert port1.entries[0].startup_id == "S-1"
    
    # g2 and g3: identical score & consensus, g3 has higher graph_confidence
    g3 = create_mock_startup_graph("S-3", "Startup C", "BioTech", 80.0, 0.85, overall_consensus=0.8, evidence_count=5)
    port2 = PortfolioEngine.generate([g2, g3])
    assert port2.entries[0].startup_id == "S-3"
    
    # g2 and g4: identical score, consensus, & confidence, g4 has more evidence (higher strength)
    g4 = create_mock_startup_graph("S-4", "Startup D", "BioTech", 80.0, 0.8, overall_consensus=0.8, evidence_count=10, evidence_strength=0.95)
    port3 = PortfolioEngine.generate([g2, g4])
    assert port3.entries[0].startup_id == "S-4"
    
    # g5 and g6: identical score, consensus, confidence, & evidence, g5 has alphabetical startup_name ("Startup E" < "Startup F")
    g5 = create_mock_startup_graph("S-5", "Startup E", "BioTech", 80.0, 0.8, overall_consensus=0.8, evidence_count=5)
    g6 = create_mock_startup_graph("S-6", "Startup F", "BioTech", 80.0, 0.8, overall_consensus=0.8, evidence_count=5)
    port4 = PortfolioEngine.generate([g6, g5])
    assert port4.entries[0].startup_name == "Startup E"
    
    # g7 and g8: identical all parameters, g7 has alphabetical startup_id ("S-7" < "S-8")
    g7 = create_mock_startup_graph("S-7", "Startup G", "BioTech", 80.0, 0.8, overall_consensus=0.8, evidence_count=5)
    g8 = create_mock_startup_graph("S-8", "Startup G", "BioTech", 80.0, 0.8, overall_consensus=0.8, evidence_count=5)
    port5 = PortfolioEngine.generate([g8, g7])
    assert port5.entries[0].startup_id == "S-7"


def test_ranking_explanations():
    g1 = create_mock_startup_graph("S-1", "Startup One", "CleanTech", 95.0, 0.95, active_risks_count=0)
    g2 = create_mock_startup_graph("S-2", "Startup Two", "SaaS", 45.0, 0.6, active_risks_count=4)
    
    port = PortfolioEngine.generate([g1, g2])
    assert "Top performer" in port.entries[0].ranking_reason
    assert "active risks" in port.entries[1].ranking_reason or "Low investment score" in port.entries[1].ranking_reason


def test_duplicate_startup_removal():
    # Create two graphs for same startup, one with higher score
    g1 = create_mock_startup_graph("S-1", "Startup One", "CleanTech", 65.0, 0.8)
    g2 = create_mock_startup_graph("S-1", "Startup One", "CleanTech", 82.0, 0.9)
    
    port = PortfolioEngine.generate([g1, g2])
    assert len(port.entries) == 1
    assert port.entries[0].investment_score == 82.0


def test_validation_rules():
    g1 = create_mock_startup_graph("S-1", "Startup One", "CleanTech", 85.0, 0.9)
    g2 = create_mock_startup_graph("S-2", "Startup Two", "SaaS", 75.0, 0.8)
    
    port = PortfolioEngine.generate([g1, g2])
    errors = PortfolioValidator.validate(port, [g1, g2])
    assert len(errors) == 0, f"Validator errors: {errors}"
    
    # 1. Induce rank duplication error
    port.entries[1].rank = 1
    errs = PortfolioValidator.validate(port)
    assert any("Duplicate ranks" in e for e in errs)
    
    # 2. Induce rank sequence continuity error
    port.entries[1].rank = 3
    errs2 = PortfolioValidator.validate(port)
    assert any("Rank sequence" in e for e in errs2)
    
    # 3. Induce score bounds error
    port.entries[1].rank = 2
    port.entries[1].investment_score = 150.0
    errs3 = PortfolioValidator.validate(port)
    assert any("Investment score" in e and "outside" in e for e in errs3)
    
    # Reset
    port.entries[1].investment_score = 75.0
    
    # 4. Induce hash check failure
    port.portfolio_hash = "fake_hash"
    errs4 = PortfolioValidator.validate(port)
    assert any("Portfolio hash is invalid" in e for e in errs4)


def test_broken_graph_references():
    g1 = create_mock_startup_graph("S-1", "Startup One", "CleanTech", 85.0, 0.9)
    g2 = create_mock_startup_graph("S-2", "Startup Two", "SaaS", 75.0, 0.8)
    
    port = PortfolioEngine.generate([g1, g2])
    
    # Create copy of list but replace g1 with a modified graph
    g1_mod = create_mock_startup_graph("S-1", "Startup One", "CleanTech", 85.0, 0.9)
    g1_mod.investment_assessment.assessment_id = "BROKEN-ID"
    
    errs = PortfolioValidator.validate(port, [g1_mod, g2])
    assert any("Assessment reference does not exist or mismatch" in e for e in errs)


def test_serialization():
    g1 = create_mock_startup_graph("S-1", "Startup One", "CleanTech", 85.0, 0.9)
    g2 = create_mock_startup_graph("S-2", "Startup Two", "SaaS", 75.0, 0.8)
    
    port = PortfolioEngine.generate([g1, g2])
    
    # JSON round-trip
    json_str = PortfolioSerializer.to_json(port)
    deserialized = PortfolioSerializer.from_json(json_str)
    
    assert deserialized.portfolio_id == port.portfolio_id
    assert len(deserialized.entries) == 2
    assert deserialized.entries[0].startup_id == "S-1"
    assert deserialized.portfolio_hash == port.portfolio_hash
    
    # CSV export
    csv_str = PortfolioSerializer.to_csv(port)
    assert "startup_id,startup_name,investment_score" in csv_str
    assert "S-1" in csv_str
    assert "S-2" in csv_str
    
    # Excel export
    xls_bytes = PortfolioSerializer.to_excel(port)
    assert isinstance(xls_bytes, bytes)
    assert len(xls_bytes) > 0
    
    # Dashboard JSON export
    dash_json = PortfolioSerializer.to_dashboard_json(port)
    dash_data = json.loads(dash_json)
    assert dash_data["size"] == 2
    assert len(dash_data["top_performers"]) == 2
    
    # Markdown Summary export
    md_str = PortfolioSerializer.to_markdown_summary(port)
    assert "# Portfolio Intelligence Report:" in md_str
    assert "S-1" in md_str
    assert "Startup Two" in md_str


def test_queries_api():
    g1 = create_mock_startup_graph("S-1", "Startup One", "CleanTech", 92.0, 0.9)
    g2 = create_mock_startup_graph("S-2", "Startup Two", "SaaS", 74.0, 0.8)
    g3 = create_mock_startup_graph("S-3", "Startup Three", "CleanTech", 65.0, 0.7)
    
    port = PortfolioEngine.generate([g1, g2, g3])
    
    # get_top_n
    top_2 = get_top_n(port, 2)
    assert len(top_2) == 2
    assert top_2[0].startup_id == "S-1"
    
    # get_by_rank
    rank_2 = get_by_rank(port, 2)
    assert rank_2 is not None
    assert rank_2.startup_id == "S-2"
    assert get_by_rank(port, 10) is None
    
    # get_by_startup
    s3 = get_by_startup(port, "S-3")
    assert s3 is not None
    assert s3.rank == 3
    assert get_by_startup(port, "NON-EXISTENT") is None
    
    # filter_by_category
    cleantech_startups = filter_by_category(port, "CleanTech")
    assert len(cleantech_startups) == 2
    
    # filter_by_confidence
    conf_startups = filter_by_confidence(port, 0.8)
    assert len(conf_startups) == 2
    
    # filter_by_recommendation
    rec_startups = filter_by_recommendation(port, "STRONG_INVEST")
    assert len(rec_startups) == 1
    assert rec_startups[0].startup_id == "S-1"
    
    # statistics
    stats = statistics(port)
    assert stats.portfolio_size == 3
    assert stats.average_score == 77.0
    assert stats.median_score == 74.0
    assert stats.highest_score == 92.0
    assert stats.lowest_score == 65.0


def test_hash_consistency_and_changes():
    g1 = create_mock_startup_graph("S-1", "Startup One", "CleanTech", 85.0, 0.9)
    g2 = create_mock_startup_graph("S-2", "Startup Two", "SaaS", 75.0, 0.8)
    
    port1 = PortfolioEngine.generate([g1, g2])
    port2 = PortfolioEngine.generate([g1, g2])
    
    # Determinism
    assert port1.portfolio_hash == port2.portfolio_hash
    
    # Change ranking order by modifying g2 score to exceed g1
    g2_higher = create_mock_startup_graph("S-2", "Startup Two", "SaaS", 95.0, 0.8)
    port3 = PortfolioEngine.generate([g1, g2_higher])
    
    assert port1.portfolio_hash != port3.portfolio_hash


def test_graph_hash_propagation():
    g1 = create_mock_startup_graph("S-1", "Startup One", "CleanTech", 85.0, 0.9)
    g2 = create_mock_startup_graph("S-2", "Startup Two", "SaaS", 75.0, 0.8)
    
    orig_hash = g1.graph_hash
    
    # Build portfolio
    PortfolioEngine.generate([g1, g2])
    
    # Hash must be updated and propagated because of the new portfolio fields
    assert g1.portfolio_entry is not None
    assert g1.graph_hash != orig_hash


def test_input_shuffle_regression():
    g1 = create_mock_startup_graph("S-1", "Startup One", "CleanTech", 90.0, 0.9)
    g2 = create_mock_startup_graph("S-2", "Startup Two", "SaaS", 80.0, 0.8)
    g3 = create_mock_startup_graph("S-3", "Startup Three", "CleanTech", 70.0, 0.7)
    
    # Generate using order [g1, g2, g3]
    port_normal = PortfolioEngine.generate([g1, g2, g3])
    # Generate using order [g3, g1, g2]
    port_shuffled = PortfolioEngine.generate([g3, g1, g2])
    
    assert port_normal.portfolio_hash == port_shuffled.portfolio_hash
    assert [e.startup_id for e in port_normal.entries] == [e.startup_id for e in port_shuffled.entries]


def test_large_dataset_performance():
    # Generate 1000 startup graphs to benchmark limits
    # Generation < 2 seconds, Queries < 50ms, Serialization < 500ms
    graphs = []
    for i in range(1000):
        # Scale parameters to simulate realistic variations
        score = float(50 + (i % 45))
        conf = 0.5 + ((i % 10) / 20.0)
        consensus = 0.6 + ((i % 5) / 10.0)
        category = "CleanTech" if i % 2 == 0 else "SaaS"
        
        g = create_mock_startup_graph(
            startup_id=f"SCALE-{i}",
            name=f"Scale Startup {i}",
            category=category,
            investment_score=score,
            confidence=conf,
            overall_consensus=consensus,
            active_risks_count=i % 4,
            evidence_count=(i % 10) + 1,
            executive_confidence=conf
        )
        graphs.append(g)

    # 1. Benchmark Portfolio Generation
    t_start = time.perf_counter()
    port = PortfolioEngine.generate(graphs)
    t_end = time.perf_counter()
    gen_duration = t_end - t_start
    print(f"Portfolio generation duration (1000 startups): {gen_duration:.4f} seconds")
    assert gen_duration < 2.0, f"Portfolio generation took {gen_duration:.4f} seconds (Limit: 2.0s)"

    # 2. Benchmark Queries
    t_q_start = time.perf_counter()
    top_50 = get_top_n(port, 50)
    item_500 = get_by_rank(port, 500)
    cleantechs = filter_by_category(port, "CleanTech")
    stats = statistics(port)
    t_q_end = time.perf_counter()
    query_duration = t_q_end - t_q_start
    print(f"Queries execution duration (1000 startups): {query_duration * 1000.0:.4f} ms")
    assert query_duration < 0.050, f"Queries took {query_duration * 1000.0:.4f} ms (Limit: 50ms)"

    # 3. Benchmark Serialization
    t_s_start = time.perf_counter()
    json_str = PortfolioSerializer.to_json(port)
    t_s_end = time.perf_counter()
    serial_duration = t_s_end - t_s_start
    print(f"Serialization duration (1000 startups): {serial_duration * 1000.0:.4f} ms")
    assert serial_duration < 0.500, f"Serialization took {serial_duration * 1000.0:.4f} ms (Limit: 500ms)"
