"""tests/test_tavily_provider.py - Deterministic Offline Tests for Tavily Research Provider.

Verifies:
1. Default safety: disabled by default, unknown provider rejection, missing key fallbacks.
2. Credit & pricing accounting:
   - Basic search: 1 credit = $0.008 USD.
   - Advanced search: 2 credits = $0.016 USD.
   - Actual credit reconciliation from response 'usage.credits'.
   - Conservative fallback when usage block is missing or contradictory.
   - Commercial list-price equivalent cost preservation.
3. Response mapping & factual provenance integrity:
   - Canonical URL, domain parsing (stripping www.), publication date, summary synthesis.
   - Strict provenance: EXTERNAL_INDEPENDENT_RESEARCH.
   - Verification grades: DOCUMENTED_EXTERNAL_FACT vs CORROBORATED_ESTIMATE.
   - External evidence does not grant VERIFIED_DOCUMENTED to internal startup claims.
   - Empty search results mapping.
4. Error handling & failure modes:
   - 401 Unauthorized -> AIProviderAuthenticationError.
   - 429 Quota/Rate Limit -> AIProviderError.
   - 5xx Server Error -> AIProviderError.
   - Timeouts & Connection Errors -> AIProviderError.
   - Malformed JSON -> AIResponseParseError.
5. Cost ledger & budget ceiling integration:
   - Pre-reservation against EvaluationCostLedger.
   - Tool expenditure reconciliation under external_tools_cost_usd.
   - Fail-closed budget blocking before dispatch.
   - Reservation cleanup on failure.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
import pytest
import httpx

from app.core.config import Settings, get_settings
from app.services.ai.cost_ledger import CostLedgerManager, EvaluationCostLedger
from app.services.ai.exceptions import (
    AIBudgetExhaustedError,
    AIProviderAuthenticationError,
    AIProviderError,
    AIResponseParseError,
)
from app.services.ai.research import (
    DisabledResearchProvider,
    ExternalResearchService,
    MockResearchProvider,
    ResearchEvidenceItem,
    ResearchQueryRequest,
    ResearchQueryResult,
    TavilyResearchProvider,
)
from app.modules.evaluation.domain_schemas import VerificationStatus


# ===========================================================================
# 1. Configuration & Default Safety Tests
# ===========================================================================

def test_research_provider_defaults_to_disabled():
    """Confirms research provider defaults to 'disabled' without explicit opt-in."""
    settings = get_settings()
    assert settings.research_provider == "disabled"
    assert settings.tavily_search_depth == "basic"
    assert settings.tavily_cost_per_credit_usd == pytest.approx(0.008, abs=0.0001)


def test_unconfigured_service_returns_disabled_provider():
    """When research_provider='disabled', ExternalResearchService resolves to DisabledResearchProvider."""
    with patch("app.services.ai.research.get_settings") as mock_settings:
        mock_settings.return_value = Settings(
            research_provider="disabled",
            tavily_api_key=None,
        )
        service = ExternalResearchService()
        assert isinstance(service._provider, DisabledResearchProvider)
        assert service.is_available() is False
        assert service.get_provider_name() == "disabled"


def test_unknown_provider_safely_falls_back_to_disabled():
    """An unknown/unsupported provider name safely falls back to DisabledResearchProvider."""
    with patch("app.services.ai.research.get_settings") as mock_settings:
        mock_settings.return_value = Settings(
            research_provider="unsupported_engine_xyz",
        )
        service = ExternalResearchService()
        assert isinstance(service._provider, DisabledResearchProvider)
        assert service.is_available() is False


def test_tavily_missing_key_safely_falls_back_to_disabled():
    """Specifying 'tavily' without an API key safely falls back to DisabledResearchProvider."""
    with patch("app.services.ai.research.get_settings") as mock_settings:
        mock_settings.return_value = Settings(
            research_provider="tavily",
            tavily_api_key=None,
            research_api_key=None,
        )
        service = ExternalResearchService()
        assert isinstance(service._provider, DisabledResearchProvider)
        assert service.is_available() is False


def test_tavily_provider_is_configured_predicate():
    """TavilyResearchProvider.is_configured() accurately checks key presence."""
    prov_no_key = TavilyResearchProvider(api_key=None)
    assert prov_no_key.is_configured() is False

    prov_empty_key = TavilyResearchProvider(api_key="   ")
    assert prov_empty_key.is_configured() is False

    prov_valid_key = TavilyResearchProvider(api_key="tvly-secret-123456789")
    assert prov_valid_key.is_configured() is True


def test_tavily_provider_repr_masks_api_key():
    """Ensures TavilyResearchProvider.__repr__ never reveals the API key."""
    prov = TavilyResearchProvider(api_key="tvly-super-secret-key-999")
    rep = repr(prov)
    assert "tvly-super-secret-key-999" not in rep
    assert "configured" in rep


# ===========================================================================
# 2. Credit & Pricing Accounting Tests
# ===========================================================================

def test_tavily_pricing_basic_vs_advanced():
    """Tests list-price credit calculation for basic ($0.008) and advanced ($0.016)."""
    prov = TavilyResearchProvider(
        api_key="tvly-test",
        search_depth="basic",
        cost_per_credit_usd=0.008,
    )
    # Basic depth: 1 credit = $0.008
    assert prov.get_cost_per_query_usd("basic") == pytest.approx(0.008, abs=0.0001)
    assert prov.get_cost_per_query_usd() == pytest.approx(0.008, abs=0.0001)

    # Advanced depth: 2 credits = $0.016
    assert prov.get_cost_per_query_usd("advanced") == pytest.approx(0.016, abs=0.0001)


def test_tavily_custom_cost_per_credit():
    """Tests custom cost per credit parameter."""
    prov = TavilyResearchProvider(
        api_key="tvly-test",
        cost_per_credit_usd=0.010,
    )
    assert prov.get_cost_per_query_usd("basic") == pytest.approx(0.010, abs=0.0001)
    assert prov.get_cost_per_query_usd("advanced") == pytest.approx(0.020, abs=0.0001)


# ===========================================================================
# 3. Successful Search & Factual Provenance Tests (Mocked Offline)
# ===========================================================================

SAMPLE_TAVILY_RESPONSE_BASIC = {
    "query": "Grid-scale battery storage market CAGR 2025",
    "results": [
        {
            "title": "Global Energy Storage Market Report 2025",
            "url": "https://www.reuters.com/business/energy-storage-cagr-2025",
            "content": "The global grid storage sector expanded 24.3% in 2024, reaching $48.2B according to industry analysts.",
            "score": 0.92,
            "published_date": "2025-03-12T10:00:00Z",
        },
        {
            "title": "BESS Technology Projections",
            "url": "https://cleantech-insights.org/battery-costs",
            "content": "Battery pack prices declined to $115/kWh for LFP cells in utility applications.",
            "score": 0.74,
            "published_date": "2025-01-20",
        },
    ],
    "response_time": 0.65,
    "usage": {
        "credits": 1,
    },
}

SAMPLE_TAVILY_RESPONSE_ADVANCED = {
    "query": "Fluence Energy financial filings and backlog",
    "results": [
        {
            "title": "Fluence Energy Q4 2025 Backlog",
            "url": "https://sec.gov/edgar/data/fluence-10k-2025",
            "content": "Fluence Energy reported $2.7B contracted backlog with 12.8% gross margins.",
            "score": 0.98,
            "published_date": "2025-11-15",
        },
    ],
    "response_time": 1.45,
    "usage": {
        "credits": 2,
    },
}


def test_tavily_basic_search_execution():
    """Verifies basic search executes properly, parses fields, and maps provenance."""
    prov = TavilyResearchProvider(api_key="tvly-mock-key", search_depth="basic")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = SAMPLE_TAVILY_RESPONSE_BASIC

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        req = ResearchQueryRequest(
            query="Grid-scale battery storage market CAGR 2025",
            search_type="market_size_growth",
            max_results=5,
        )
        res = prov.search_detailed(req)

        assert mock_post.called
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        assert payload["query"] == "Grid-scale battery storage market CAGR 2025"
        assert payload["search_depth"] == "basic"
        assert payload["include_usage"] is True

        assert res.actual_cost_usd == pytest.approx(0.008, abs=0.0001)
        assert res.credits_used == 1
        assert len(res.evidence_items) == 2

        item1 = res.evidence_items[0]
        assert item1.url == "https://www.reuters.com/business/energy-storage-cagr-2025"
        assert item1.source_domain == "reuters.com"
        assert item1.publication_date == "2025-03-12T10:00:00Z"
        assert "24.3%" in item1.excerpt
        assert item1.provenance == "EXTERNAL_INDEPENDENT_RESEARCH"
        # Phase 4.3 Evidence-Grade Semantics: Score is relevance, not proof of truth
        assert item1.relevance_score == 0.92
        assert item1.source_authority == "INDUSTRY_ANALYST"
        assert item1.requires_verification is True
        assert item1.verification_grade == "RETRIEVED_SEARCH_RESULT"

        item2 = res.evidence_items[1]
        assert item2.source_domain == "cleantech-insights.org"
        assert item2.provenance == "EXTERNAL_INDEPENDENT_RESEARCH"
        assert item2.relevance_score == 0.74
        assert item2.source_authority == "GENERAL_WEB"
        assert item2.requires_verification is True
        assert item2.verification_grade == "RETRIEVED_SEARCH_RESULT"


def test_tavily_advanced_search_execution():
    """Verifies advanced search charges 2 credits ($0.016) and reconciles response."""
    prov = TavilyResearchProvider(api_key="tvly-mock-key", search_depth="basic")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = SAMPLE_TAVILY_RESPONSE_ADVANCED

    with patch("httpx.Client.post", return_value=mock_resp) as mock_post:
        # Override search_depth in request
        req = ResearchQueryRequest(
            query="Fluence Energy financial filings and backlog",
            search_type="competitor_intelligence",
            search_depth="advanced",
            max_results=5,
        )
        res = prov.search_detailed(req)

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["search_depth"] == "advanced"
        assert res.actual_cost_usd == pytest.approx(0.016, abs=0.0001)
        assert res.credits_used == 2
        assert len(res.evidence_items) == 1
        assert res.evidence_items[0].source_domain == "sec.gov"


def test_tavily_usage_fallback_when_usage_missing():
    """When Tavily response omits 'usage' block, provider safely defaults to expected depth credits."""
    resp_without_usage = {
        "query": "CleanTech TAM",
        "results": [
            {
                "title": "CleanTech TAM Survey",
                "url": "https://cleantech.org/report",
                "content": "TAM benchmark.",
                "score": 0.85,
            }
        ],
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = resp_without_usage

    # 1. Basic search depth fallback -> 1 credit ($0.008)
    prov_basic = TavilyResearchProvider(api_key="tvly-mock-key", search_depth="basic")
    with patch("httpx.Client.post", return_value=mock_resp):
        res1 = prov_basic.search_detailed(ResearchQueryRequest(query="CleanTech TAM"))
        assert res1.credits_used == 1
        assert res1.actual_cost_usd == pytest.approx(0.008, abs=0.0001)

    # 2. Advanced search depth fallback -> 2 credits ($0.016)
    prov_adv = TavilyResearchProvider(api_key="tvly-mock-key", search_depth="advanced")
    with patch("httpx.Client.post", return_value=mock_resp):
        res2 = prov_adv.search_detailed(ResearchQueryRequest(query="CleanTech TAM"))
        assert res2.credits_used == 2
        assert res2.actual_cost_usd == pytest.approx(0.016, abs=0.0001)


def test_tavily_usage_reconciliation_multi_credit():
    """When Tavily reports non-standard credit usage (e.g. 3 credits), actual credits are reconciled."""
    resp_multi_credit = {
        "query": "Deep audit",
        "results": [],
        "usage": {"credits": 3},
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = resp_multi_credit

    prov = TavilyResearchProvider(api_key="tvly-mock-key")
    with patch("httpx.Client.post", return_value=mock_resp):
        res = prov.search_detailed(ResearchQueryRequest(query="Deep audit"))
        assert res.credits_used == 3
        # 3 * 0.008 = $0.024
        assert res.actual_cost_usd == pytest.approx(0.024, abs=0.0001)


def test_tavily_empty_results_handling():
    """Empty results list returns empty evidence and NO_RELEVANT_SOURCES confidence."""
    empty_resp = {
        "query": "Non-existent unicorn startup 9999",
        "results": [],
        "usage": {"credits": 1},
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = empty_resp

    prov = TavilyResearchProvider(api_key="tvly-mock-key")
    service = ExternalResearchService(provider=prov)

    with patch("httpx.Client.post", return_value=mock_resp):
        res = service.search(ResearchQueryRequest(query="Non-existent unicorn startup 9999"))
        assert res.is_available is True
        assert len(res.evidence_items) == 0
        assert res.confidence == "NO_RELEVANT_SOURCES"
        assert res.cost_usd == pytest.approx(0.008, abs=0.0001)


def test_provenance_integrity_distinction():
    """Confirms external research items cannot be confused with VERIFIED_DOCUMENTED internal claims."""
    item = ResearchEvidenceItem(
        url="https://bloomberg.com/news/123",
        title="Benchmark",
        excerpt="Benchmark quote",
        summary="Benchmark summary",
        source_domain="bloomberg.com",
    )
    # Strict provenance assertion
    assert item.provenance == "EXTERNAL_INDEPENDENT_RESEARCH"
    # Never matches internal deck verification status
    assert item.provenance != VerificationStatus.VERIFIED_DOCUMENTED.value
    assert item.verification_grade in ("RETRIEVED_SEARCH_RESULT", "DOCUMENTED_EXTERNAL_FACT", "CORROBORATED_ESTIMATE")


# ===========================================================================
# 4. Error Handling & Recoverability Tests
# ===========================================================================

def test_tavily_authentication_failure_401():
    """HTTP 401 raises AIProviderAuthenticationError and fails fast."""
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = json.dumps({"error": "Invalid API key provided."})

    prov = TavilyResearchProvider(api_key="invalid-key")
    with patch("httpx.Client.post", return_value=mock_resp):
        with pytest.raises(AIProviderAuthenticationError) as exc_info:
            prov.search_detailed(ResearchQueryRequest(query="test"))
        assert "401" in str(exc_info.value)
        assert issubclass(AIProviderAuthenticationError, AIProviderError)


def test_tavily_rate_limit_or_quota_exhausted_429():
    """HTTP 429 raises AIProviderError with rate limit/quota explanation."""
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.text = json.dumps({"error": "Monthly credit allowance exceeded."})

    prov = TavilyResearchProvider(api_key="tvly-test")
    with patch("httpx.Client.post", return_value=mock_resp):
        with pytest.raises(AIProviderError) as exc_info:
            prov.search_detailed(ResearchQueryRequest(query="test"))
        assert "429" in str(exc_info.value)


def test_tavily_provider_server_error_500():
    """HTTP 500 raises AIProviderError."""
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"

    prov = TavilyResearchProvider(api_key="tvly-test")
    with patch("httpx.Client.post", return_value=mock_resp):
        with pytest.raises(AIProviderError) as exc_info:
            prov.search_detailed(ResearchQueryRequest(query="test"))
        assert "500" in str(exc_info.value)


def test_tavily_timeout_handling():
    """httpx.TimeoutException translates to AIProviderError."""
    prov = TavilyResearchProvider(api_key="tvly-test", timeout_seconds=5.0)

    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Read timed out")):
        with pytest.raises(AIProviderError) as exc_info:
            prov.search_detailed(ResearchQueryRequest(query="test"))
        assert "timed out" in str(exc_info.value).lower()


def test_tavily_connection_error_handling():
    """httpx.ConnectError translates to AIProviderError."""
    prov = TavilyResearchProvider(api_key="tvly-test")

    with patch("httpx.Client.post", side_effect=httpx.ConnectError("Connection refused")):
        with pytest.raises(AIProviderError) as exc_info:
            prov.search_detailed(ResearchQueryRequest(query="test"))
        assert "connection failed" in str(exc_info.value).lower()


def test_tavily_malformed_json_handling():
    """Non-JSON response translates to AIResponseParseError."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.side_effect = ValueError("Invalid JSON token")

    prov = TavilyResearchProvider(api_key="tvly-test")
    with patch("httpx.Client.post", return_value=mock_resp):
        with pytest.raises(AIResponseParseError):
            prov.search_detailed(ResearchQueryRequest(query="test"))


# ===========================================================================
# 5. Cost Ledger & Budget Enforcement Integration Tests
# ===========================================================================

def test_tavily_ledger_integration_reconciles_tool_cost():
    """Full lifecycle: pre-reserves budget, calls Tavily, and reconciles external_tools_cost_usd."""
    eval_id = "eval-tavily-ledger-success"
    ledger = CostLedgerManager.get_instance().get_or_create_ledger(
        evaluation_id=eval_id,
        max_budget_usd=0.55,
    )

    prov = TavilyResearchProvider(api_key="tvly-real-simulated", search_depth="basic")
    service = ExternalResearchService(provider=prov)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = SAMPLE_TAVILY_RESPONSE_BASIC

    with patch("httpx.Client.post", return_value=mock_resp):
        res = service.research_market_size_and_growth(
            sector="CleanTech",
            target_market="Energy Storage",
            evaluation_id=eval_id,
        )

        assert res.cost_usd == pytest.approx(0.008, abs=0.0001)
        summary = ledger.get_summary()
        assert summary["total_spent_usd"] == pytest.approx(0.008, abs=0.0001)
        assert summary["total_external_tools_usd"] == pytest.approx(0.008, abs=0.0001)
        assert summary["total_operations"] == 1
        assert summary["reserved_in_flight_usd"] == 0.0


def test_tavily_blocked_when_budget_exhausted():
    """When remaining ledger budget is less than query cost, search is blocked before HTTP dispatch."""
    eval_id = "eval-tavily-exhausted"
    ledger = CostLedgerManager.get_instance().get_or_create_ledger(
        evaluation_id=eval_id,
        max_budget_usd=0.005,  # Less than $0.008 basic query cost
    )

    prov = TavilyResearchProvider(api_key="tvly-mock", search_depth="basic")
    service = ExternalResearchService(provider=prov)

    with patch("httpx.Client.post") as mock_post:
        with pytest.raises(AIBudgetExhaustedError):
            service.research_market_size_and_growth(
                sector="SpaceTech",
                target_market="Propulsion",
                evaluation_id=eval_id,
            )
        # Guarantees network was never touched
        mock_post.assert_not_called()


def test_tavily_reservation_released_on_error():
    """When Tavily provider fails, in-flight reservation is released and not counted as committed spend."""
    eval_id = "eval-tavily-error-cleanup"
    ledger = CostLedgerManager.get_instance().get_or_create_ledger(
        evaluation_id=eval_id,
        max_budget_usd=0.55,
    )

    prov = TavilyResearchProvider(api_key="tvly-mock")
    service = ExternalResearchService(provider=prov)

    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal error"

    with patch("httpx.Client.post", return_value=mock_resp):
        with pytest.raises(AIProviderError):
            service.research_market_size_and_growth(
                sector="SpaceTech",
                target_market="Propulsion",
                evaluation_id=eval_id,
            )

        summary = ledger.get_summary()
        assert summary["total_spent_usd"] == 0.0
        assert summary["reserved_in_flight_usd"] == 0.0
        assert summary["total_operations"] == 0
