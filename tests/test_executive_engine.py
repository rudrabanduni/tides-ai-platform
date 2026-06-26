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
from app.modules.evaluation.executive import (
    ExecutiveAssessment, ExecutiveFinding, ExecutiveSummary, ExecutiveMetrics,
    ExecutiveEngine, ExecutiveValidator, ExecutiveSerializer,
    get_executive_assessment, get_executive_summary, get_key_risks,
    get_unresolved_conflicts, trace_executive_finding, get_readiness_level
)


# --- Mock Helpers ---

class DummyDocument:
    def __init__(self, id, name, doc_type, uploaded_at="2026-06-24T12:00:00Z"):
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
    def __init__(self, id, claim_id, doc_id, text="excerpt", section="Moat", page=1, conf=0.9):
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
    def __init__(self, domain, obs_list, risk_list=None, qst_list=None, version="1.0.0", prompt_ver="1.0.0", conf=0.85, generated_at="2026-06-24T12:00:00Z"):
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
    def __init__(self, id, explanation, claim1_id, claim2_id, conflict_type="FACTUAL", conf=0.9, created_at="2026-06-24T12:00:00Z"):
        self.id = id
        self.conflict_explanation = explanation
        self.conflict_type = conflict_type
        self.confidence = conf
        self.created_at = created_at
        self.preferred_claim_id = claim1_id
        self.superseded_claim_id = claim2_id


@pytest.fixture
def complex_graph():
    docs = [DummyDocument("doc-1", "Standard Patent", "Patent")]
    profile = DummyProfile(docs)
    claims = [
        DummyClaim("claim-1", "moat_status", "Startup has robust tech moat"),
        DummyClaim("claim-2", "moat_status", "Startup has no tech moat"),
        DummyClaim("claim-3", "trl_level", "TRL level is 5"),
    ]
    evidence = [
        DummyEvidence("ev-1", "claim-1", "doc-1", conf=0.95),
        DummyEvidence("ev-2", "claim-2", "doc-1", conf=0.60),
        DummyEvidence("ev-3", "claim-3", "doc-1", conf=0.90)
    ]
    obs1 = DummyObservation("obs-1", "Moat is robust.", ["claim-1"], ["ev-1"], conf=0.9, domain="ip")
    obs2 = DummyObservation("obs-2", "No real moat.", ["claim-2"], ["ev-2"], conf=0.6, domain="competition")
    obs3 = DummyObservation("obs-3", "TRL is validated at level 5.", ["claim-3"], ["ev-3"], conf=0.85, domain="trl")

    risk = DummyRisk("risk-1", "Regulatory approval delay risk.", ["obs-1"], ["claim-1"], ["ev-1"])
    qst = DummyQuestion("qst-1", "What is the manufacturing scale plan?", "Assess scalability")

    asm1 = DummyAssessment("ip", [obs1], [risk], [qst], generated_at="2026-06-24T12:00:00Z")
    asm2 = DummyAssessment("competition", [obs2], generated_at="2026-06-24T11:00:00Z")
    asm3 = DummyAssessment("trl", [obs3], generated_at="2026-06-24T11:30:00Z")

    conflict = DummyConflict("conf-1", "Factual moat conflict", "claim-1", "claim-2")

    graph = ObservationGraphBuilder.build(profile, claims, evidence, [asm1, asm2, asm3], [conflict])
    return graph


def test_executive_generation(complex_graph):
    # Run conflict resolution first
    graph = ConflictResolutionEngine.resolve(complex_graph)
    
    # Generate executive assessment
    graph = ExecutiveEngine.generate(graph)
    
    exec_node = graph.executive_assessment
    assert exec_node is not None
    assert exec_node.node_type == NodeType.EXECUTIVE
    assert len(exec_node.key_observations) > 0
    assert len(exec_node.major_risks) > 0
    assert exec_node.confidence > 0.0

    # Validate
    errors = ExecutiveValidator.validate(graph)
    assert len(errors) == 0, f"Validation errors found: {errors}"


def test_summary_generation(complex_graph):
    graph = ConflictResolutionEngine.resolve(complex_graph)
    graph = ExecutiveEngine.generate(graph)
    
    summary = get_executive_summary(graph)
    assert summary is not None
    assert "yielder" in summary.overview or "yield" in summary.overview or "assessment" in summary.overview
    assert len(summary.strengths) > 0
    assert len(summary.weaknesses) > 0
    assert len(summary.opportunities) > 0
    assert len(summary.threats) > 0
    assert len(summary.missing_information) > 0


def test_risk_aggregation(complex_graph):
    graph = ConflictResolutionEngine.resolve(complex_graph)
    graph = ExecutiveEngine.generate(graph)
    
    risks = get_key_risks(graph)
    assert len(risks) == 1
    assert risks[0].finding_type == "RISK"
    assert "Regulatory approval" in risks[0].description


def test_conflict_aggregation(complex_graph):
    # 1. Unresolved conflict test (without running conflict resolution)
    graph = ExecutiveEngine.generate(complex_graph)
    unresolved = get_unresolved_conflicts(graph)
    assert len(unresolved) == 1
    assert "conf-1" in unresolved

    # 2. Resolved conflict test
    graph2 = ConflictResolutionEngine.resolve(complex_graph)
    graph2 = ExecutiveEngine.generate(graph2)
    unresolved2 = get_unresolved_conflicts(graph2)
    assert len(unresolved2) == 0


def test_resolution_usage(complex_graph):
    # Factual conflict resolved in favor of claim-1 (which links to obs-1). obs-2 (superseded) should be suppressed.
    graph = ConflictResolutionEngine.resolve(complex_graph)
    graph = ExecutiveEngine.generate(graph)
    
    exec_node = get_executive_assessment(graph)
    obs_desc_list = [f.description for f in exec_node.key_observations]
    
    assert "Moat is robust." in obs_desc_list
    assert "No real moat." not in obs_desc_list  # Suppressed!


def test_duplicate_filtering(complex_graph):
    # Add duplicate observations via correlation node
    corr_id = "corr-dup-1"
    corr = CorrelationNode(
        node_id=corr_id,
        node_type=NodeType.CORRELATION,
        correlation_id=corr_id,
        correlation_type="DUPLICATES",
        description="Duplicate observations.",
        confidence=0.9,
        created_at=datetime.utcnow().isoformat() + "Z"
    )
    complex_graph.correlations[corr_id] = corr
    
    # Link to obs-1 and obs-3
    edge1 = Edge(source_id=corr_id, source_type=NodeType.CORRELATION, target_id="obs-1", target_type=NodeType.OBSERVATION, relationship="RELATED_TO")
    edge2 = Edge(source_id=corr_id, source_type=NodeType.CORRELATION, target_id="obs-3", target_type=NodeType.OBSERVATION, relationship="RELATED_TO")
    complex_graph.edges.extend([edge1, edge2])
    complex_graph.out_edges.setdefault(corr_id, []).extend([edge1, edge2])
    complex_graph.in_edges.setdefault("obs-1", []).append(edge1)
    complex_graph.in_edges.setdefault("obs-3", []).append(edge2)
    
    graph = ExecutiveEngine.generate(complex_graph)
    exec_node = get_executive_assessment(graph)
    
    obs_ids_in_exec = []
    for f in exec_node.key_observations:
        obs_ids_in_exec.extend(f.supporting_observations)
        
    # Duplicate obs-3 should be filtered out
    assert "obs-1" in obs_ids_in_exec
    assert "obs-3" not in obs_ids_in_exec


def test_traceability(complex_graph):
    graph = ConflictResolutionEngine.resolve(complex_graph)
    graph = ExecutiveEngine.generate(graph)
    
    # Trace finding for obs-1
    trace = trace_executive_finding(graph, "EXEC-FIND-OBS-obs-1")
    assert trace is not None
    assert "observation" in trace
    assert trace["observation"].observation_id == "obs-1"
    assert len(trace["claims"]) > 0


def test_confidence_validation(complex_graph):
    graph = ConflictResolutionEngine.resolve(complex_graph)
    graph = ExecutiveEngine.generate(graph)
    
    # Mutate confidence to illegal value
    graph.executive_assessment.confidence = 1.5
    errors = ExecutiveValidator.validate(graph)
    assert any("must be between 0.0 and 1.0" in e for e in errors)


def test_readiness_level(complex_graph):
    graph = ConflictResolutionEngine.resolve(complex_graph)
    graph = ExecutiveEngine.generate(graph)
    
    readiness = get_readiness_level(graph)
    assert readiness == "TRL-5"


def test_serialization(complex_graph):
    graph = ConflictResolutionEngine.resolve(complex_graph)
    graph = ExecutiveEngine.generate(graph)
    orig_hash = graph.graph_hash

    # Serialize
    json_data = ExecutiveSerializer.to_json(graph)
    
    # Deserialize
    new_graph = ExecutiveSerializer.from_json(json_data)
    assert new_graph.graph_hash == orig_hash
    assert new_graph.executive_assessment is not None
    assert new_graph.executive_assessment.readiness_level == "TRL-5"
    assert len(new_graph.executive_assessment.key_observations) == len(graph.executive_assessment.key_observations)
    
    # Export Report
    report = ExecutiveSerializer.export_executive_report(new_graph)
    assert report["readiness_level"] == "TRL-5"
    assert report["graph_hash"] == orig_hash
    assert report["metrics"]["total_observations"] == 3


def test_graph_hash_changes(complex_graph):
    graph = ConflictResolutionEngine.resolve(complex_graph)
    graph = ExecutiveEngine.generate(graph)
    orig_hash = graph.graph_hash
    
    # Mutate executive assessment summary
    graph.executive_assessment.summary.overview = "Mutated summary overview text"
    
    # Recompute hash
    new_hash = ObservationGraphBuilder._compute_hash(graph)
    assert orig_hash != new_hash


def test_backward_compatibility(complex_graph):
    # Serialize before generating executive assessment
    json_data = ExecutiveSerializer.to_json(complex_graph)
    
    new_graph = ExecutiveSerializer.from_json(json_data)
    assert new_graph.executive_assessment is None
    assert len(new_graph.executive_indexes) == 0
    assert len(new_graph.executive_statistics) == 0


def test_large_graph_performance():
    # Setup dataset mimicking the performance targets:
    # 5000 evidence, 1000 claims, 500 observations, 300 correlations, 150 conflicts, 150 resolutions, 100 assessments
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
    for i in range(100):
        obs_list = []
        for _ in range(5):  # 5 observations per assessment => 500 observations total
            obs_id = f"obs-{obs_counter}"
            claim_ids = [f"claim-{obs_counter * 2 % 1000}", f"claim-{(obs_counter * 2 + 1) % 1000}"]
            ev_ids = [f"ev-{obs_counter * 10 % 5000}"]
            obs_list.append(DummyObservation(obs_id, f"Observation text for {obs_id}", claim_ids, ev_ids))
            obs_counter += 1
            
        assessments.append(DummyAssessment(f"domain_{i}", obs_list))
        
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
        
    # Benchmark 1: Executive Generation < 500 ms
    t_gen_start = time.perf_counter()
    graph = ExecutiveEngine.generate(graph)
    t_gen_end = time.perf_counter()
    gen_duration = t_gen_end - t_gen_start
    print(f"Executive Generation time: {gen_duration * 1000.0:.4f} ms")
    assert gen_duration < 0.500, f"Executive generation exceeded 500 ms: {gen_duration * 1000.0:.4f}ms"
    
    # Benchmark 2: Queries < 10 ms
    t_query_start = time.perf_counter()
    asm = get_executive_assessment(graph)
    sumry = get_executive_summary(graph)
    risks = get_key_risks(graph)
    unres = get_unresolved_conflicts(graph)
    trl = get_readiness_level(graph)
    t_query_end = time.perf_counter()
    query_duration = (t_query_end - t_query_start) * 1000.0
    print(f"Queries execution time: {query_duration:.4f} ms")
    assert query_duration < 10.0, f"Queries execution exceeded 10 ms: {query_duration:.4f}ms"
    
    # Benchmark 3: Serialization < 500 ms
    t_serial_start = time.perf_counter()
    json_str = ExecutiveSerializer.to_json(graph)
    t_serial_end = time.perf_counter()
    serial_duration = t_serial_end - t_serial_start
    print(f"Serialization time: {serial_duration * 1000.0:.4f} ms")
    assert serial_duration < 0.500, f"Serialization exceeded 500 ms: {serial_duration * 1000.0:.4f}ms"
