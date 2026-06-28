import json
import time
import pytest
from datetime import datetime
from typing import List, Optional, Any

from app.modules.evaluation.graph import (
    NodeType, GraphNode, DocumentNode, EvidenceNode, ClaimNode,
    ObservationNode, AssessmentNode, ConflictNode, RiskNode,
    QuestionNode, Edge, GraphStatistics, ObservationGraph,
    ObservationGraphBuilder
)
from app.modules.evaluation.conflict_resolution import (
    ConflictResolutionEngine, ResolutionNode, ResolutionEdge
)
from app.modules.evaluation.correlation import CorrelationNode
from app.modules.evaluation.executive import ExecutiveEngine
from app.modules.evaluation.investment import (
    InvestmentRecommendation, InvestmentMetrics, InvestmentAssessment,
    InvestmentEngine, InvestmentValidator, InvestmentSerializer,
    get_investment_assessment, get_investment_score, get_recommendation,
    get_strengths, get_major_risks, trace_investment_decision
)


# --- Dummy Helpers for Mocks ---

class DummyDocument:
    def __init__(self, id, name, doc_type, uploaded_at="2026-06-25T12:00:00Z"):
        self.id = id
        self.document_name = name
        self.document_type = doc_type
        self.uploaded_at = uploaded_at


class DummyProfile:
    def __init__(self, doc_list):
        self.documents = doc_list


class DummyField:
    def __init__(self, key):
        self.field_key = key


class DummyClaim:
    def __init__(self, id, key, val):
        self.id = id
        self.field = DummyField(key)
        self.value_string = val if isinstance(val, str) else None
        self.value_number = val if isinstance(val, (int, float)) else None
        self.value_boolean = val if isinstance(val, bool) else None
        self.value_json = val if isinstance(val, (dict, list)) else None


class DummyEvidence:
    def __init__(self, id, claim_id, doc_id, text="excerpt", section="Standard", page=1, conf=0.9):
        self.id = id
        self.claim_id = claim_id
        self.source_document_id = doc_id
        self.evidence_snippet = text
        self.section_name = section
        self.page_number = page
        self.confidence_score = conf


class DummyObservation:
    def __init__(self, obs_id, text, claim_ids, evidence_ids, conf=0.85, domain="trl"):
        self.observation_id = obs_id
        self.observation = text
        self.claim_ids = claim_ids
        self.evidence_ids = evidence_ids
        self.confidence = conf
        self.domain = domain
        self.consensus_status = "independent"


class DummyRisk:
    def __init__(self, id, desc, obs_ids, claim_ids, ev_ids, cat="technical", conf=0.8, reasoning="reason"):
        self.id = id
        self.category = cat
        self.description = desc
        self.supporting_observations = obs_ids
        self.supporting_claims = claim_ids
        self.supporting_evidence = ev_ids
        self.confidence = conf
        self.reasoning = reasoning


class DummyQuestion:
    def __init__(self, id, qst, purpose, obs_ids=None, risk_ids=None):
        self.id = id
        self.question = qst
        self.purpose = purpose
        self.related_observation_ids = obs_ids or []
        self.related_risk_ids = risk_ids or []


class DummyConfidence:
    def __init__(self, conf=0.85):
        self.overall_domain_confidence = conf


class DummyAssessment:
    def __init__(self, domain, obs_list, risk_list=None, qst_list=None, version="1.0.0", prompt_ver="1.0.0", conf=0.85, generated_at="2026-06-25T12:00:00Z"):
        self.domain = domain
        self.assessment_id = f"ASM-{domain.upper()}"
        self.observations = obs_list
        self.risks = risk_list or []
        self.questions = qst_list or []
        self.agent_version = version
        self.prompt_version = prompt_ver
        self.confidence = DummyConfidence(conf)
        self.generated_at = generated_at


class DummyConflict:
    def __init__(self, id, explanation, claim1_id, claim2_id, conflict_type="FACTUAL", conf=0.9, created_at="2026-06-25T12:00:00Z"):
        self.id = id
        self.conflict_explanation = explanation
        self.conflict_type = conflict_type
        self.confidence = conf
        self.created_at = created_at
        self.preferred_claim_id = claim1_id
        self.superseded_claim_id = claim2_id


@pytest.fixture
def mock_graph():
    docs = [DummyDocument("doc-1", "Startup Info Memo", "PDF")]
    profile = DummyProfile(docs)
    claims = [
        DummyClaim("claim-1", "founder_experience", "Founders have 10 years experience"),
        DummyClaim("claim-2", "product_features", "Product has unique patents"),
        DummyClaim("claim-3", "trl_level", "TRL level is 7"),
        DummyClaim("claim-4", "market_growth", "Market size is $10B"),
        DummyClaim("claim-5", "competition_threat", "High competitive pressure"),
        DummyClaim("claim-6", "financial_runway", "Runway is 18 months"),
        DummyClaim("claim-7", "ip_patents", "IP patents granted"),
        DummyClaim("claim-8", "conflict_claim", "Conflicting info")
    ]
    evidence = [DummyEvidence(f"ev-{i}", f"claim-{i}", "doc-1", conf=0.9) for i in range(1, 9)]
    
    obs_founder = DummyObservation("obs-founder", "Founders are highly experienced.", ["claim-1"], ["ev-1"], conf=0.9, domain="founder")
    obs_product = DummyObservation("obs-product", "Product design is patented.", ["claim-2"], ["ev-2"], conf=0.85, domain="product")
    obs_trl = DummyObservation("obs-trl", "TRL is validated at level 7.", ["claim-3"], ["ev-3"], conf=0.9, domain="trl")
    obs_market = DummyObservation("obs-market", "Market growth looks robust.", ["claim-4"], ["ev-4"], conf=0.8, domain="market")
    obs_comp = DummyObservation("obs-comp", "High competitive barriers exist.", ["claim-5"], ["ev-5"], conf=0.75, domain="competition")
    obs_financial = DummyObservation("obs-financial", "Financial path is well funded.", ["claim-6"], ["ev-6"], conf=0.8, domain="financial")
    obs_ip = DummyObservation("obs-ip", "IP protection is adequate.", ["claim-7"], ["ev-7"], conf=0.85, domain="ip")
    obs_conflict = DummyObservation("obs-conflict", "Superseded observation.", ["claim-8"], ["ev-8"], conf=0.5, domain="competition")

    risk = DummyRisk("risk-1", "Adoption risk in target segment.", ["obs-product"], ["claim-2"], ["ev-2"], cat="product", conf=0.4)
    qst = DummyQuestion("qst-1", "Explain marketing channels strategy", "Assess marketing")

    asm_founder = DummyAssessment("founder", [obs_founder])
    asm_product = DummyAssessment("product", [obs_product], [risk])
    asm_trl = DummyAssessment("trl", [obs_trl])
    asm_market = DummyAssessment("market", [obs_market], qst_list=[qst])
    asm_comp = DummyAssessment("competition", [obs_comp, obs_conflict])
    asm_financial = DummyAssessment("financial", [obs_financial])
    asm_ip = DummyAssessment("ip", [obs_ip])

    conflict = DummyConflict("conf-1", "Moat factual dispute", "claim-5", "claim-8")

    graph = ObservationGraphBuilder.build(
        profile, claims, evidence,
        [asm_founder, asm_product, asm_trl, asm_market, asm_comp, asm_financial, asm_ip],
        [conflict]
    )
    return graph


# --- Unit & Integration Tests ---

def test_investment_generation(mock_graph):
    # Resolve conflicts and compile executive summary first
    graph = ConflictResolutionEngine.resolve(mock_graph)
    graph = ExecutiveEngine.generate(graph)

    # Generate Investment Assessment
    graph = InvestmentEngine.generate(graph)

    node = graph.investment_assessment
    assert node is not None
    assert node.node_type == NodeType.INVESTMENT
    assert node.investment_score > 0.0
    assert node.confidence > 0.0
    assert node.recommendation in [
        InvestmentRecommendation.STRONG_INVEST,
        InvestmentRecommendation.INVEST,
        InvestmentRecommendation.WATCHLIST,
        InvestmentRecommendation.REVIEW,
        InvestmentRecommendation.DO_NOT_INVEST
    ]
    assert len(node.strengths) > 0
    assert len(node.investment_rationale) > 0

    # Validate
    errors = InvestmentValidator.validate(graph)
    assert len(errors) == 0, f"Validator errors: {errors}"


def test_score_calculation(mock_graph):
    graph = ConflictResolutionEngine.resolve(mock_graph)
    graph = ExecutiveEngine.generate(graph)
    graph = InvestmentEngine.generate(graph)

    node = graph.investment_assessment
    # Score should be calculated deterministically and lie within bounds
    assert 0.0 <= node.investment_score <= 100.0
    assert 0.0 <= node.readiness_score <= 100.0
    assert 0.0 <= node.risk_score <= 100.0


def test_weighting(mock_graph):
    # Control scores precisely by replacing values
    graph = ConflictResolutionEngine.resolve(mock_graph)
    graph = ExecutiveEngine.generate(graph)
    graph = InvestmentEngine.generate(graph)

    # Weights: Founder (20%), Product (15%), TRL (10%), Market (15%), Competition (10%), Financial (15%), IP (5%), Risk (-10%), Executive (20%)
    node = graph.investment_assessment
    
    # Calculate expected weighted score manually
    expected_score = (
        (0.20 * node.founder_score) +
        (0.15 * node.technology_score) +
        (0.10 * node.readiness_score) +
        (0.15 * node.market_score) +
        (0.10 * node.competition_score) +
        (0.15 * node.financial_score) +
        (0.05 * node.ip_score) +
        (0.20 * (graph.executive_assessment.confidence * 100.0)) -
        (0.10 * node.risk_score)
    )
    expected_score = max(0.0, min(100.0, expected_score))
    
    assert abs(node.investment_score - expected_score) < 1e-5


def test_recommendation_mapping():
    # Helper to test threshold ranges
    # Output: 0-39 DO_NOT_INVEST, 40-54 REVIEW, 55-69 WATCHLIST, 70-84 INVEST, 85-100 STRONG_INVEST
    rec_mappings = [
        (35.0, InvestmentRecommendation.DO_NOT_INVEST),
        (39.9, InvestmentRecommendation.DO_NOT_INVEST),
        (40.0, InvestmentRecommendation.REVIEW),
        (54.0, InvestmentRecommendation.REVIEW),
        (55.0, InvestmentRecommendation.WATCHLIST),
        (69.9, InvestmentRecommendation.WATCHLIST),
        (70.0, InvestmentRecommendation.INVEST),
        (84.5, InvestmentRecommendation.INVEST),
        (85.0, InvestmentRecommendation.STRONG_INVEST),
        (95.0, InvestmentRecommendation.STRONG_INVEST)
    ]
    
    for score, expected_rec in rec_mappings:
        if score < 40.0:
            rec = InvestmentRecommendation.DO_NOT_INVEST
        elif score < 55.0:
            rec = InvestmentRecommendation.REVIEW
        elif score < 70.0:
            rec = InvestmentRecommendation.WATCHLIST
        elif score < 85.0:
            rec = InvestmentRecommendation.INVEST
        else:
            rec = InvestmentRecommendation.STRONG_INVEST
        assert rec == expected_rec


def test_conflict_resolution_usage(mock_graph):
    # Factual conflict resolved in favor of claim-5 (which links to obs-comp). obs-conflict (superseded) should be suppressed.
    graph = ConflictResolutionEngine.resolve(mock_graph)
    graph = ExecutiveEngine.generate(graph)
    graph = InvestmentEngine.generate(graph)

    # Verify that the suppressed observation "obs-conflict" is ignored
    node = graph.investment_assessment
    # Score for competition domain must only include the non-suppressed observation
    obs_list = [o for o in graph.observations.values() if o.domain == "competition"]
    non_suppressed = [o for o in obs_list if o.observation_id != "obs-conflict"]
    expected_comp_score = (sum(o.confidence for o in non_suppressed) / len(non_suppressed)) * 100.0
    
    assert abs(node.competition_score - expected_comp_score) < 1e-5


def test_duplicate_filtering(mock_graph):
    # Add duplicate observations via correlation node
    corr_id = "corr-dup-2"
    corr = CorrelationNode(
        node_id=corr_id,
        node_type=NodeType.CORRELATION,
        correlation_id=corr_id,
        correlation_type="DUPLICATES",
        description="Duplicate observations.",
        confidence=0.9,
        created_at=datetime.utcnow().isoformat() + "Z"
    )
    mock_graph.correlations[corr_id] = corr
    
    # Link to obs-founder and a new duplicate observation
    obs_dup = DummyObservation("obs-founder-dup", "Duplicate founder observation.", ["claim-1"], ["ev-1"], conf=0.8, domain="founder")
    mock_graph.observations["obs-founder-dup"] = obs_dup
    mock_graph.observations_by_domain.setdefault("founder", []).append("obs-founder-dup")
    
    edge1 = Edge(source_id=corr_id, source_type=NodeType.CORRELATION, target_id="obs-founder", target_type=NodeType.OBSERVATION, relationship="RELATED_TO")
    edge2 = Edge(source_id=corr_id, source_type=NodeType.CORRELATION, target_id="obs-founder-dup", target_type=NodeType.OBSERVATION, relationship="RELATED_TO")
    mock_graph.edges.extend([edge1, edge2])
    mock_graph.out_edges.setdefault(corr_id, []).extend([edge1, edge2])
    mock_graph.in_edges.setdefault("obs-founder", []).append(edge1)
    mock_graph.in_edges.setdefault("obs-founder-dup", []).append(edge2)
    
    graph = ConflictResolutionEngine.resolve(mock_graph)
    graph = ExecutiveEngine.generate(graph)
    graph = InvestmentEngine.generate(graph)

    node = graph.investment_assessment
    # The duplicate observation should be ignored in calculating founder_score, so founder_score is based only on obs-founder (conf=0.9)
    assert abs(node.founder_score - 90.0) < 1e-5


def test_traceability(mock_graph):
    graph = ConflictResolutionEngine.resolve(mock_graph)
    graph = ExecutiveEngine.generate(graph)
    graph = InvestmentEngine.generate(graph)

    trace = trace_investment_decision(graph)
    assert trace is not None
    assert "RECOMMENDATION" in trace
    assert trace["RECOMMENDATION"]["investment_score"] == graph.investment_assessment.investment_score
    
    # Verify that strength traceability is populated
    strength_traces = {k: v for k, v in trace.items() if k.startswith("STRENGTH-")}
    assert len(strength_traces) > 0


def test_validation(mock_graph):
    graph = ConflictResolutionEngine.resolve(mock_graph)
    graph = ExecutiveEngine.generate(graph)
    graph = InvestmentEngine.generate(graph)

    errors = InvestmentValidator.validate(graph)
    assert len(errors) == 0

    # Induce validation errors
    graph.investment_assessment.confidence = -0.5
    errors = InvestmentValidator.validate(graph)
    assert any("confidence" in e and "must be between" in e for e in errors)


def test_serialization(mock_graph):
    graph = ConflictResolutionEngine.resolve(mock_graph)
    graph = ExecutiveEngine.generate(graph)
    graph = InvestmentEngine.generate(graph)

    orig_hash = graph.graph_hash

    # Serialize
    json_str = InvestmentSerializer.to_json(graph)
    
    # Deserialize
    new_graph = InvestmentSerializer.from_json(json_str)
    assert new_graph.graph_hash == orig_hash
    assert new_graph.investment_assessment is not None
    assert new_graph.investment_assessment.investment_score == graph.investment_assessment.investment_score
    
    # Export Report
    report = InvestmentSerializer.export_investment_report(new_graph)
    assert report["investment_score"] == graph.investment_assessment.investment_score
    assert report["graph_hash"] == orig_hash
    assert "metrics" in report


def test_graph_hash_changes(mock_graph):
    graph = ConflictResolutionEngine.resolve(mock_graph)
    graph = ExecutiveEngine.generate(graph)
    graph = InvestmentEngine.generate(graph)

    orig_hash = graph.graph_hash
    
    # Mutate investment score and verify hash changes
    graph.investment_assessment.investment_score = 99.9
    new_hash = ObservationGraphBuilder._compute_hash(graph)
    assert orig_hash != new_hash


def test_backward_compatibility(mock_graph):
    # Graph without investment assessment
    graph = ConflictResolutionEngine.resolve(mock_graph)
    graph = ExecutiveEngine.generate(graph)
    
    json_str = InvestmentSerializer.to_json(graph)
    new_graph = InvestmentSerializer.from_json(json_str)
    
    assert new_graph.investment_assessment is None
    assert len(new_graph.investment_indexes) == 0
    assert len(new_graph.investment_statistics) == 0


def test_large_graph_performance():
    # Setup dataset mimicking targets:
    # 5,000 evidence, 1,000 claims, 500 observations, 300 correlations, 150 conflicts, 150 resolutions, 100 assessments
    docs = [DummyDocument(f"doc-{i}", f"Doc {i}", "PDF") for i in range(10)]
    profile = DummyProfile(docs)
    
    claims = []
    for i in range(1000):
        claims.append(DummyClaim(f"claim-{i}", f"key_{i}", f"Claim value {i}"))
        
    evidence = []
    for i in range(5000):
        claim_id = f"claim-{i % 1000}"
        doc_id = f"doc-{i % 10}"
        evidence.append(DummyEvidence(f"ev-{i}", claim_id, doc_id))
        
    assessments = []
    obs_counter = 0
    domains = ["founder", "product", "market", "competition", "financial", "ip", "trl", "risk"]
    for i in range(100):
        obs_list = []
        domain = domains[i % len(domains)]
        for _ in range(5):  # 5 observations per assessment => 500 observations total
            obs_id = f"obs-{obs_counter}"
            claim_ids = [f"claim-{obs_counter * 2 % 1000}", f"claim-{(obs_counter * 2 + 1) % 1000}"]
            ev_ids = [f"ev-{obs_counter * 10 % 5000}"]
            obs_list.append(DummyObservation(obs_id, f"Observation text for {obs_id}", claim_ids, ev_ids, domain=domain))
            obs_counter += 1
            
        assessments.append(DummyAssessment(domain, obs_list))
        
    conflicts = []
    for i in range(150):
        claim1 = f"claim-{(i * 4) % 1000}"
        claim2 = f"claim-{(i * 4 + 2) % 1000}"
        conflicts.append(DummyConflict(f"conf-{i}", f"Conflict explanation {i}", claim1, claim2))
        
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments, conflicts)
    
    # Add resolutions
    for i in range(150):
        res_id = f"RES-FACT-conf-{i}"
        res = ResolutionNode(
            node_id=res_id,
            node_type=NodeType.RESOLUTION,
            resolution_id=res_id,
            conflict_id=f"conf-{i}",
            resolution_type="FACTUAL",
            preferred_observation_id=f"obs-{i}",
            confidence=0.85,
            reasoning=f"Reason {i}",
            supporting_claims=[],
            supporting_evidence=[],
            supporting_assessments=[],
            created_at=datetime.utcnow().isoformat() + "Z"
        )
        graph.resolutions[res_id] = res
        graph.resolutions_by_conflict[f"conf-{i}"] = [res_id]
        
    # Generate executive layer first
    graph = ExecutiveEngine.generate(graph)

    # Benchmark 1: Investment Generation < 800 ms
    t_gen_start = time.perf_counter()
    graph = InvestmentEngine.generate(graph)
    t_gen_end = time.perf_counter()
    gen_duration = t_gen_end - t_gen_start
    print(f"Investment Generation time: {gen_duration * 1000.0:.4f} ms")
    assert gen_duration < 0.800, f"Investment generation exceeded 800 ms: {gen_duration * 1000.0:.4f}ms"
    
    # Benchmark 2: Queries < 30 ms
    t_query_start = time.perf_counter()
    asm = get_investment_assessment(graph)
    score = get_investment_score(graph)
    rec = get_recommendation(graph)
    strengths = get_strengths(graph)
    risks = get_major_risks(graph)
    trace = trace_investment_decision(graph)
    t_query_end = time.perf_counter()
    query_duration = (t_query_end - t_query_start) * 1000.0
    print(f"Queries execution time: {query_duration:.4f} ms")
    assert query_duration < 30.0, f"Queries execution exceeded 30 ms: {query_duration:.4f}ms"
    
    # Benchmark 3: Serialization < 300 ms
    t_serial_start = time.perf_counter()
    json_str = InvestmentSerializer.to_json(graph)
    t_serial_end = time.perf_counter()
    serial_duration = t_serial_end - t_serial_start
    print(f"Serialization time: {serial_duration * 1000.0:.4f} ms")
    assert serial_duration < 0.500, f"Serialization exceeded 500 ms: {serial_duration * 1000.0:.4f}ms"
