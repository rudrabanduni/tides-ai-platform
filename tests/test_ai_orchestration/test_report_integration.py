import pytest
from app.modules.evaluation.graph.graph_models import ObservationGraph, NodeType
from app.modules.reporting import ReportBuilder, DueDiligenceReport
from app.modules.ai.orchestrator.report_integration import integrate_assessment_to_graph
from app.modules.ai.agents.models import AgentAssessment, Observation, Evidence, ExecutionMetadata

def test_report_integration_from_agent_assessments():
    # 1. Initialize an empty ObservationGraph
    graph = ObservationGraph()
    graph.startup_id = "startup-123"
    graph.startup_name = "Echo Startup"
    graph.category = "DeepTech"
    
    # 2. Build mock AgentAssessment objects for Founder, Product, Market
    meta = ExecutionMetadata(
        model="gpt-4o",
        provider="openai",
        latency_ms=120.5,
        retries=0,
        token_count=1500,
        prompt_version="1.0.0",
        timestamp="2026-06-27T12:00:00Z",
        execution_status="success"
    )
    
    founder_asm = AgentAssessment(
        domain="founder",
        overall_score=0.9,
        confidence=0.85,
        summary="Strong technical leadership.",
        strengths=["Core technical domain expertise"],
        weaknesses=["Gaps in sales and GTM roles"],
        opportunities=["Hiring commercial leads"],
        risks=["Key person risk"],
        recommendations=["Recruit GTM co-founder"],
        observations=[
            Observation(
                observation_id="OBS-FOUNDER-001",
                observation="Founders hold PhDs in AI.",
                claim_ids=["claim-1"],
                evidence_ids=["ev-1"],
                reasoning="Expert resumes show advanced degrees.",
                confidence=0.95
            )
        ],
        supporting_evidence=[
            Evidence(
                evidence_id="ev-1",
                source_claim_id="claim-1",
                evidence_snippet="CEO holds a PhD in computer science.",
                source_document="resumes.pdf"
            )
        ],
        open_questions=["Is the CTO committed full time?"],
        execution_metadata=meta
    )
    
    product_asm = AgentAssessment(
        domain="product",
        overall_score=0.8,
        confidence=0.9,
        summary="Defensible proprietary architecture.",
        strengths=["Scalable infrastructure"],
        weaknesses=["Roadmap delay risks"],
        opportunities=["Expanding product features"],
        risks=["Technical execution delay"],
        recommendations=["Enforce milestone delivery"],
        observations=[
            Observation(
                observation_id="OBS-PRODUCT-001",
                observation="Software architecture uses microservices.",
                claim_ids=["claim-2"],
                evidence_ids=["ev-2"],
                reasoning="System architectural design document reviews.",
                confidence=0.88
            )
        ],
        supporting_evidence=[
            Evidence(
                evidence_id="ev-2",
                source_claim_id="claim-2",
                evidence_snippet="Kubernetes cluster orchestrates API requests.",
                source_document="architecture.pdf"
            )
        ],
        open_questions=["What is the security compliance plan?"],
        execution_metadata=meta
    )
    
    market_asm = AgentAssessment(
        domain="market",
        overall_score=0.85,
        confidence=0.8,
        summary="High demand and large addressable market.",
        strengths=["Large TAM"],
        weaknesses=["Intense competition"],
        opportunities=["Niche expansion"],
        risks=["Competitor pricing pressure"],
        recommendations=["Differentiate positioning"],
        observations=[
            Observation(
                observation_id="OBS-MARKET-001",
                observation="TAM estimated at $10B.",
                claim_ids=["claim-3"],
                evidence_ids=["ev-3"],
                reasoning="Sizing analysis in slides.",
                confidence=0.92
            )
        ],
        supporting_evidence=[
            Evidence(
                evidence_id="ev-3",
                source_claim_id="claim-3",
                evidence_snippet="TAM: $10B based on customer segments.",
                source_document="deck.pdf"
            )
        ],
        open_questions=["What is the pricing discount model?"],
        execution_metadata=meta
    )
    
    # 3. Integrate all assessments to graph
    integrate_assessment_to_graph(graph, founder_asm)
    integrate_assessment_to_graph(graph, product_asm)
    integrate_assessment_to_graph(graph, market_asm)
    
    # Verify graph populated counts
    assert graph.graph_stats.observation_count == 3
    assert graph.graph_stats.evidence_count == 3
    assert graph.graph_stats.claim_count == 3
    assert graph.graph_stats.assessment_count == 3
    assert graph.graph_stats.risk_count == 3
    assert graph.graph_stats.question_count == 3
    
    # 4. Generate report
    report = ReportBuilder.build_due_diligence_report(graph)
    
    assert isinstance(report, DueDiligenceReport)
    assert report.startup_name == "Echo Startup"
    
    # Verify Founder assessment in report
    assert report.founder_assessment.confidence == 0.95
    assert len(report.founder_assessment.observations) == 1
    assert report.founder_assessment.observations[0]["id"] == "OBS-FOUNDER-001"
    assert report.founder_assessment.supporting_evidence[0]["id"] == "ev-1"
    assert "PhD in computer science" in report.founder_assessment.supporting_evidence[0]["excerpt"]
    
    # Verify Product assessment in report
    assert report.product_assessment.confidence == 0.88  # get_avg_confidence of OBS-PRODUCT-001
    assert len(report.product_assessment.observations) == 1
    assert report.product_assessment.observations[0]["id"] == "OBS-PRODUCT-001"
    assert "Kubernetes cluster" in report.product_assessment.supporting_evidence[0]["excerpt"]
    
    # Verify Market assessment in report
    assert report.market_assessment.confidence == 0.92  # get_avg_confidence of OBS-MARKET-001
    assert len(report.market_assessment.observations) == 1
    assert "TAM estimated at $10B" in report.market_assessment.observations[0]["text"]
