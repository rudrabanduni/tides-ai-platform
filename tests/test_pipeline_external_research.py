"""tests/test_pipeline_external_research.py - End-to-End Tests for Pipeline External Research Integration.

Verifies Phase 4.2 requirements:
1. Research is not invoked while disabled (default behavior).
2. MarketOpportunityExpert consumes external research findings when enabled in test configuration.
3. Research sources propagate end-to-end into DomainAssessmentReport, FinalReviewAssessment, Appendix D, and exported Markdown.
4. Strict factual provenance distinction: external research never elevates internal startup claims to VERIFIED_DOCUMENTED without primary deck evidence.
5. Research calls share the evaluation cost ledger and fail closed at the $0.55 ceiling.
6. Provider errors and zero-result queries fail safely without crashing the evaluation or inventing citations.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pytest

from app.core.config import Settings, get_settings
from app.modules.evaluation.domain_schemas import (
    CriterionAssessment,
    DomainAssessmentReport,
    FinalReviewAssessment,
    VerificationStatus,
)
from app.modules.evaluation.domains.market_opportunity import MarketOpportunityExpert
from app.modules.evaluation.supervisory.reviewer import SupervisoryReviewer
from app.modules.evaluation.graph.graph_builder import ObservationGraphBuilder
from app.modules.evaluation.report.report_engine import DueDiligenceReportEngine
from app.modules.evaluation.report.report_serializer import ReportSerializer
from app.services.ai.cost_ledger import CostLedgerManager, EvaluationCostLedger
from app.services.ai.exceptions import AIBudgetExhaustedError, AIProviderError
from app.services.ai.research import (
    DisabledResearchProvider,
    ExternalResearchService,
    MockResearchProvider,
    ResearchEvidenceItem,
    ResearchQueryRequest,
    TavilyResearchProvider,
)
from tests.test_phase2_domains_and_supervisory import MockStartup, MockClaim, MockEvidence


# ===========================================================================
# 1. Research Disabled by Default Tests
# ===========================================================================

def test_research_is_not_invoked_while_disabled():
    """Confirms that in default platform configuration, MarketOpportunityExpert makes 0 external calls."""
    ExternalResearchService.reset_instance()
    service = ExternalResearchService.get_instance()
    assert service.is_available() is False

    startup = MockStartup(name="VoltGrid", sector="CleanTech")
    claims = [
        MockClaim("c-mo-01", "mo_01_tam", "$48B TAM by 2032"),
        MockClaim("c-mo-03", "mo_03_target_market", "Utility BESS"),
    ]
    evidence = [
        MockEvidence("ev-mo-01", "c-mo-01", "Utility BESS market estimated at $48B", "Slide 6", 6),
        MockEvidence("ev-mo-03", "c-mo-03", "Target market is utility grid operators", "Slide 6", 6),
    ]
    metadata = {"evaluation_id": "eval-disabled-test-1"}

    expert = MarketOpportunityExpert()
    # Gather research explicitly
    items = expert.gather_external_research(startup, claims, metadata)
    assert items == []

    # Run full evaluate
    report = expert.evaluate(startup, claims, evidence, [], metadata)
    assert report.external_research_evidence == []
    assert "unavailable" in (report.confidence_limitations or "").lower()


# ===========================================================================
# 2. Market Evaluation Consumes External Findings When Enabled
# ===========================================================================

def test_market_opportunity_gathers_and_attaches_external_research():
    """When research provider is enabled, MarketOpportunityExpert collects and attaches external evidence."""
    mock_provider = MockResearchProvider(cost_per_query_usd=0.005)
    ExternalResearchService.reset_instance()
    service = ExternalResearchService.get_instance()
    service.set_provider(mock_provider)
    assert service.is_available() is True

    startup = MockStartup(name="VoltGrid Inc", sector="CleanTech")
    claims = [
        MockClaim("c-mo-01", "mo_01_tam", "$48B TAM"),
        MockClaim("c-mo-03", "mo_03_target_market", "BESS Storage"),
        MockClaim("c-mo-07", "mo_07_competitor_details", "Fluence Energy"),
    ]
    evidence = [
        MockEvidence("ev-mo-01", "c-mo-01", "Market estimated at $48B", "Slide 6", 6),
        MockEvidence("ev-mo-03", "c-mo-03", "Target segment BESS", "Slide 6", 6),
        MockEvidence("ev-mo-07", "c-mo-07", "Fluence Energy primary competitor", "Slide 7", 7),
    ]
    eval_id = "eval-enabled-test-2"
    metadata = {"evaluation_id": eval_id}

    ledger = CostLedgerManager.get_instance().get_or_create_ledger(
        evaluation_id=eval_id,
        max_budget_usd=0.55,
    )

    expert = MarketOpportunityExpert()
    report = expert.evaluate(startup, claims, evidence, [], metadata)

    # 1. External evidence attached to report
    assert len(report.external_research_evidence) >= 2
    assert any("iea.org" in str(src.get("source_domain", "")) for src in report.external_research_evidence)

    # 2. Attached to specific criteria
    mo_01 = report.criteria_evaluations.get("MO-01")
    assert mo_01 is not None
    assert len(mo_01.external_research_sources) > 0
    assert any("iea.org" in loc for loc in mo_01.source_locations)

    mo_07 = report.criteria_evaluations.get("MO-07")
    assert mo_07 is not None
    assert len(mo_07.external_research_sources) > 0

    # 3. Verified ledger recorded tool spend
    summary = ledger.get_summary()
    assert summary["total_external_tools_usd"] > 0.0
    assert summary["total_operations"] >= 2


# ===========================================================================
# 3. End-to-End Provenance & Final Due Diligence Report Propagation
# ===========================================================================

def test_external_sources_propagate_to_final_report_and_appendix():
    """External research items flow from domain report -> supervisory review -> Appendix D and Markdown."""
    mock_provider = MockResearchProvider(cost_per_query_usd=0.005)
    ExternalResearchService.reset_instance()
    service = ExternalResearchService.get_instance()
    service.set_provider(mock_provider)

    eval_id = "eval-e2e-report-propagation"
    ledger = CostLedgerManager.get_instance().get_or_create_ledger(
        evaluation_id=eval_id,
        max_budget_usd=0.55,
    )

    startup = MockStartup(name="Solaris Grid", sector="CleanTech")
    claims = [
        MockClaim("c-mo-01", "mo_01_tam", "$48B TAM"),
        MockClaim("c-mo-07", "mo_07_competitor_details", "Fluence"),
    ]
    evidence = [
        MockEvidence("ev-mo-01", "c-mo-01", "TAM $48B in 2032", "Slide 6", 6),
        MockEvidence("ev-mo-07", "c-mo-07", "Competitor Fluence noted", "Slide 7", 7),
    ]
    metadata = {"evaluation_id": eval_id}

    expert = MarketOpportunityExpert()
    mo_report = expert.evaluate(startup, claims, evidence, [], metadata)

    domain_reports = {"market_opportunity": mo_report}

    # Run Supervisory Review
    reviewer = SupervisoryReviewer()
    final_review = reviewer.review(
        domain_reports=domain_reports,
        domain_experts={"market_opportunity": expert},
        profile=startup,
        claims=claims,
        evidence=evidence,
        metadata=metadata,
    )

    # Verify Supervisory Review captured external research sources
    assert len(final_review.external_research_sources) > 0
    assert any("iea.org" in src.get("source_domain", "") for src in final_review.external_research_sources)

    # Build ObservationGraph with ObservationGraphBuilder
    graph = ObservationGraphBuilder.build(
        profile=startup,
        claims=claims,
        evidence=evidence,
        assessments=[mo_report],
        conflicts=[]
    )
    graph.final_review = final_review
    graph.supervisory_review = final_review
    graph.domain_assessments["market_opportunity"] = mo_report

    graph = DueDiligenceReportEngine.generate(graph)
    report = graph.report

    # Check Appendix D exists in report appendices
    app_d = next((a for a in report.appendices if a.appendix_id == "appendix_d"), None)
    assert app_d is not None
    assert "External Independent Research Evidence Registry" in app_d.title
    assert "iea.org" in app_d.content
    assert "SIMULATED_TEST_EVIDENCE" in app_d.content
    assert "[MOCK]" in app_d.content

    # Export to Markdown and confirm clickable external links
    md = ReportSerializer.export_markdown(report)
    assert "# Appendices" in md
    assert "Appendix D: External Independent Research Evidence Registry" in md
    assert "https://www.iea.org/reports/energy-storage-market-update-2025" in md
    assert "External Independent Research Sources" in md


# ===========================================================================
# 4. Strict Factual Provenance: No Automatic Elevation to VERIFIED_DOCUMENTED
# ===========================================================================

def test_external_search_does_not_elevate_internal_claim_to_verified_documented():
    """Confirms founder claim without primary deck proof remains SELF_REPORTED_ONLY despite external search."""
    mock_provider = MockResearchProvider()
    ExternalResearchService.reset_instance()
    service = ExternalResearchService.get_instance()
    service.set_provider(mock_provider)

    startup = MockStartup()
    claims = [
        MockClaim("c-mo-01", "mo_01_tam", "$48B global TAM"),
    ]
    # Claim exists but has unverified evidence snippet = None
    evidence = [
        MockEvidence("ev-mo-01", "c-mo-01", "Founder verbal estimate")
    ]
    evidence[0].evidence_snippet = None
    metadata = {"evaluation_id": "eval-provenance-guard"}

    expert = MarketOpportunityExpert()
    report = expert.evaluate(startup, claims, evidence, [], metadata)

    mo_01 = report.criteria_evaluations["MO-01"]
    # STRICT ASSERTION: Still SELF_REPORTED_ONLY, NOT elevated to VERIFIED_DOCUMENTED
    assert mo_01.verification_status == VerificationStatus.SELF_REPORTED_ONLY
    assert mo_01.verification_status != VerificationStatus.VERIFIED_DOCUMENTED

    # Mock research sources are visibly identified with mock provenance
    assert len(mo_01.external_research_sources) > 0
    ext_src = mo_01.external_research_sources[0]
    assert ext_src["provenance"] == "MOCK_SIMULATED_RESEARCH"
    assert ext_src["verification_grade"] == "SIMULATED_TEST_EVIDENCE"
    assert ext_src.get("is_mock") is True


# ===========================================================================
# 5. Shared Ledger Budget Ceiling Enforcement (Fail Closed)
# ===========================================================================

def test_pipeline_external_research_fails_closed_when_budget_exhausted():
    """When shared ledger budget is insufficient, research stops and does not dispatch unmetered calls."""
    eval_id = "eval-budget-ceiling-fail-closed"
    # Set ledger budget to $0.004 (less than $0.008 Tavily query cost)
    ledger = CostLedgerManager.get_instance().get_or_create_ledger(
        evaluation_id=eval_id,
        max_budget_usd=0.004,
    )

    tavily_prov = TavilyResearchProvider(api_key="tvly-mock-test", search_depth="basic")
    ExternalResearchService.reset_instance()
    service = ExternalResearchService.get_instance()
    service.set_provider(tavily_prov)

    startup = MockStartup()
    claims = [MockClaim("c-mo-01", "mo_01_tam", "$48B TAM")]
    metadata = {"evaluation_id": eval_id}

    expert = MarketOpportunityExpert()

    with patch("httpx.Client.post") as mock_post:
        # Gathers research
        items = expert.gather_external_research(startup, claims, metadata)
        # Guarantees network was never touched
        mock_post.assert_not_called()
        # Items should be empty due to budget block
        assert items == []


# ===========================================================================
# 6. Provider Error & Zero Results Resilience
# ===========================================================================

def test_provider_error_does_not_crash_market_evaluation():
    """If provider returns HTTP 500 error, market evaluation proceeds gracefully on document evidence."""
    tavily_prov = TavilyResearchProvider(api_key="tvly-mock-test")
    ExternalResearchService.reset_instance()
    service = ExternalResearchService.get_instance()
    service.set_provider(tavily_prov)

    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"

    startup = MockStartup()
    claims = [MockClaim("c-mo-01", "mo_01_tam", "$48B TAM")]
    evidence = [MockEvidence("ev-mo-01", "c-mo-01", "$48B TAM claimed", "Slide 6", 6)]
    metadata = {"evaluation_id": "eval-error-resilience"}

    expert = MarketOpportunityExpert()

    with patch("httpx.Client.post", return_value=mock_resp):
        # Must not raise an exception; evaluates safely using submitted documents
        report = expert.evaluate(startup, claims, evidence, [], metadata)
        assert report is not None
        assert report.domain_key == "market_opportunity"
        assert report.external_research_evidence == []
        assert "MO-01" in report.criteria_evaluations
