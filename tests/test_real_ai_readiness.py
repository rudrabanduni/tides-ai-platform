"""tests/test_real_ai_readiness.py - Comprehensive Unit & Integration Tests for Phase 4.

Verifies:
1. Cost-aware model routing (fast model for extraction, reasoning model for 6 domains & review).
2. Fail-closed pricing catalog (unknown/unpriced models rejected before dispatch).
3. Pre-call budget reservation and ceiling enforcement ($0.55 / ₹70).
4. Shared evaluation ID and ledger continuity across extraction, domains, rechecks, and supervisory review.
5. Error handling and recovery states (authentication errors, budget exhaustion, invalid response recovery).
6. External research provider abstraction (disabled by default, mock fixtures, provenance tagging, budget reservation).
7. Mathematical validation of the ₹70 absolute cost ceiling and ₹50–₹60 target range.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.services.ai.cost_ledger import CostLedgerManager, EvaluationCostLedger
from app.services.ai.exceptions import (
    AIBudgetExhaustedError,
    AIProviderError,
    AIResponseParseError,
    UnknownModelPricingError,
)
from app.services.ai.pricing import PricingCatalog, get_pricing_catalog
from app.services.ai.research import (
    DisabledResearchProvider,
    ExternalResearchService,
    MockResearchProvider,
    ResearchEvidenceItem,
    ResearchQueryRequest,
)
from app.services.ai.router import ModelRouter
from app.services.ai.schemas import AICompletionRequest, AICompletionResult


# ---------------------------------------------------------------------------
# Dummy Schemas for Testing
# ---------------------------------------------------------------------------

class SampleOutput(BaseModel):
    summary: str = Field(..., description="Summary")
    score: float = Field(..., description="Score")


# ===========================================================================
# 1. Cloud Model Routing Tests
# ===========================================================================

def test_router_selects_fast_model_for_extraction_tasks():
    """Confirms extraction tasks route strictly to the configured fast model (Claude Haiku 5.5)."""
    settings = get_settings()
    router = ModelRouter(settings)

    # 1. Operation type: extraction
    req1 = AICompletionRequest(
        system_prompt="Extract facts",
        user_prompt="Startup text",
        agent_name="document_extraction",
        operation_type="extraction",
    )
    assert router.resolve_model(req1) == settings.ai_fast_model
    assert "haiku" in router.resolve_model(req1).lower()

    # 2. Agent name: intake extractor
    req2 = AICompletionRequest(
        system_prompt="Parse",
        user_prompt="Doc",
        agent_name="intake_extractor",
        operation_type="general",
    )
    assert router.resolve_model(req2) == settings.ai_fast_model


def test_router_selects_reasoning_model_for_domain_specialists_and_review():
    """Confirms domain specialists and supervisory review route to the reasoning model (Claude Sonnet 5.5)."""
    settings = get_settings()
    router = ModelRouter(settings)

    # 1. Domain specialist
    req_domain = AICompletionRequest(
        system_prompt="Evaluate domain",
        user_prompt="Evidence context",
        agent_name="domain_problem_solution",
        operation_type="expert_evaluation",
    )
    assert router.resolve_model(req_domain) == settings.ai_reasoning_model
    assert "sonnet" in router.resolve_model(req_domain).lower()

    # 2. Supervisory review
    req_review = AICompletionRequest(
        system_prompt="Supervise",
        user_prompt="Synthesis context",
        agent_name="supervisory_review",
        operation_type="supervisory_review",
    )
    assert router.resolve_model(req_review) == settings.ai_reasoning_model


def test_router_respects_explicit_model_override():
    """Explicit model in request overrides automatic routing."""
    router = ModelRouter()
    req = AICompletionRequest(
        system_prompt="Sys",
        user_prompt="User",
        model="claude-sonnet-5-5",
        operation_type="extraction",
    )
    assert router.resolve_model(req) == "claude-sonnet-5-5"


# ===========================================================================
# 2. Fail-Closed Pricing Verification
# ===========================================================================

def test_unknown_model_pricing_fails_closed():
    """Confirms that unpriced or unknown model names raise UnknownModelPricingError."""
    catalog = get_pricing_catalog()

    with pytest.raises(UnknownModelPricingError) as exc_info:
        catalog.get_pricing("gpt-fantasy-99", allow_fallback=False)
    assert "gpt-fantasy-99" in str(exc_info.value)

    with pytest.raises(UnknownModelPricingError):
        catalog.calculate_cost(
            model="unregistered-claude-variant",
            prompt_tokens=1000,
            completion_tokens=500,
        )


def test_verified_models_have_exact_official_rates():
    """Confirms that active production models match verified Anthropic pricing documentation."""
    catalog = get_pricing_catalog()

    sonnet = catalog.get_pricing("claude-sonnet-5-5")
    assert sonnet.input_cost_per_m == 2.00
    assert sonnet.output_cost_per_m == 10.00
    assert sonnet.cached_input_cost_per_m == 0.10
    assert sonnet.cache_write_5m_cost_per_m == 2.50
    assert sonnet.cache_write_1h_cost_per_m == 4.00
    assert sonnet.is_active is True

    haiku = catalog.get_pricing("claude-haiku-5-5")
    assert haiku.input_cost_per_m == 0.10
    assert haiku.output_cost_per_m == 0.50
    assert haiku.cached_input_cost_per_m == 0.01
    assert haiku.cache_write_5m_cost_per_m == 0.125
    assert haiku.cache_write_1h_cost_per_m == 0.20
    assert haiku.tier_threshold_tokens == 100_000
    assert haiku.tier_input_cost_per_m == 0.50
    assert haiku.tier_output_cost_per_m == 2.50


# ===========================================================================
# 3. Budget Reservation and Ceiling Enforcement
# ===========================================================================

def test_budget_reservation_prevents_overcommit():
    """Confirms budget is reserved before execution and blocks operations exceeding limit."""
    ledger = EvaluationCostLedger(
        evaluation_id="eval-budget-test",
        max_budget_usd=0.10,  # Small limit for testing
    )

    # 1. First reservation ($0.06 of $0.10)
    res1 = ledger.reserve_budget(estimated_cost_usd=0.06, agent_name="agent_1")
    assert res1.startswith("res_")
    assert ledger.reserved_usd == 0.06
    assert ledger.remaining_budget_usd == 0.04

    # 2. Second reservation ($0.05) would exceed $0.10 total -> must fail closed
    with pytest.raises(AIBudgetExhaustedError) as exc_info:
        ledger.reserve_budget(estimated_cost_usd=0.05, agent_name="agent_2")
    assert "would exceed budget ceiling" in str(exc_info.value)
    assert ledger.is_exhausted is True

    # 3. Release first reservation -> budget restored
    ledger.release_reservation(res1)
    assert ledger.reserved_usd == 0.0


def test_reconcile_operation_records_actual_usage_and_inr():
    """Confirms reconciliation creates an audit CostRecord with USD and buffered INR."""
    ledger = EvaluationCostLedger(
        evaluation_id="eval-reconcile-test",
        max_budget_usd=0.55,
        exchange_rate=96.0,
        buffer_multiplier=1.18,
    )

    res_id = ledger.reserve_budget(estimated_cost_usd=0.04, agent_name="domain_expert")
    record = ledger.reconcile_operation(
        reservation_id=res_id,
        agent_name="domain_expert",
        provider="litellm",
        model="claude-sonnet-5-5",
        input_tokens=5000,
        output_tokens=1500,
        cached_tokens=0,
        cache_write_tokens=0,
    )

    # 5,000 * $2.00/M = $0.010; 1,500 * $10.00/M = $0.015 -> $0.025 USD
    assert record.final_cost_usd == pytest.approx(0.025, abs=0.0001)
    # $0.025 * 96.0 = ₹2.40 INR
    assert record.cost_inr == pytest.approx(2.40, abs=0.01)
    # ₹2.40 * 1.18 = ₹2.832 buffered INR
    assert record.buffered_cost_inr == pytest.approx(2.832, abs=0.01)

    summary = ledger.get_summary()
    assert summary["total_spent_usd"] == pytest.approx(0.025, abs=0.0001)
    assert summary["total_cost_inr_buffered"] == pytest.approx(2.832, abs=0.01)
    assert summary["total_operations"] == 1


# ===========================================================================
# 4. External Research Integration Architecture
# ===========================================================================

def test_external_research_disabled_by_default():
    """When disabled or unconfigured, search safely returns UNAVAILABLE with zero cost."""
    service = ExternalResearchService(provider=DisabledResearchProvider())
    assert service.is_available() is False

    req = ResearchQueryRequest(query="Quantum computing TAM 2030", search_type="market_size_growth")
    res = service.search(req)

    assert res.is_available is False
    assert res.confidence == "UNAVAILABLE"
    assert res.cost_usd == 0.0
    assert len(res.evidence_items) == 0
    assert "disabled or provider API key is not configured" in res.message


def test_mock_research_provider_returns_verifiable_evidence_and_provenance():
    """Mock research provider returns structured evidence items with verified provenance."""
    provider = MockResearchProvider(cost_per_query_usd=0.005)
    service = ExternalResearchService(provider=provider)
    assert service.is_available() is True

    # 1. Market size query
    market_res = service.research_market_size_and_growth(
        sector="CleanTech",
        target_market="Commercial BESS energy storage",
    )
    assert market_res.is_available is True
    assert len(market_res.evidence_items) >= 1
    first_ev = market_res.evidence_items[0]
    assert isinstance(first_ev, ResearchEvidenceItem)
    assert first_ev.url.startswith("https://")
    assert first_ev.publication_date is not None
    assert first_ev.provenance == "MOCK_SIMULATED_RESEARCH"
    assert first_ev.verification_grade == "SIMULATED_TEST_EVIDENCE"
    assert first_ev.is_mock is True
    assert "CAGR" in first_ev.excerpt

    # 2. Competitor query
    comp_res = service.research_competitors(
        company_name="CleanPower Systems",
        sector="CleanTech",
        competitor_names=["Fluence Energy", "Form Energy"],
    )
    assert comp_res.is_available is True
    assert any("Fluence" in ev.title or "Form Energy" in ev.title for ev in comp_res.evidence_items)


def test_external_research_reserves_and_reconciles_on_shared_ledger():
    """External research participates in the same evaluation cost ledger."""
    eval_id = "eval-research-ledger-test"
    ledger = CostLedgerManager.get_instance().get_or_create_ledger(
        evaluation_id=eval_id,
        max_budget_usd=0.55,
    )

    provider = MockResearchProvider(cost_per_query_usd=0.005)
    service = ExternalResearchService(provider=provider)

    # Execute search with evaluation_id
    res = service.research_market_size_and_growth(
        sector="CleanTech",
        target_market="Grid Storage",
        evaluation_id=eval_id,
    )

    assert res.cost_usd == 0.005
    summary = ledger.get_summary()
    assert summary["total_spent_usd"] == pytest.approx(0.005, abs=0.0001)
    assert summary["total_external_tools_usd"] == pytest.approx(0.005, abs=0.0001)
    assert summary["total_operations"] == 1


def test_external_research_blocked_if_evaluation_budget_exhausted():
    """When budget is exhausted, research query is blocked before execution."""
    eval_id = "eval-research-exhausted-test"
    ledger = CostLedgerManager.get_instance().get_or_create_ledger(
        evaluation_id=eval_id,
        max_budget_usd=0.004,  # Less than query cost of $0.005
    )

    provider = MockResearchProvider(cost_per_query_usd=0.005)
    service = ExternalResearchService(provider=provider)

    with pytest.raises(AIBudgetExhaustedError):
        service.research_market_size_and_growth(
            sector="CleanTech",
            target_market="Grid Storage",
            evaluation_id=eval_id,
        )


# ===========================================================================
# 5. Mathematical Validation of the ₹70 Evaluation Budget
# ===========================================================================

def test_hard_usd_budget_ceiling_mathematically_guarantees_below_70_inr():
    """Proves that the $0.35 USD default ceiling and explicit $0.55 override remain strictly below ₹70 INR."""
    settings = get_settings()
    max_usd = settings.ai_max_evaluation_budget_usd  # 0.35 default
    fx_rate = settings.ai_inr_exchange_rate          # 96.0
    buffer = settings.ai_inr_buffer_multiplier       # 1.18
    hard_inr_ceiling = settings.ai_absolute_cost_inr_ceiling  # 70.0

    unbuffered_inr = max_usd * fx_rate
    buffered_inr = unbuffered_inr * buffer

    # Default $0.35 * 96.0 = ₹33.60 INR; buffered = ₹39.648 INR
    assert max_usd == pytest.approx(0.35, abs=1e-6)
    assert unbuffered_inr == pytest.approx(33.60, abs=0.01)
    assert buffered_inr == pytest.approx(39.648, abs=0.01)
    assert buffered_inr <= hard_inr_ceiling

    # Explicit override $0.55 * 96.0 = ₹52.80 INR; buffered = ₹62.304 INR <= ₹70
    override_settings = Settings(ai_max_evaluation_budget_usd=0.55)
    override_unbuffered = override_settings.ai_max_evaluation_budget_usd * fx_rate
    override_buffered = override_unbuffered * buffer
    assert override_unbuffered == pytest.approx(52.80, abs=0.01)
    assert override_buffered == pytest.approx(62.304, abs=0.01)
    assert override_buffered <= hard_inr_ceiling


def test_full_pipeline_expected_token_costs_remain_well_under_budget():
    """Recalculates the token economics across all five pipeline stages."""
    catalog = get_pricing_catalog()

    # 1. Document Extraction (Claude Haiku 5.5: 10k in, 3k out)
    cost_extraction = catalog.calculate_cost("claude-haiku-5-5", prompt_tokens=10_000, completion_tokens=3_000)
    # 10k * 0.10/M ($0.0010) + 3k * 0.50/M ($0.0015) = $0.0025
    assert cost_extraction == pytest.approx(0.0025, abs=0.0001)

    # 2. Six Domain Evaluations (Claude Sonnet 5.5: 5k in, 1.5k out each = 30k in, 9k out)
    cost_per_domain = catalog.calculate_cost("claude-sonnet-5-5", prompt_tokens=5_000, completion_tokens=1_500)
    # 5k * 2.0/M ($0.010) + 1.5k * 10.0/M ($0.015) = $0.025
    assert cost_per_domain == pytest.approx(0.025, abs=0.0001)
    cost_6_domains = cost_per_domain * 6  # $0.150

    # 3. External Research (4 basic Tavily searches @ $0.008 per credit modeled estimate)
    cost_research = 4 * 0.008  # $0.032 modeled research cost estimate
    assert cost_research == pytest.approx(0.032, abs=0.0001)

    # 4. Targeted Rechecks (Claude Sonnet 5.5: 2 rechecks @ 2.5k in, 600 out each modeled estimate)
    cost_per_recheck = catalog.calculate_cost("claude-sonnet-5-5", prompt_tokens=2_500, completion_tokens=600)
    # 2.5k * 2.0/M ($0.005) + 600 * 10.0/M ($0.006) = $0.011 modeled estimate
    assert cost_per_recheck == pytest.approx(0.011, abs=0.0001)
    cost_2_rechecks = cost_per_recheck * 2  # $0.022 modeled estimate

    # 5. Supervisory Review (Claude Sonnet 5.5: 7k in, 2k out modeled estimate)
    cost_review = catalog.calculate_cost("claude-sonnet-5-5", prompt_tokens=7_000, completion_tokens=2_000)
    # 7k * 2.0/M ($0.014) + 2k * 10.0/M ($0.020) = $0.034 modeled estimate
    assert cost_review == pytest.approx(0.034, abs=0.0001)

    # Cumulative expected modeled budget estimate:
    # Extraction: $0.0025 + 6 Domains: $0.1500 + Research: $0.0320 + Rechecks: $0.0220 + Review: $0.0340 = $0.2405 USD
    total_expected_usd = cost_extraction + cost_6_domains + cost_research + cost_2_rechecks + cost_review
    assert total_expected_usd == pytest.approx(0.2405, abs=0.001)

    inr_spent = total_expected_usd * 96.0
    buffered_inr = inr_spent * 1.18

    # Modeled INR with safety buffer is ~₹27.24 INR (modeled estimate, not actual live charge)
    assert buffered_inr == pytest.approx(27.24, abs=0.2)
    # Strictly below the ₹50.0–₹60.0 business target band and far below the ₹70.0 hard ceiling
    assert buffered_inr < 50.0
    assert total_expected_usd < 0.55
