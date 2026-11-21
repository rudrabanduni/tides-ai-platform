"""tests/test_mock_research_provenance_guard.py - Regression Tests for Mock Research Provenance Guard.

Verifies Phase 4.5 requirements:
1. Every result from MockResearchProvider is visibly identified with:
   - is_mock == True
   - provenance == "MOCK_SIMULATED_RESEARCH"
   - verification_grade == "SIMULATED_TEST_EVIDENCE"
   - requires_verification == True
2. Mock results CANNOT be represented as sources retrieved or verified during a real external search.
3. Live-retrieved sources (Tavily) retain actual provider provenance (EXTERNAL_INDEPENDENT_RESEARCH) and source URLs.
4. A source's existence or query relevance score does not independently prove that it supports the startup's claim.
5. In Markdown, HTML, and ReportLab PDF binary exports:
   - Mock citations are visibly identified with SIMULATED MOCK EVIDENCE / OFFLINE MOCK markers.
   - Appendix D table explicitly tags mock entries with [MOCK] and [SIMULATED].
"""

from __future__ import annotations

import io
import pypdf
import pytest

from app.modules.evaluation.domain_schemas import (
    CriterionAssessment,
    DomainAssessmentReport,
    VerificationStatus,
)
from app.modules.evaluation.domains.market_opportunity import MarketOpportunityExpert
from app.modules.evaluation.graph.graph_builder import ObservationGraphBuilder
from app.modules.evaluation.report.report_engine import DueDiligenceReportEngine
from app.modules.evaluation.report.report_serializer import ReportSerializer
from app.modules.evaluation.supervisory.reviewer import SupervisoryReviewer
from app.services.ai.research import (
    ExternalResearchService,
    MockResearchProvider,
    ResearchEvidenceItem,
    ResearchQueryRequest,
    TavilyResearchProvider,
)
from tests.test_phase2_domains_and_supervisory import MockStartup, MockClaim, MockEvidence


def test_mock_research_provider_provenance_and_grade_strictly_identified():
    """All items from MockResearchProvider must be tagged as simulated test evidence."""
    provider = MockResearchProvider()
    req = ResearchQueryRequest(query="BESS energy storage TAM", search_type="market_size_growth")
    items = provider.search(req)

    assert len(items) >= 2
    for item in items:
        # Strict mock identification
        assert item.is_mock is True
        assert item.provenance == "MOCK_SIMULATED_RESEARCH"
        assert item.verification_grade == "SIMULATED_TEST_EVIDENCE"
        assert item.requires_verification is True
        assert "Simulated test fixture" in (item.verification_limitations or "")

        # Must NEVER be represented as live external research or documented fact
        assert item.provenance != "EXTERNAL_INDEPENDENT_RESEARCH"
        assert item.verification_grade != "DOCUMENTED_EXTERNAL_FACT"
        assert item.verification_grade != "DOCUMENTED_OFFICIAL_FILING"


def test_tavily_research_provider_retains_live_provenance_and_decouples_support():
    """Live search results from Tavily retain external provenance and decouple relevance from claim support."""
    # Simulate a search result with high query relevance (0.92)
    fake_tavily_data = {
        "query": "Grid BESS market size",
        "results": [
            {
                "title": "IEA Grid Storage Outlook",
                "url": "https://www.iea.org/reports/grid-storage-outlook",
                "content": "Global grid storage reached 48 GW in 2024.",
                "score": 0.92,
                "published_date": "2025-02-10",
            }
        ],
        "usage": {"credits": 1},
    }

    prov = TavilyResearchProvider(api_key="tvly-mock-key")

    from unittest.mock import MagicMock, patch
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = fake_tavily_data

    with patch("httpx.Client.post", return_value=mock_resp):
        req = ResearchQueryRequest(query="Grid BESS", search_type="market_size_growth")
        items = prov.search(req)

    assert len(items) == 1
    item = items[0]

    # Live provenance
    assert item.is_mock is False
    assert item.provenance == "EXTERNAL_INDEPENDENT_RESEARCH"
    assert item.url == "https://www.iea.org/reports/grid-storage-outlook"
    assert item.source_authority == "INSTITUTIONAL_BENCHMARK"

    # Factual diligence rule: high relevance score (0.92) does NOT automatically declare EXPLICIT_SUPPORT
    assert item.support_status != "EXPLICIT_SUPPORT"
    assert item.support_status == "RETRIEVED_CONTEXT"


def test_mock_citations_in_markdown_html_and_pdf_visibly_identified():
    """Confirms mock citations are visibly tagged in Markdown, HTML, and ReportLab PDF."""
    mock_prov = MockResearchProvider()
    ExternalResearchService.reset_instance()
    service = ExternalResearchService.get_instance()
    service.set_provider(mock_prov)

    startup = MockStartup(name="EcoStorage Systems", sector="CleanTech")
    claims = [
        MockClaim("c-mo-01", "mo_01_tam", "$48B TAM by 2032"),
        MockClaim("c-mo-07", "mo_07_competitor_details", "Fluence Energy"),
    ]
    evidence = [
        MockEvidence("ev-mo-01", "c-mo-01", "Pitch deck slide 5 TAM estimate", "Slide 5", 5),
        MockEvidence("ev-mo-07", "c-mo-07", "Pitch deck slide 8 competitor matrix", "Slide 8", 8),
    ]
    metadata = {"evaluation_id": "eval-provenance-guard-test"}

    # 1. Evaluate with MarketOpportunityExpert
    expert = MarketOpportunityExpert()
    mo_report = expert.evaluate(startup, claims, evidence, [], metadata)

    # 2. Supervisory Review
    reviewer = SupervisoryReviewer()
    final_review = reviewer.review(
        domain_reports={"market_opportunity": mo_report},
        domain_experts={"market_opportunity": expert},
        profile=startup,
        claims=claims,
        evidence=evidence,
        metadata=metadata,
    )

    # 3. Build Observation Graph & Report
    graph = ObservationGraphBuilder.build(
        profile=startup,
        claims=claims,
        evidence=evidence,
        assessments=[mo_report],
        conflicts=[],
    )
    graph.final_review = final_review
    graph.supervisory_review = final_review
    graph.domain_assessments["market_opportunity"] = mo_report

    graph = DueDiligenceReportEngine.generate(graph)
    report = graph.report

    # -----------------------------------------------------------------------
    # Verification 1: Markdown Export
    # -----------------------------------------------------------------------
    md = ReportSerializer.export_markdown(report)
    assert "[SIMULATED MOCK EVIDENCE" in md
    assert "[MOCK / TEST EVIDENCE - NOT A LIVE SEARCH RESULT]" in md
    assert "SIMULATED_TEST_EVIDENCE" in md
    assert "[MOCK] iea.org" in md
    assert "[SIMULATED] SIMULATED_TEST_EVIDENCE" in md
    assert "[SIMULATED MOCK FIXTURE - NOT LIVE SEARCH]" in md
    # Must NOT present mock results under live search banner
    assert "[LIVE RESEARCH" not in md

    # -----------------------------------------------------------------------
    # Verification 2: HTML Export
    # -----------------------------------------------------------------------
    html = ReportSerializer.export_html(report)
    assert "SIMULATED TEST EVIDENCE (OFFLINE MOCK)" in html
    assert "[SIMULATED MOCK EVIDENCE" in html
    assert "[MOCK] iea.org" in html
    assert "[SIMULATED] SIMULATED_TEST_EVIDENCE" in html

    # -----------------------------------------------------------------------
    # Verification 3: ReportLab PDF Binary Export
    # -----------------------------------------------------------------------
    pdf_bytes = ReportSerializer.export_pdf_data(report)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    full_pdf_text = "\n".join(p.extract_text() for p in reader.pages)

    # PDF must contain explicit mock markers
    assert "SIMULATED MOCK EVIDENCE" in full_pdf_text
    assert "OFFLINE MOCK" in full_pdf_text
    assert "[MOCK]" in full_pdf_text
    assert "[SIMULATED]" in full_pdf_text
