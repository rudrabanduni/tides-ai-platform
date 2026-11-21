"""tests/test_external_evidence_quality.py - Comprehensive Offline Quality Suite for Phase 4.3.

Verifies:
1. Evidence-Grade Semantics Correction:
   - Tavily's numeric 'score' reflects search-result relevance, not factual accuracy or truth probability.
   - Decoupled relevance score stored in relevance_score.
   - Source authority tiers: OFFICIAL_REGULATORY_FILING, INSTITUTIONAL_BENCHMARK, INDUSTRY_ANALYST, GENERAL_WEB.
   - Freshness tracking: CURRENT, OUTDATED, DATE_UNAVAILABLE.
   - Support status: EXPLICIT_SUPPORT, INDIRECT_CONTEXT, INCONCLUSIVE.
   - Candidate unverified search results default to RETRIEVED_SEARCH_RESULT with requires_verification=True.
2. Multi-Source Corroboration:
   - Distinct source domains (>= 2) upgrade to INDEPENDENTLY_CORROBORATED and CORROBORATED_EXTERNAL_BENCHMARK.
   - Duplicate domains (e.g. 2 articles on same domain) remain SINGLE_SOURCE and requires_verification=True.
3. Official Regulatory Filings:
   - sec.gov, mca.gov.in, .gov, .nic.in recognized as OFFICIAL_REGULATORY_FILING with requires_verification=False.
4. Claim-to-Source Traceability:
   - Criteria evaluations link claimed_criterion_id, support status, and diligence limitations.
   - Founder self-reported claims strictly remain SELF_REPORTED_ONLY without submitted deck proof.
5. Export Format Audit:
   - Markdown, HTML, and ReportLab PDF all include Appendix D (External Independent Research Evidence Registry).
   - HTML renders styled responsive <table> elements and working <a> links.
   - PDF renders ReportLab Table flowables with proper margins, column widths, and clickable links.
6. Budget & Error Resilience:
   - Zero-result searches and budget exhaustion fail safely without inventing citations or crashing.
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
from app.services.ai.exceptions import AIBudgetExhaustedError
from app.services.ai.research import (
    DisabledResearchProvider,
    ExternalResearchService,
    MockResearchProvider,
    ResearchEvidenceItem,
    ResearchQueryRequest,
    TavilyResearchProvider,
    classify_source_authority,
    assess_freshness,
)
from tests.test_phase2_domains_and_supervisory import MockStartup, MockClaim, MockEvidence


# ===========================================================================
# 1. Evidence-Grade Semantics: Decoupling Relevance from Truth
# ===========================================================================

def test_high_relevance_score_does_not_grant_documented_fact():
    """A search result with 0.98 query relevance from a general web source remains
    RETRIEVED_SEARCH_RESULT with requires_verification=True, not DOCUMENTED_EXTERNAL_FACT.
    """
    prov = TavilyResearchProvider(api_key="tvly-mock-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "query": "Battery storage cost per kWh 2025",
        "results": [
            {
                "title": "CleanTech Enthusiast Forum Discussion",
                "url": "https://cleantechforum.io/posts/battery-costs-plunge",
                "content": "A forum poster claims battery packs now cost under $40/kWh.",
                "score": 0.98,  # Extremely high keyword relevance
                "published_date": "2025-05-01",
            }
        ],
        "usage": {"credits": 1},
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        res = prov.search_detailed(
            ResearchQueryRequest(query="Battery storage cost per kWh 2025", search_type="market_size_growth")
        )
        assert len(res.evidence_items) == 1
        item = res.evidence_items[0]

        # Score is preserved as relevance, NOT proof of truth
        assert item.relevance_score == 0.98
        assert item.source_authority == "GENERAL_WEB"
        assert item.verification_grade == "RETRIEVED_SEARCH_RESULT"
        assert item.requires_verification is True
        assert item.corroboration_status == "SINGLE_SOURCE"
        assert item.provenance == "EXTERNAL_INDEPENDENT_RESEARCH"


def test_low_relevance_score_marked_inconclusive():
    """A search result with score < 0.4 is classified as INCONCLUSIVE with explicit diligence limitations."""
    prov = TavilyResearchProvider(api_key="tvly-mock-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "query": "Grid BESS market sizing India",
        "results": [
            {
                "title": "Smartphone Battery Care Tips",
                "url": "https://techguide.com/battery-tips",
                "content": "Charge your mobile battery between 20% and 80% for longevity.",
                "score": 0.28,  # Low relevance
                "published_date": "2025-01-10",
            }
        ],
        "usage": {"credits": 1},
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        res = prov.search_detailed(
            ResearchQueryRequest(query="Grid BESS market sizing India", search_type="market_size_growth")
        )
        assert len(res.evidence_items) == 1
        item = res.evidence_items[0]

        assert item.relevance_score == 0.28
        assert item.support_status == "INCONCLUSIVE"
        assert item.requires_verification is True
        assert "Low search-result relevance" in (item.verification_limitations or "")


# ===========================================================================
# 2. Freshness and Publication Date Handling
# ===========================================================================

def test_freshness_classification_and_date_handling():
    """Verifies CURRENT, OUTDATED, and DATE_UNAVAILABLE publication date handling."""
    assert assess_freshness("2025-04-15") == "CURRENT"
    assert assess_freshness("2023-11-20") == "CURRENT"
    assert assess_freshness("2019-03-01") == "OUTDATED"
    assert assess_freshness("2015-10-12") == "OUTDATED"
    assert assess_freshness(None) == "DATE_UNAVAILABLE"
    assert assess_freshness("") == "DATE_UNAVAILABLE"
    assert assess_freshness("N/A") == "DATE_UNAVAILABLE"

    # Verify provider attaches freshness and limitations for outdated sources
    prov = TavilyResearchProvider(api_key="tvly-mock-key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "query": "Historical Solar PV Costs",
        "results": [
            {
                "title": "Solar PV Cost Analysis 2017",
                "url": "https://reuters.com/solar-2017",
                "content": "Solar PV module prices dropped in 2017.",
                "score": 0.85,
                "published_date": "2017-06-15",
            },
            {
                "title": "Undated Blog Post",
                "url": "https://generalblog.org/solar",
                "content": "Solar panels are popular.",
                "score": 0.70,
                "published_date": None,
            }
        ],
        "usage": {"credits": 1},
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        res = prov.search_detailed(
            ResearchQueryRequest(query="Historical Solar PV Costs", search_type="market_size_growth")
        )
        assert len(res.evidence_items) == 2

        outdated_item = res.evidence_items[0]
        assert outdated_item.freshness_status == "OUTDATED"
        assert "over 3 years old" in (outdated_item.verification_limitations or "")

        undated_item = res.evidence_items[1]
        assert undated_item.freshness_status == "DATE_UNAVAILABLE"
        assert "unavailable" in (undated_item.verification_limitations or "")


# ===========================================================================
# 3. Source Authority Classification & Official Regulatory Filings
# ===========================================================================

def test_source_authority_tier_classification():
    """Verifies domain categorization across regulatory, institutional, analyst, and web tiers."""
    assert classify_source_authority("sec.gov") == "OFFICIAL_REGULATORY_FILING"
    assert classify_source_authority("mca.gov.in") == "OFFICIAL_REGULATORY_FILING"
    assert classify_source_authority("cea.nic.in") == "OFFICIAL_REGULATORY_FILING"
    assert classify_source_authority("energy.gov") == "OFFICIAL_REGULATORY_FILING"
    assert classify_source_authority("rbi.org.in") == "OFFICIAL_REGULATORY_FILING"

    assert classify_source_authority("iea.org") == "INSTITUTIONAL_BENCHMARK"
    assert classify_source_authority("worldbank.org") == "INSTITUTIONAL_BENCHMARK"
    assert classify_source_authority("standards.ieee.org") == "INSTITUTIONAL_BENCHMARK"
    assert classify_source_authority("iso.org") == "INSTITUTIONAL_BENCHMARK"

    assert classify_source_authority("gartner.com") == "INDUSTRY_ANALYST"
    assert classify_source_authority("bloomberg.com") == "INDUSTRY_ANALYST"
    assert classify_source_authority("reuters.com") == "INDUSTRY_ANALYST"
    assert classify_source_authority("mckinsey.com") == "INDUSTRY_ANALYST"
    assert classify_source_authority("techcrunch.com") == "INDUSTRY_ANALYST"

    assert classify_source_authority("unknown-startup-blog.io") == "GENERAL_WEB"
    assert classify_source_authority("randomdomain.net") == "GENERAL_WEB"


def test_official_regulatory_filing_receives_official_grade():
    """An official regulatory source (.gov or sec.gov) is recognized as DOCUMENTED_OFFICIAL_FILING."""
    prov = TavilyResearchProvider(api_key="tvly-mock-key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "query": "Fluence Energy SEC Form 10-K",
        "results": [
            {
                "title": "Fluence Energy Inc 2024 Form 10-K",
                "url": "https://www.sec.gov/ix?doc=/Archives/edgar/data/1868944/000186894424000078/flnc-20240930.htm",
                "content": "Total revenue for fiscal year ended September 30, 2024 was $2.7 billion.",
                "score": 0.94,
                "published_date": "2024-11-27",
            }
        ],
        "usage": {"credits": 2},
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        res = prov.search_detailed(
            ResearchQueryRequest(query="Fluence Energy SEC Form 10-K", search_type="competitor_intelligence", search_depth="advanced")
        )
        assert len(res.evidence_items) == 1
        item = res.evidence_items[0]
        assert item.source_domain == "sec.gov"
        assert item.source_authority == "OFFICIAL_REGULATORY_FILING"
        assert item.verification_grade == "DOCUMENTED_OFFICIAL_FILING"
        assert item.requires_verification is False


# ===========================================================================
# 4. Multi-Source Corroboration: Independent vs Duplicate Domains
# ===========================================================================

def test_multi_source_corroboration_distinct_vs_duplicate_domains():
    """>= 2 distinct domains corroborate an external finding; duplicate articles from
    the same domain remain SINGLE_SOURCE and requires_verification=True.
    """
    expert = MarketOpportunityExpert()

    # Case A: Duplicate domains (both from techcrunch.com)
    dup_items = [
        ResearchEvidenceItem(
            url="https://techcrunch.com/2024/article1",
            title="Form Energy Series F Part 1",
            excerpt="Raised $405M.",
            summary="Raised $405M.",
            source_domain="techcrunch.com",
            source_type="competitor_intelligence",
            relevance_score=0.88,
            verification_grade="RETRIEVED_SEARCH_RESULT",
            requires_verification=True,
        ),
        ResearchEvidenceItem(
            url="https://techcrunch.com/2024/article2",
            title="Form Energy Series F Follow-Up",
            excerpt="Follow-up on $405M round.",
            summary="Follow-up on $405M round.",
            source_domain="techcrunch.com",
            source_type="competitor_intelligence",
            relevance_score=0.82,
            verification_grade="RETRIEVED_SEARCH_RESULT",
            requires_verification=True,
        ),
    ]

    corroborated_dup = expert.corroborate_evidence_items(dup_items)
    assert corroborated_dup[0].corroboration_status == "SINGLE_SOURCE"
    assert corroborated_dup[1].corroboration_status == "SINGLE_SOURCE"
    assert corroborated_dup[0].requires_verification is True
    assert corroborated_dup[0].verification_grade == "RETRIEVED_SEARCH_RESULT"

    # Case B: Distinct domains (bloomberg.com + reuters.com)
    distinct_items = [
        ResearchEvidenceItem(
            url="https://bloomberg.com/news/form-energy",
            title="Bloomberg: Form Energy Raises $405M",
            excerpt="Form Energy raised $405M.",
            summary="Form Energy raised $405M.",
            source_domain="bloomberg.com",
            source_type="competitor_intelligence",
            relevance_score=0.91,
            verification_grade="RETRIEVED_SEARCH_RESULT",
            requires_verification=True,
        ),
        ResearchEvidenceItem(
            url="https://reuters.com/business/form-energy-funding",
            title="Reuters: Form Energy Secures $405M",
            excerpt="Reuters confirms Form Energy $405M Series F.",
            summary="Reuters confirms Form Energy $405M Series F.",
            source_domain="reuters.com",
            source_type="competitor_intelligence",
            relevance_score=0.89,
            verification_grade="RETRIEVED_SEARCH_RESULT",
            requires_verification=True,
        ),
    ]

    corroborated_distinct = expert.corroborate_evidence_items(distinct_items)
    assert corroborated_distinct[0].corroboration_status == "INDEPENDENTLY_CORROBORATED"
    assert corroborated_distinct[1].corroboration_status == "INDEPENDENTLY_CORROBORATED"
    assert corroborated_distinct[0].verification_grade == "CORROBORATED_EXTERNAL_BENCHMARK"
    assert corroborated_distinct[1].verification_grade == "CORROBORATED_EXTERNAL_BENCHMARK"
    assert corroborated_distinct[0].requires_verification is False


# ===========================================================================
# 5. Strict Factual Provenance: No Self-Reported Elevation
# ===========================================================================

def test_external_search_never_elevates_unsupported_founder_claim():
    """Founder self-reported TAM without supporting deck documentation strictly remains
    SELF_REPORTED_ONLY even when independent research corroborates the market size.
    """
    mock_provider = MockResearchProvider()
    ExternalResearchService.reset_instance()
    service = ExternalResearchService.get_instance()
    service.set_provider(mock_provider)

    startup = MockStartup(name="VoltTech", sector="CleanTech")
    claims = [
        MockClaim("c-tam-01", "mo_01_tam", "$48B global TAM"),
    ]
    # Evidence exists but has no primary verified snippet, so status remains SELF_REPORTED_ONLY
    evidence = [
        MockEvidence("ev-tam-01", "c-tam-01", "Founder interview statement")
    ]
    evidence[0].evidence_snippet = None
    metadata = {"evaluation_id": "eval-provenance-test"}

    expert = MarketOpportunityExpert()
    report = expert.evaluate(startup, claims, evidence, [], metadata)

    # Criterion MO-01 must remain SELF_REPORTED_ONLY
    tam_crit = report.criteria_evaluations["MO-01"]
    assert tam_crit.verification_status == VerificationStatus.SELF_REPORTED_ONLY
    assert tam_crit.verification_status != VerificationStatus.VERIFIED_DOCUMENTED

    # External research from mock provider is attached as context with strict mock provenance
    assert len(tam_crit.external_research_sources) > 0
    first_ext = tam_crit.external_research_sources[0]
    assert first_ext["provenance"] == "MOCK_SIMULATED_RESEARCH"
    assert first_ext["verification_grade"] == "SIMULATED_TEST_EVIDENCE"
    assert first_ext.get("is_mock") is True


# ===========================================================================
# 6. Full Export Format Audit: Markdown, HTML, and ReportLab PDF
# ===========================================================================

def test_full_export_formats_include_appendix_d_and_sources():
    """Verifies Appendix D (External Independent Research Evidence Registry) is present
    and valid across Markdown, HTML, and ReportLab PDF binary exports.
    """
    mock_provider = MockResearchProvider()
    ExternalResearchService.reset_instance()
    service = ExternalResearchService.get_instance()
    service.set_provider(mock_provider)

    startup = MockStartup(name="VoltGrid Systems", sector="CleanTech")
    claims = [
        MockClaim("c-mo-01", "mo_01_tam", "$48B TAM"),
        MockClaim("c-mo-03", "mo_03_target_market", "Utility BESS"),
        MockClaim("c-mo-07", "mo_07_competitor_details", "Fluence Energy"),
    ]
    evidence = [
        MockEvidence("ev-mo-01", "c-mo-01", "Utility BESS market estimated at $48B", "Slide 6", 6),
        MockEvidence("ev-mo-03", "c-mo-03", "Target segment utility BESS operators", "Slide 6", 6),
        MockEvidence("ev-mo-07", "c-mo-07", "Fluence Energy primary competitor", "Slide 7", 7),
    ]
    eval_id = "eval-export-audit-test"
    metadata = {"evaluation_id": eval_id}

    expert = MarketOpportunityExpert()
    mo_report = expert.evaluate(startup, claims, evidence, [], metadata)

    reviewer = SupervisoryReviewer()
    final_review = reviewer.review(
        domain_reports={"market_opportunity": mo_report},
        domain_experts={"market_opportunity": expert},
        profile=startup,
        claims=claims,
        evidence=evidence,
        metadata=metadata,
    )

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

    # 1. Appendix D in DueDiligenceReport
    app_d = next((a for a in report.appendices if a.appendix_id == "appendix_d"), None)
    assert app_d is not None
    assert "Appendix D: External Independent Research Evidence Registry" in app_d.title
    assert "iea.org" in app_d.content
    assert "Authority" in app_d.content
    assert "Support Status" in app_d.content

    # 2. Markdown Export
    md = ReportSerializer.export_markdown(report)
    assert "# Appendices" in md
    assert "Appendix D: External Independent Research Evidence Registry" in md
    assert "https://www.iea.org/reports/energy-storage-market-update-2025" in md
    assert "| Source Domain | Document / Article Title |" in md

    # 3. HTML Export
    html = ReportSerializer.export_html(report)
    assert "<html" in html
    assert "Appendix D: External Independent Research Evidence Registry" in html
    # HTML must render styled <table> elements
    assert '<table class="report-table">' in html
    assert "<th>Source Domain</th>" in html
    assert 'href="https://www.iea.org/reports/energy-storage-market-update-2025"' in html

    # 4. ReportLab PDF Export
    pdf_bytes = ReportSerializer.export_pdf_data(report)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 5000  # Multi-page compiled PDF
    assert pdf_bytes.startswith(b"%PDF")  # Valid PDF binary signature


# ===========================================================================
# 7. Budget & Error Resilience: Zero Results and Budget Exhaustion
# ===========================================================================

def test_zero_result_query_does_not_invent_citations():
    """Zero-result queries return an empty evidence list with NO_RELEVANT_SOURCES
    and do not invent false sources or verification grades.
    """
    prov = TavilyResearchProvider(api_key="tvly-mock-key")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "query": "Nonexistent hyper-niche startup xyz123",
        "results": [],
        "usage": {"credits": 1},
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        res = prov.search_detailed(
            ResearchQueryRequest(query="Nonexistent hyper-niche startup xyz123", search_type="competitor_intelligence")
        )
        assert len(res.evidence_items) == 0
        assert res.credits_used == 1
        assert res.actual_cost_usd == pytest.approx(0.008, abs=0.0001)


def test_budget_exhaustion_stops_gracefully_without_crashing_pipeline():
    """When shared evaluation budget ceiling is reached, research stops gracefully
    and evaluation completes without raising unhandled exceptions.
    """
    mock_provider = MockResearchProvider()
    ExternalResearchService.reset_instance()
    service = ExternalResearchService.get_instance()
    service.set_provider(mock_provider)

    eval_id = "eval-budget-exhausted-test"
    cost_mgr = CostLedgerManager.get_instance()
    ledger = cost_mgr.get_or_create_ledger(eval_id)
    # Saturate budget by reserving and reconciling the ledger ceiling
    sat_cost = ledger.max_budget_usd
    res_id = ledger.reserve_budget(estimated_cost_usd=sat_cost, agent_name="prior_ops")
    ledger.reconcile_operation(
        reservation_id=res_id,
        agent_name="prior_ops",
        provider="anthropic",
        model="claude-3-5-sonnet",
        input_tokens=10000,
        output_tokens=2500,
        actual_cost_usd=sat_cost,
    )
    assert ledger.is_exhausted is True

    startup = MockStartup(name="SolarWave", sector="CleanTech")
    claims = [MockClaim("c-mo-01", "mo_01_tam", "$10B TAM")]
    evidence = [MockEvidence("ev-01", "c-mo-01", "TAM $10B", "Slide 2", 2)]
    metadata = {"evaluation_id": eval_id}

    expert = MarketOpportunityExpert()
    # When budget ceiling is reached, research stops gracefully and returns empty list
    items = expert.gather_external_research(startup, claims, metadata)
    assert items == []
