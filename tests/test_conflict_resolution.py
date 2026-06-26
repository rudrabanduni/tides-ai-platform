import json
import time
import pytest
from datetime import datetime, timedelta
from typing import List, Optional, Any

from app.modules.evaluation.graph import (
    NodeType, GraphNode, DocumentNode, EvidenceNode, ClaimNode,
    ObservationNode, AssessmentNode, ConflictNode, RiskNode,
    QuestionNode, Edge, GraphStatistics, ObservationGraph,
    ObservationGraphBuilder
)
from app.modules.evaluation.conflict_resolution import (
    ResolutionNode, ResolutionEdge, ConflictResolutionEngine,
    ConflictResolutionValidator, get_resolution, get_conflict_resolutions,
    get_observation_resolutions, get_preferred_observation, trace_resolution,
    ConflictSerializer
)
from app.modules.evaluation.correlation import CorrelationNode


# --- Mock Context Helpers ---

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
    def __init__(self, obs_id, text, claim_ids, evidence_ids, conf=0.85):
        self.observation_id = obs_id
        self.observation = text
        self.claim_ids = claim_ids
        self.evidence_ids = evidence_ids
        self.confidence = conf


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
def sample_graph():
    docs = [DummyDocument("doc-1", "Standard Patent", "Patent")]
    profile = DummyProfile(docs)
    claims = [
        DummyClaim("claim-1", "moat_status", "Startup has a validated technology moat"),
        DummyClaim("claim-2", "moat_status", "Startup has no technology moat")
    ]
    evidence = [
        DummyEvidence("ev-1", "claim-1", "doc-1", conf=0.95),
        DummyEvidence("ev-2", "claim-2", "doc-1", conf=0.70)
    ]
    obs1 = DummyObservation("obs-1", "Moat is robust.", ["claim-1"], ["ev-1"], conf=0.9)
    obs2 = DummyObservation("obs-2", "No real moat.", ["claim-2"], ["ev-2"], conf=0.6)

    asm1 = DummyAssessment("ip", [obs1], generated_at="2026-06-24T12:00:00Z")
    asm2 = DummyAssessment("competition", [obs2], generated_at="2026-06-24T11:00:00Z")

    conflict = DummyConflict("conf-1", "Factual moat conflict", "claim-1", "claim-2")

    graph = ObservationGraphBuilder.build(profile, claims, evidence, [asm1, asm2], [conflict])
    return graph


def test_resolution_build_success(sample_graph):
    # Execute conflict resolution
    graph = ConflictResolutionEngine.resolve(sample_graph)
    assert len(graph.resolutions) == 1
    assert len(graph.resolution_edges) > 0

    # Verify using validator
    errors = ConflictResolutionValidator.validate(graph)
    assert len(errors) == 0, f"Expected no validation errors, got: {errors}"


def test_factual_resolution():
    docs = [DummyDocument("doc-1", "Doc 1", "PDF")]
    profile = DummyProfile(docs)
    claims = [
        DummyClaim("c-1", "val", "Moat is strong"),
        DummyClaim("c-2", "val", "Moat is weak")
    ]
    
    # Obs 1 has more evidence and higher confidence evidence
    evidence = [
        DummyEvidence("e-1", "c-1", "doc-1", conf=0.95),
        DummyEvidence("e-2", "c-1", "doc-1", conf=0.85),
        DummyEvidence("e-3", "c-2", "doc-1", conf=0.60)
    ]
    
    obs1 = DummyObservation("obs-1", "Moat is strong.", ["c-1"], ["e-1", "e-2"])
    obs2 = DummyObservation("obs-2", "Moat is weak.", ["c-2"], ["e-3"])
    
    asm1 = DummyAssessment("ip", [obs1])
    asm2 = DummyAssessment("competition", [obs2])
    conflict = DummyConflict("conf-1", "Explanation", "c-1", "c-2", conflict_type="FACTUAL")
    
    graph = ObservationGraphBuilder.build(profile, claims, evidence, [asm1, asm2], [conflict])
    graph = ConflictResolutionEngine.resolve(graph)
    
    # Assert preferred observation is obs-1
    res = get_resolution(graph, "RES-FACT-conf-1")
    assert res is not None
    assert res.preferred_observation_id == "obs-1"
    assert "stronger evidence support" in res.reasoning


def test_numerical_resolution():
    docs = [DummyDocument("doc-1", "Doc 1", "PDF")]
    profile = DummyProfile(docs)
    claims = [
        DummyClaim("c-1", "val", "Value is 100"),
        DummyClaim("c-2", "val", "Value is 200")
    ]
    
    evidence = [
        DummyEvidence("e-1", "c-1", "doc-1"),
        DummyEvidence("e-2", "c-2", "doc-1")
    ]
    
    obs1 = DummyObservation("obs-1", "Value is 100.", ["c-1"], ["e-1"])
    obs2 = DummyObservation("obs-2", "Value is 200.", ["c-2"], ["e-2"])
    
    # asm2 has later generated_at date
    asm1 = DummyAssessment("financial", [obs1], generated_at="2026-06-24T12:00:00Z")
    asm2 = DummyAssessment("market", [obs2], generated_at="2026-06-25T12:00:00Z")
    
    conflict = DummyConflict("conf-1", "Explanation", "c-1", "c-2", conflict_type="NUMERICAL")
    
    graph = ObservationGraphBuilder.build(profile, claims, evidence, [asm1, asm2], [conflict])
    graph = ConflictResolutionEngine.resolve(graph)
    
    # Assert preferred observation is obs-2 (latest timestamp)
    res = get_resolution(graph, "RES-NUME-conf-1")
    assert res is not None
    assert res.preferred_observation_id == "obs-2"
    assert "latest validated value" in res.reasoning


def test_temporal_resolution():
    docs = [DummyDocument("doc-1", "Doc 1", "PDF")]
    profile = DummyProfile(docs)
    claims = [
        DummyClaim("c-1", "val", "Product launched in 2024"),
        DummyClaim("c-2", "val", "Product launched in 2025")
    ]
    
    evidence = [
        DummyEvidence("e-1", "c-1", "doc-1"),
        DummyEvidence("e-2", "c-2", "doc-1")
    ]
    
    obs1 = DummyObservation("obs-1", "Launch 2024.", ["c-1"], ["e-1"])
    obs2 = DummyObservation("obs-2", "Launch 2025.", ["c-2"], ["e-2"])
    
    # asm2 generated_at is newer
    asm1 = DummyAssessment("product", [obs1], generated_at="2026-06-24T12:00:00Z")
    asm2 = DummyAssessment("product_expert_v2", [obs2], generated_at="2026-06-25T15:00:00Z")
    
    conflict = DummyConflict("conf-1", "Explanation", "c-1", "c-2", conflict_type="TEMPORAL")
    
    graph = ObservationGraphBuilder.build(profile, claims, evidence, [asm1, asm2], [conflict])
    graph = ConflictResolutionEngine.resolve(graph)
    
    # Assert preferred observation is obs-2
    res = get_resolution(graph, "RES-TEMP-conf-1")
    assert res is not None
    assert res.preferred_observation_id == "obs-2"
    assert "newest validated timestamp" in res.reasoning


def test_duplicate_resolution():
    docs = [DummyDocument("doc-1", "Doc 1", "PDF")]
    profile = DummyProfile(docs)
    claims = [
        DummyClaim("c-1", "val", "IP is registered"),
        DummyClaim("c-2", "val", "IP is registered")
    ]
    
    evidence = [
        DummyEvidence("e-1", "c-1", "doc-1"),
        DummyEvidence("e-2", "c-2", "doc-1")
    ]
    
    obs1 = DummyObservation("obs-1", "IP is registered.", ["c-1"], ["e-1"])
    obs2 = DummyObservation("obs-2", "IP is registered.", ["c-2"], ["e-2"])
    
    asm1 = DummyAssessment("ip", [obs1])
    asm2 = DummyAssessment("ip", [obs2])
    
    graph = ObservationGraphBuilder.build(profile, claims, evidence, [asm1, asm2])
    
    # Manually create a duplicate correlation
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
    graph.correlations[corr_id] = corr
    
    # Link correlation to the observations
    edge1 = Edge(source_id=corr_id, source_type=NodeType.CORRELATION, target_id="obs-1", target_type=NodeType.OBSERVATION, relationship="RELATED_TO")
    edge2 = Edge(source_id=corr_id, source_type=NodeType.CORRELATION, target_id="obs-2", target_type=NodeType.OBSERVATION, relationship="RELATED_TO")
    graph.edges.extend([edge1, edge2])
    graph.out_edges.setdefault(corr_id, []).extend([edge1, edge2])
    graph.in_edges.setdefault("obs-1", []).append(edge1)
    graph.in_edges.setdefault("obs-2", []).append(edge2)
    
    graph = ConflictResolutionEngine.resolve(graph)
    
    res = get_resolution(graph, "RES-CONS-corr-dup-1")
    assert res is not None
    assert res.resolution_type == "CONSENSUS"
    assert res.preferred_observation_id == "obs-1"


def test_insufficient_evidence():
    docs = [DummyDocument("doc-1", "Doc 1", "PDF")]
    profile = DummyProfile(docs)
    claims = [
        DummyClaim("c-1", "val", "IP registered"),
        DummyClaim("c-2", "val", "IP unregistered")
    ]
    
    evidence = []  # No evidence!
    
    obs1 = DummyObservation("obs-1", "IP registered.", ["c-1"], [])
    obs2 = DummyObservation("obs-2", "IP unregistered.", ["c-2"], [])
    
    asm1 = DummyAssessment("ip", [obs1])
    asm2 = DummyAssessment("ip", [obs2])
    conflict = DummyConflict("conf-1", "Explanation", "c-1", "c-2", conflict_type="FACTUAL")
    
    graph = ObservationGraphBuilder.build(profile, claims, evidence, [asm1, asm2], [conflict])
    graph = ConflictResolutionEngine.resolve(graph)
    
    res = get_resolution(graph, "RES-INSU-conf-1")
    assert res is not None
    assert res.resolution_type == "INSUFFICIENT_EVIDENCE"
    assert res.preferred_observation_id is None
    assert "Neither observation" in res.reasoning


def test_missing_conflict(sample_graph):
    graph = ConflictResolutionEngine.resolve(sample_graph)
    res = graph.resolutions["RES-FACT-conf-1"]
    
    # Artificially remove conflict node
    del graph.conflicts["conf-1"]
    
    errors = ConflictResolutionValidator.validate(graph)
    assert any("Dangling Reference: Conflict ID 'conf-1'" in e for e in errors)


def test_invalid_resolution(sample_graph):
    graph = ConflictResolutionEngine.resolve(sample_graph)
    res = graph.resolutions["RES-FACT-conf-1"]
    
    # 1. Invalid confidence
    res.confidence = -0.5
    errors = ConflictResolutionValidator.validate(graph)
    assert any("Invalid Confidence" in e for e in errors)
    res.confidence = 0.8
    
    # 2. Self reference edge
    bad_edge = ResolutionEdge(
        source_id="RES-FACT-conf-1",
        source_type=NodeType.RESOLUTION,
        target_id="RES-FACT-conf-1",
        target_type=NodeType.RESOLUTION,
        relationship="RESOLVES"
    )
    graph.resolution_edges.append(bad_edge)
    errors = ConflictResolutionValidator.validate(graph)
    assert any("Self-Reference" in e for e in errors)
    graph.resolution_edges.remove(bad_edge)
    
    # 3. Orphan resolution
    res_id = "RES-ORPHAN"
    orphan_node = ResolutionNode(
        node_id=res_id,
        node_type=NodeType.RESOLUTION,
        resolution_id=res_id,
        conflict_id="conf-1",
        resolution_type="FACTUAL",
        preferred_observation_id="obs-1",
        confidence=0.8,
        reasoning="orphan",
        supporting_claims=[],
        supporting_evidence=[],
        supporting_assessments=[],
        created_at=datetime.utcnow().isoformat() + "Z"
    )
    graph.resolutions[res_id] = orphan_node
    errors = ConflictResolutionValidator.validate(graph)
    assert any("Orphan Resolution: Resolution 'RES-ORPHAN' has no RESOLVES relationship." in e for e in errors)
    del graph.resolutions[res_id]


def test_trace_resolution(sample_graph):
    graph = ConflictResolutionEngine.resolve(sample_graph)
    trace = trace_resolution(graph, "RES-FACT-conf-1")
    
    assert trace is not None
    assert "resolution" in trace
    assert "conflict" in trace
    assert "observations" in trace
    
    obs_traces = trace["observations"]
    assert len(obs_traces) == 2
    
    # Validate trace details
    first_obs_trace = obs_traces[0]
    assert "observation" in first_obs_trace
    assert "claims" in first_obs_trace
    assert "assessments" in first_obs_trace
    assert len(first_obs_trace["claims"]) > 0
    assert len(first_obs_trace["assessments"]) > 0


def test_resolution_serialization(sample_graph):
    graph = ConflictResolutionEngine.resolve(sample_graph)
    orig_hash = graph.graph_hash

    # Serialize to JSON
    json_data = ConflictSerializer.to_json(graph)
    
    # Deserialize back
    new_graph = ConflictSerializer.from_json(json_data)
    
    assert new_graph.graph_hash == orig_hash
    assert len(new_graph.resolutions) == 1
    assert len(new_graph.resolution_edges) == len(graph.resolution_edges)
    assert "RES-FACT-conf-1" in new_graph.resolutions
    
    # Verify report export
    report = ConflictSerializer.export_resolution_report(new_graph)
    assert report["graph_hash"] == orig_hash
    assert report["statistics"]["resolution_count"] == 1
    assert report["statistics"]["resolved_conflicts"] == 1
    assert len(report["resolutions"]) == 1
    assert len(report["resolution_edges"]) > 0


def test_resolution_indexes(sample_graph):
    graph = ConflictResolutionEngine.resolve(sample_graph)
    
    # Check resolutions_by_conflict index
    res_conflict = get_conflict_resolutions(graph, "conf-1")
    assert len(res_conflict) == 1
    assert res_conflict[0].resolution_id == "RES-FACT-conf-1"
    
    # Check resolutions_by_observation index
    res_obs = get_observation_resolutions(graph, "obs-1")
    assert len(res_obs) == 1
    assert res_obs[0].resolution_id == "RES-FACT-conf-1"


def test_graph_hash_changes(sample_graph):
    graph = ConflictResolutionEngine.resolve(sample_graph)
    orig_hash = graph.graph_hash
    
    # Mutate a resolution field
    graph.resolutions["RES-FACT-conf-1"].reasoning = "New reasoning details"
    
    # Recompute hash
    new_hash = ObservationGraphBuilder._compute_hash(graph)
    assert orig_hash != new_hash


def test_backward_compatibility(sample_graph):
    # Serialize the graph BEFORE resolution
    json_data = ConflictSerializer.to_json(sample_graph)
    
    # Deserialize and ensure everything still works
    new_graph = ConflictSerializer.from_json(json_data)
    assert len(new_graph.resolutions) == 0
    assert len(new_graph.resolution_edges) == 0
    assert len(new_graph.conflicts) == 1


def test_large_graph_resolution_performance():
    # Setup dataset mimicking the performance targets:
    # 5000 evidence, 1000 claims, 500 observations, 300 correlations, 150 conflicts, 100 assessments
    docs = [DummyDocument(f"doc-{i}", f"Doc {i}", "PDF") for i in range(10)]
    profile = DummyProfile(docs)
    
    # Create claims
    claims = []
    for i in range(1000):
        claims.append(DummyClaim(f"claim-{i}", f"key_{i}", f"Claim value {i}"))
        
    # Create evidence linked to claims
    evidence = []
    for i in range(5000):
        claim_id = f"claim-{i % 1000}"
        doc_id = f"doc-{i % 10}"
        evidence.append(DummyEvidence(f"ev-{i}", claim_id, doc_id))
        
    # Create assessments with observations
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
        
    # Create 150 conflicts
    conflicts = []
    for i in range(150):
        # Conflict between claims
        claim1 = f"claim-{(i * 4) % 1000}"
        claim2 = f"claim-{(i * 4 + 2) % 1000}"
        conf_type = "FACTUAL" if i % 3 == 0 else ("NUMERICAL" if i % 3 == 1 else "TEMPORAL")
        conflicts.append(DummyConflict(f"conf-{i}", f"Conflict explanation {i}", claim1, claim2, conflict_type=conf_type))
        
    # Build graph
    t_start = time.perf_counter()
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments, conflicts)
    
    # Add 300 correlations
    for i in range(300):
        corr_id = f"corr-{i}"
        corr_type = "DUPLICATES" if i % 4 == 0 else "CORROBORATES"
        corr = CorrelationNode(
            node_id=corr_id,
            node_type=NodeType.CORRELATION,
            correlation_id=corr_id,
            correlation_type=corr_type,
            description=f"Correlation {i}",
            confidence=0.85,
            created_at=datetime.utcnow().isoformat() + "Z"
        )
        graph.correlations[corr_id] = corr
        # Link correlation to observations
        obs1_id = f"obs-{(i * 2) % 500}"
        obs2_id = f"obs-{(i * 2 + 1) % 500}"
        edge1 = Edge(source_id=corr_id, source_type=NodeType.CORRELATION, target_id=obs1_id, target_type=NodeType.OBSERVATION, relationship="RELATED_TO")
        edge2 = Edge(source_id=corr_id, source_type=NodeType.CORRELATION, target_id=obs2_id, target_type=NodeType.OBSERVATION, relationship="RELATED_TO")
        graph.edges.extend([edge1, edge2])
        graph.out_edges.setdefault(corr_id, []).extend([edge1, edge2])
        graph.in_edges.setdefault(obs1_id, []).append(edge1)
        graph.in_edges.setdefault(obs2_id, []).append(edge2)
        
    # Benchmark 1: Conflict Resolution < 2 seconds
    t_resolve_start = time.perf_counter()
    graph = ConflictResolutionEngine.resolve(graph)
    t_resolve_end = time.perf_counter()
    resolve_duration = t_resolve_end - t_resolve_start
    print(f"Conflict Resolution time: {resolve_duration:.4f} seconds")
    assert resolve_duration < 2.0, f"Conflict resolution exceeded 2 seconds: {resolve_duration:.4f}s"
    
    # Benchmark 2: Resolution lookup < 20 ms
    t_lookup_start = time.perf_counter()
    for i in range(150):
        res = get_resolution(graph, f"RES-FACT-conf-{i}") or get_resolution(graph, f"RES-NUME-conf-{i}") or get_resolution(graph, f"RES-TEMP-conf-{i}")
    t_lookup_end = time.perf_counter()
    lookup_duration = (t_lookup_end - t_lookup_start) / 150.0  # Average lookup time
    print(f"Average Resolution Lookup time: {lookup_duration * 1000.0:.4f} ms")
    assert lookup_duration < 0.020, f"Average lookup time exceeded 20 ms: {lookup_duration * 1000.0:.4f}ms"
    
    # Benchmark 3: Serialization < 500 ms
    t_serial_start = time.perf_counter()
    json_str = ConflictSerializer.to_json(graph)
    t_serial_end = time.perf_counter()
    serial_duration = t_serial_end - t_serial_start
    print(f"Serialization time: {serial_duration:.4f} seconds")
    assert serial_duration < 0.500, f"Serialization exceeded 500 ms: {serial_duration:.4f}s"
