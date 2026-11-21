"""Unit tests for Phase A: Cost Observability and Budget Guards.

All tests run strictly using deterministic mocks without making any paid API calls.
"""

import concurrent.futures
from unittest.mock import patch
import pytest
from litellm import Choices, Message, ModelResponse, Usage
from pydantic import BaseModel

from app.services.ai.cost_ledger import CostLedgerManager, EvaluationCostLedger
from app.services.ai.exceptions import AIBudgetExhaustedError, UnknownModelPricingError
from app.services.ai.litellm import (
    LiteLLMAIGateway,
    LiteLLMGateway,
    evaluation_completion_tokens,
    evaluation_cost,
    evaluation_latency,
    evaluation_prompt_tokens,
    evaluation_total_tokens,
)
from app.services.ai.mock import MockAIGateway
from app.services.ai.pricing import ModelPricing, PricingCatalog, get_pricing_catalog, resolve_cache_attribution
from app.services.ai.router import ModelRouter
from app.services.ai.schemas import AICompletionRequest


class DummyResponseModel(BaseModel):
    message: str = "Test response"
    score: int = 100


class TestPricingCatalog:
    def test_default_model_pricing_rates(self):
        catalog = PricingCatalog(version="2026-10-v1")

        # Claude Sonnet 3.5: $3.00/MTok in, $15.00/MTok out
        cost_sonnet = catalog.calculate_cost(
            model="claude-3-5-sonnet-20241022",
            prompt_tokens=10_000,
            completion_tokens=2_000,
        )
        # Expected: (10,000 * 3.00 + 2,000 * 15.00) / 1,000,000 = (30,000 + 30,000)/1,000,000 = $0.06
        assert cost_sonnet == 0.06

        # Claude Haiku 3.5: $0.80/MTok in, $4.00/MTok out
        cost_haiku = catalog.calculate_cost(
            model="claude-3-5-haiku-20241022",
            prompt_tokens=10_000,
            completion_tokens=2_000,
        )
        # Expected: (10,000 * 0.80 + 2,000 * 4.00) / 1,000,000 = (8,000 + 8,000)/1,000,000 = $0.016
        assert cost_haiku == 0.016

    def test_planning_assumptions_sonnet_5_5_and_haiku_5_5(self):
        catalog = PricingCatalog(version="2026-10-v1")

        # Claude Sonnet 5.5: $2.00/MTok in, $10.00/MTok out
        cost_sonnet_5 = catalog.calculate_cost(
            model="claude-sonnet-5.5",
            prompt_tokens=50_000,
            completion_tokens=5_000,
        )
        # (50,000 * 2.00 + 5,000 * 10.00) / 1,000,000 = (100,000 + 50,000) / 1,000,000 = $0.15
        assert cost_sonnet_5 == 0.15

        # Claude Haiku 5.5: $0.10 in / $0.50 out for <= 100k tokens
        cost_haiku_5 = catalog.calculate_cost(
            model="claude-haiku-5.5",
            prompt_tokens=20_000,
            completion_tokens=4_000,
        )
        # (20,000 * 0.10 + 4,000 * 0.50) / 1,000,000 = (2,000 + 2,000) / 1,000,000 = $0.004
        assert cost_haiku_5 == 0.004

    def test_cached_tokens_rate(self):
        catalog = PricingCatalog(version="2026-10-v1")
        # 10,000 prompt tokens total, of which 8,000 are cached
        cost = catalog.calculate_cost(
            model="claude-3-5-sonnet-20241022",
            prompt_tokens=10_000,
            completion_tokens=1_000,
            cached_tokens=8_000,
            cache_write_tokens=0,
        )
        # Regular prompt: 2,000 * $3.00/M = $0.006
        # Cached prompt: 8,000 * $0.30/M = $0.0024
        # Completion: 1,000 * $15.00/M = $0.015
        # Total = 0.006 + 0.0024 + 0.015 = 0.0234
        assert cost == 0.0234

    def test_inr_conversion_and_buffer(self):
        catalog = PricingCatalog()
        # Conservative reference conversion: $0.55 at exchange rate 96.0 and 1.18 buffer
        cost_usd = 0.55
        raw_inr, buffered_inr = catalog.convert_to_inr(cost_usd, exchange_rate=96.0, buffer_multiplier=1.18)
        # raw_inr = 0.55 * 96.0 = 52.80
        # buffered_inr = 52.80 * 1.18 = 62.304
        assert raw_inr == 52.80
        assert round(buffered_inr, 2) == 62.30
        assert buffered_inr <= 70.0

        # Verify default exchange rate in convert_to_inr is 96.0
        default_raw, default_buffered = catalog.convert_to_inr(cost_usd)
        assert default_raw == 52.80
        assert round(default_buffered, 2) == 62.30

        # Safe override capability: test with custom rate
        custom_raw, custom_buffered = catalog.convert_to_inr(cost_usd, exchange_rate=86.0, buffer_multiplier=1.18)
        assert custom_raw == 47.30
        assert round(custom_buffered, 2) == 55.81

    def test_pricing_catalog_versioning_and_custom_override(self):
        catalog = PricingCatalog(version="2026-11-custom")
        custom_pricing = ModelPricing(
            model_name="custom-model",
            input_cost_per_m=5.00,
            output_cost_per_m=20.00,
        )
        catalog.register_pricing(custom_pricing)
        cost = catalog.calculate_cost("custom-model", 10_000, 1_000)
        assert cost == (10_000 * 5.00 + 1_000 * 20.00) / 1_000_000.0


class TestModelRouter:
    def test_task_based_routing(self):
        router = ModelRouter()

        # Extraction operations route to fast model
        req_extraction = AICompletionRequest(
            system_prompt="",
            user_prompt="",
            operation_type="extraction",
            agent_name="document_extractor",
        )
        assert router.resolve_model(req_extraction) == router.settings.ai_fast_model

        # Reasoning operations route to reasoning model
        req_reasoning = AICompletionRequest(
            system_prompt="",
            user_prompt="",
            operation_type="expert_evaluation",
            agent_name="FounderExpert",
        )
        assert router.resolve_model(req_reasoning) == router.settings.ai_reasoning_model

        # Explicit model override takes highest precedence
        req_override = AICompletionRequest(
            system_prompt="",
            user_prompt="",
            model="custom-override-model",
            operation_type="extraction",
        )
        assert router.resolve_model(req_override) == "custom-override-model"


class TestEvaluationCostLedgerAndBudgetGuards:
    def test_budget_reservation_and_reconciliation(self):
        ledger = EvaluationCostLedger(
            evaluation_id="eval-test-01",
            startup_id="startup-01",
            max_budget_usd=0.55,
        )

        assert ledger.remaining_budget_usd == 0.55

        # Reserve $0.10
        res_id = ledger.reserve_budget(0.10, agent_name="Extractor")
        assert ledger.reserved_usd == 0.10
        assert ledger.remaining_budget_usd == 0.45

        # Reconcile operation with actual $0.08
        record = ledger.reconcile_operation(
            reservation_id=res_id,
            agent_name="Extractor",
            provider="litellm",
            model="claude-3-5-haiku-20241022",
            input_tokens=10_000,
            output_tokens=1_000,
            actual_cost_usd=0.08,
            latency_ms=150.0,
        )

        assert ledger.reserved_usd == 0.0
        assert ledger.spent_usd == 0.08
        assert ledger.remaining_budget_usd == 0.47
        assert record.final_cost_usd == 0.08
        assert record.confidence == "EXACT_REPORTED"

    def test_budget_exhaustion_prevents_subsequent_calls(self):
        ledger = EvaluationCostLedger(
            evaluation_id="eval-test-02",
            max_budget_usd=0.55,
        )

        # First operation spends $0.50
        res1 = ledger.reserve_budget(0.50, agent_name="Agent1")
        ledger.reconcile_operation(
            reservation_id=res1,
            agent_name="Agent1",
            provider="mock",
            model="claude-3-5-sonnet-20241022",
            input_tokens=50_000,
            output_tokens=10_000,
            actual_cost_usd=0.50,
        )

        assert ledger.remaining_budget_usd == 0.05

        # Attempting to reserve $0.10 must raise AIBudgetExhaustedError
        with pytest.raises(AIBudgetExhaustedError) as exc_info:
            ledger.reserve_budget(0.10, agent_name="Agent2")

        assert "exceed budget ceiling" in str(exc_info.value)
        assert ledger.is_exhausted is True

    def test_concurrent_budget_reservations_share_ceiling(self):
        ledger = EvaluationCostLedger(
            evaluation_id="eval-test-concurrent",
            max_budget_usd=0.55,
        )

        # 6 concurrent agents attempting to reserve $0.10 each
        # Total attempted = $0.60 > $0.55 ceiling
        # Exactly 5 should succeed ($0.50 reserved), and 1 must fail with AIBudgetExhaustedError

        success_count = 0
        failure_count = 0

        def try_reserve(idx: int):
            try:
                res = ledger.reserve_budget(0.10, agent_name=f"ExpertAgent_{idx}")
                return True
            except AIBudgetExhaustedError:
                return False

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            results = list(executor.map(try_reserve, range(6)))

        success_count = sum(1 for r in results if r is True)
        failure_count = sum(1 for r in results if r is False)

        assert success_count == 5
        assert failure_count == 1
        assert ledger.reserved_usd == 0.50
        assert ledger.remaining_budget_usd == 0.05

    def test_mock_gateway_enforces_budget_and_records_telemetry(self):
        CostLedgerManager.get_instance().clear_all()
        eval_id = "eval-mock-test"
        gateway = MockAIGateway()

        # Step 1: Normal call under budget
        req1 = AICompletionRequest(
            evaluation_id=eval_id,
            startup_id="startup-123",
            agent_name="FounderExpert",
            operation_type="expert_evaluation",
            system_prompt="Founder evaluation prompt",
            user_prompt="Evaluate founder details",
        )
        res1 = gateway.complete_json(req1, DummyResponseModel)
        assert isinstance(res1.data, DummyResponseModel)
        assert res1.metadata.cost_usd > 0
        assert res1.metadata.evaluation_id == eval_id

        # Verify ledger summary
        ledger = CostLedgerManager.get_instance().get_ledger(eval_id)
        assert ledger is not None
        summary = ledger.get_summary()
        assert summary["total_operations"] == 1
        assert summary["under_max_usd_ceiling"] is True
        assert summary["under_max_inr_ceiling"] is True
        assert summary["exchange_rate"] == 96.0
        assert summary["buffer_multiplier"] == 1.18
        assert "estimated_provider_charge_usd" in summary
        assert "estimated_provider_charge_inr" in summary
        assert "estimated_tax_and_fees_inr" in summary
        assert "final_billed_inr" in summary
        # Verify tax and fees is raw_inr * (1.18 - 1)
        expected_tax = round(summary["total_cost_inr_buffered"] - summary["total_cost_inr_raw"], 4)
        assert summary["estimated_tax_and_fees_inr"] == expected_tax

        # Step 2: Simulate budget exhaustion
        ledger.reserve_budget(round(ledger.remaining_budget_usd - 0.0001, 4), agent_name="ArtificialExhaustion")

        # Next call must be blocked
        req2 = AICompletionRequest(
            evaluation_id=eval_id,
            agent_name="SecondExpert",
            operation_type="expert_evaluation",
            system_prompt="Prompt",
            user_prompt="Prompt text",
        )
        with pytest.raises(AIBudgetExhaustedError):
            gateway.complete_json(req2, DummyResponseModel)

    def test_failed_call_releases_reservation(self):
        ledger = EvaluationCostLedger(evaluation_id="eval-failed-call-test", max_budget_usd=0.55)
        res_id = ledger.reserve_budget(0.25, agent_name="FlakyAgent")
        assert ledger.reserved_usd == 0.25
        assert ledger.spent_usd == 0.0

        # Simulate exception during call -> release reservation
        ledger.release_reservation(res_id)
        assert ledger.reserved_usd == 0.0
        assert ledger.spent_usd == 0.0
        assert ledger.remaining_budget_usd == 0.55

    def test_actual_vs_estimated_cost_precedence_and_retries(self):
        ledger = EvaluationCostLedger(evaluation_id="eval-actual-cost-test", max_budget_usd=0.55, exchange_rate=96.0)
        res_id = ledger.reserve_budget(0.15, agent_name="ReasoningAgent")

        # Reconcile with exact provider reported cost
        record = ledger.reconcile_operation(
            reservation_id=res_id,
            agent_name="ReasoningAgent",
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            input_tokens=5_000,
            output_tokens=1_000,
            cached_tokens=0,
            actual_cost_usd=0.0300,  # Exact provider cost
            retry_count=2,
            latency_ms=1250.0,
            status="SUCCESS",
        )
        assert record.final_cost_usd == 0.0300
        assert record.confidence == "EXACT_REPORTED"
        assert record.retry_count == 2
        assert ledger.spent_usd == 0.0300
        assert ledger.reserved_usd == 0.0

        summary = ledger.get_summary()
        assert summary["total_retries"] == 2
        assert summary["total_spent_usd"] == 0.0300
        # ₹96 * 0.03 = ₹2.88
        assert summary["total_cost_inr_raw"] == 2.88

    def test_buffered_reference_arithmetic_matches_specification(self):
        """Validates reference conversion arithmetic:
        - Provider budget: $0.55 per evaluation
        - Reference conversion: ₹96/USD
        - Existing buffer multiplier: 1.18
        - Buffered reference amount: ₹62.30
        """
        budget_usd = 0.55
        rate = 96.0
        buffer_mult = 1.18

        raw_inr = round(budget_usd * rate, 2)
        assert raw_inr == 52.80

        buffered_inr = round(raw_inr * buffer_mult, 2)
        assert buffered_inr == 62.30
        assert buffered_inr <= 70.0


    def test_haiku_5_5_short_and_long_context_pricing_with_prompt_caching(self):
        """Validates exact Anthropic rates for Claude Haiku 5.5 across 5m and 1h write TTLs:
        <=100k tokens: in $0.10, out $0.50, cache read $0.01, cache write (5m) $0.125, cache write (1h) $0.20
        >100k tokens:  in $0.50, out $2.50, cache read $0.05, cache write (5m) $0.625, cache write (1h) $1.00
        """
        catalog = PricingCatalog()

        # 1. Short context: 50k prompt (20k cached read, 10k cache write, 20k uncached regular), 10k completion
        # Uncached prompt: 50,000 - (20,000 + 10,000) = 20,000 (No token counted twice)
        # Regular input: 20,000 * $0.10 / 1M = $0.00200
        # Cached read:   20,000 * $0.01 / 1M = $0.00020
        # Output:        10,000 * $0.50 / 1M = $0.00500

        # (a) 5-minute TTL write: 10,000 * $0.125 / 1M = $0.00125 -> Total = $0.00845
        cost_5m = catalog.calculate_cost(
            model="claude-haiku-5-5",
            prompt_tokens=50_000,
            completion_tokens=10_000,
            cached_tokens=20_000,
            cache_write_tokens=10_000,
            cache_write_ttl="5m",
        )
        assert cost_5m == 0.00845

        # (b) 1-hour TTL write: 10,000 * $0.20 / 1M = $0.00200 -> Total = $0.00920
        cost_1h = catalog.calculate_cost(
            model="claude-haiku-5-5",
            prompt_tokens=50_000,
            completion_tokens=10_000,
            cached_tokens=20_000,
            cache_write_tokens=10_000,
            cache_write_ttl="1h",
        )
        assert cost_1h == 0.00920

        # (c) Unspecified TTL -> Conservative default uses 1h rate to prevent undercounting
        cost_default = catalog.calculate_cost(
            model="claude-haiku-5-5",
            prompt_tokens=50_000,
            completion_tokens=10_000,
            cached_tokens=20_000,
            cache_write_tokens=10_000,
        )
        assert cost_default == 0.00920

        # 2. Long context (>100k): 150k prompt (50k cached read, 20k cache write, 80k uncached), 10k completion
        # Uncached prompt: 150,000 - (50,000 + 20,000) = 80,000
        # Regular input: 80,000 * $0.50 / 1M = $0.04000
        # Cached read:   50,000 * $0.05 / 1M = $0.00250
        # Output:        10,000 * $2.50 / 1M = $0.02500

        # (a) 5-minute TTL write: 20,000 * $0.625 / 1M = $0.01250 -> Total = $0.08000
        cost_long_5m = catalog.calculate_cost(
            model="claude-haiku-5-5",
            prompt_tokens=150_000,
            completion_tokens=10_000,
            cached_tokens=50_000,
            cache_write_tokens=20_000,
            cache_write_ttl="5m",
        )
        assert cost_long_5m == 0.08000

        # (b) 1-hour TTL write: 20,000 * $1.00 / 1M = $0.02000 -> Total = $0.08750
        cost_long_1h = catalog.calculate_cost(
            model="claude-haiku-5-5",
            prompt_tokens=150_000,
            completion_tokens=10_000,
            cached_tokens=50_000,
            cache_write_tokens=20_000,
            cache_write_ttl="1h",
        )
        assert cost_long_1h == 0.08750

    def test_sonnet_5_5_pricing_with_prompt_caching(self):
        """Validates exact Anthropic rates for Claude Sonnet 5.5 across 5m and 1h write TTLs:
        in $2.00, out $10.00, cache read $0.10, cache write (5m) $2.50, cache write (1h) $4.00
        """
        catalog = PricingCatalog()

        # 100k gross prompt (60k cached read, 20k cache write, 20k uncached regular), 5k completion
        # Regular prompt: 100,000 - (60,000 + 20,000) = 20,000 (No token counted twice)
        # Regular input: 20,000 * $2.00 / 1M = $0.040
        # Cached read:   60,000 * $0.10 / 1M = $0.006
        # Completion:    5,000 * $10.00 / 1M = $0.050

        # (a) 5-minute TTL write: 20,000 * $2.50 / 1M = $0.050 -> Total = $0.146
        cost_5m = catalog.calculate_cost(
            model="claude-sonnet-5-5",
            prompt_tokens=100_000,
            completion_tokens=5_000,
            cached_tokens=60_000,
            cache_write_tokens=20_000,
            cache_write_ttl="5m",
        )
        assert cost_5m == 0.146

        # (b) 1-hour TTL write: 20,000 * $4.00 / 1M = $0.080 -> Total = $0.176
        cost_1h = catalog.calculate_cost(
            model="claude-sonnet-5-5",
            prompt_tokens=100_000,
            completion_tokens=5_000,
            cached_tokens=60_000,
            cache_write_tokens=20_000,
            cache_write_ttl="1h",
        )
        assert cost_1h == 0.176

        # (c) Unspecified TTL -> Conservative policy applies 1-hour rate
        cost_default = catalog.calculate_cost(
            model="claude-sonnet-5-5",
            prompt_tokens=100_000,
            completion_tokens=5_000,
            cached_tokens=60_000,
            cache_write_tokens=20_000,
        )
        assert cost_default == 0.176

    def test_unknown_model_fail_closed_policy(self):
        """Enforces that unknown model IDs raise UnknownModelPricingError and are never silently priced."""
        catalog = PricingCatalog()

        with pytest.raises(UnknownModelPricingError) as exc_info:
            catalog.get_pricing("completely-unknown-model-xyz")
        assert "Fail-closed budget policy rejects unpriced models" in str(exc_info.value)

        with pytest.raises(UnknownModelPricingError):
            catalog.calculate_cost("completely-unknown-model-xyz", 1000, 100)

        with pytest.raises(UnknownModelPricingError):
            catalog.estimate_max_cost("completely-unknown-model-xyz", 1000, 100)

        # Explicit documented fallback policy works only if requested
        fallback = catalog.get_pricing("completely-unknown-model-xyz", allow_fallback=True)
        assert fallback.pricing_status == "CONSERVATIVE_FALLBACK"
        assert fallback.input_cost_per_m == 2.00

    def test_gateway_rejects_unknown_model_before_dispatch(self):
        """Ensures MockAIGateway and LiteLLMGateway reject unknown models before dispatch or reservation."""
        from app.services.ai.litellm import LiteLLMGateway

        req = AICompletionRequest(
            model="unpriced-experimental-model-9000",
            agent_name="tester",
            system_prompt="sys",
            user_prompt="usr",
            evaluation_id="eval-fail-closed-test",
        )

        # Mock gateway rejection
        mock_gw = MockAIGateway()
        with pytest.raises(UnknownModelPricingError):
            mock_gw.complete_json(req, DummyResponseModel)

        # LiteLLM gateway rejection
        litellm_gw = LiteLLMGateway()
        with pytest.raises(UnknownModelPricingError):
            litellm_gw.complete_json(req, DummyResponseModel)

    def test_cache_token_accounting_in_cost_ledger(self):
        """Validates that cached tokens and cache write tokens are tracked in the ledger and reflected in summary telemetry."""
        ledger = EvaluationCostLedger(
            evaluation_id="eval-cache-accounting",
            max_budget_usd=0.55,
        )

        res_id = ledger.reserve_budget(0.05, agent_name="CacheAgent")
        record = ledger.reconcile_operation(
            reservation_id=res_id,
            agent_name="CacheAgent",
            provider="litellm",
            model="claude-sonnet-5-5",
            input_tokens=20_000,
            output_tokens=2_000,
            cached_tokens=15_000,
            cache_write_tokens=5_000,
        )

        assert record.cached_tokens == 15_000
        assert record.cache_write_tokens == 5_000

        summary = ledger.get_summary()
        assert summary["total_cached_tokens"] == 15_000
        assert summary["total_cache_write_tokens"] == 5_000
        assert summary["operations"][0]["cached_tokens"] == 15_000
        assert summary["operations"][0]["cache_write_tokens"] == 5_000

    def test_failed_request_cannot_bypass_or_leak_budget_guard(self):
        """Validates that failed, aborted, or rejected operations release reservations and do not leak budget."""
        ledger = EvaluationCostLedger(
            evaluation_id="eval-leak-prevention",
            max_budget_usd=0.55,
        )

        # Step 1: Reserve budget
        res_id = ledger.reserve_budget(0.20, agent_name="VulnerableAgent")
        assert ledger.reserved_usd == 0.20
        assert ledger.remaining_budget_usd == 0.35

        # Step 2: Simulate failure -> release reservation
        ledger.release_reservation(res_id)
        assert ledger.reserved_usd == 0.0
        assert ledger.spent_usd == 0.0
        assert ledger.remaining_budget_usd == 0.55

        # Step 3: Ensure remaining budget cannot be bypassed (cumulative ceiling strictly maintained)
        res_id2 = ledger.reserve_budget(0.50, agent_name="BigAgent")
        ledger.reconcile_operation(
            reservation_id=res_id2,
            agent_name="BigAgent",
            provider="mock",
            model="mock-model",
            input_tokens=1000,
            output_tokens=1000,
            actual_cost_usd=0.50,
        )
        assert ledger.spent_usd == 0.50
        assert ledger.remaining_budget_usd == 0.05

        with pytest.raises(AIBudgetExhaustedError):
            ledger.reserve_budget(0.10, agent_name="BypassAttempt")

    def test_all_configured_evaluation_models_have_verified_pricing(self):
        """Verifies that all active models configured in Settings have explicit verified pricing entries."""
        from app.core.config import get_settings
        settings = get_settings()
        catalog = PricingCatalog()

        configured_models = [
            settings.litellm_model,
            settings.ai_fast_model,
            settings.ai_reasoning_model,
        ]

        for m in configured_models:
            pricing = catalog.get_pricing(m)
            assert pricing is not None, f"Configured model {m} has no pricing definition"
            assert pricing.is_verified is True, f"Configured model {m} pricing is not verified"
            assert catalog.has_pricing(m) is True

        # Active production models must be active and not deprecated
        assert catalog.get_pricing(settings.ai_fast_model).is_active is True
        assert catalog.get_pricing(settings.ai_fast_model).is_deprecated is False
        assert catalog.get_pricing(settings.ai_reasoning_model).is_active is True
        assert catalog.get_pricing(settings.ai_reasoning_model).is_deprecated is False

    def test_haiku_100k_threshold_rule_includes_cached_tokens(self):
        """Validates that Haiku 5.5's 100k threshold is evaluated against gross prompt length,
        including cached input tokens, strictly adhering to Anthropic's documented rule.
        """
        catalog = PricingCatalog()

        # Case 1: Uncached 80k + Cached Read 30k = 110k total prompt tokens (>100k threshold)
        # Even though uncached is 80k (<=100k), total context exceeds 100k.
        # Tiered rates must apply: in $0.50, cached read $0.05, out $2.50
        # Expected: 80,000 * $0.50/M + 30,000 * $0.05/M + 5,000 * $2.50/M
        #         = $0.04000 + $0.00150 + $0.01250 = $0.05400
        cost_tiered = catalog.calculate_cost(
            model="claude-haiku-5-5",
            prompt_tokens=110_000,
            completion_tokens=5_000,
            cached_tokens=30_000,
            cache_write_tokens=0,
        )
        assert cost_tiered == 0.05400

        # Case 2: Uncached 60k + Cached Read 30k = 90k total prompt tokens (<=100k threshold)
        # Standard rates apply: in $0.10, cached read $0.01, out $0.50
        # Expected: 60,000 * $0.10/M + 30,000 * $0.01/M + 5,000 * $0.50/M
        #         = $0.00600 + $0.00030 + $0.00250 = $0.00880
        cost_standard = catalog.calculate_cost(
            model="claude-haiku-5-5",
            prompt_tokens=90_000,
            completion_tokens=5_000,
            cached_tokens=30_000,
            cache_write_tokens=0,
        )
        assert cost_standard == 0.00880

    def test_both_cache_write_durations_5m_and_1h_all_models(self):
        """Validates explicit separate pricing fields for 5-minute and 1-hour cache writes
        across all models, verifying that a 5-minute price does not infer coverage of a 1-hour write.
        """
        catalog = PricingCatalog()

        # 1. Claude Sonnet 5.5
        sonnet = catalog.get_pricing("claude-sonnet-5-5")
        assert sonnet.cache_write_5m_cost_per_m == 2.50
        assert sonnet.cache_write_1h_cost_per_m == 4.00
        assert sonnet.cache_write_5m_cost_per_m != sonnet.cache_write_1h_cost_per_m

        # 2. Claude Haiku 5.5 (Short Context <=100k)
        haiku = catalog.get_pricing("claude-haiku-5-5")
        assert haiku.cache_write_5m_cost_per_m == 0.125
        assert haiku.cache_write_1h_cost_per_m == 0.20
        assert haiku.cache_write_5m_cost_per_m != haiku.cache_write_1h_cost_per_m

        # 3. Claude Haiku 5.5 (Long Context >100k)
        assert haiku.tier_cache_write_5m_cost_per_m == 0.625
        assert haiku.tier_cache_write_1h_cost_per_m == 1.00
        assert haiku.tier_cache_write_5m_cost_per_m != haiku.tier_cache_write_1h_cost_per_m

        # 4. Retired Claude 3.5 Sonnet
        sonnet_35 = catalog.get_pricing("claude-3-5-sonnet-20241022")
        assert sonnet_35.cache_write_5m_cost_per_m == 3.75
        assert sonnet_35.cache_write_1h_cost_per_m == 6.00

        # 5. Retired Claude 3.5 Haiku
        haiku_35 = catalog.get_pricing("claude-3-5-haiku-20241022")
        assert haiku_35.cache_write_5m_cost_per_m == 1.00
        assert haiku_35.cache_write_1h_cost_per_m == 1.60

    def test_provider_usage_attribution_disambiguation_no_double_counting(self):
        """Validates that provider usage responses with cache_creation_input_tokens
        never double-count written tokens as both regular input and cache write tokens.
        """
        catalog = PricingCatalog()

        # In LiteLLM: usage.prompt_tokens = input_tokens (raw) + cache_creation + cache_read
        # Gross prompt = 5,000, cache_read = 2,000, cache_write = 2,000, completion = 500
        # Net uncached input = 5,000 - (2,000 + 2,000) = 1,000 tokens
        # Cost with Sonnet 5.5 (5m TTL):
        # 1,000 * $2.00/M + 2,000 * $0.10/M + 2,000 * $2.50/M + 500 * $10.00/M
        # = $0.00200 + $0.00020 + $0.00500 + $0.00500 = $0.01220
        cost = catalog.calculate_cost(
            model="claude-sonnet-5-5",
            prompt_tokens=5_000,
            completion_tokens=500,
            cached_tokens=2_000,
            cache_write_tokens=2_000,
            cache_write_ttl="5m",
        )
        assert cost == 0.01220

        # Explicit uncached prompt tokens argument produces identical unambiguous result
        cost_explicit = catalog.calculate_cost(
            model="claude-sonnet-5-5",
            prompt_tokens=0,
            completion_tokens=500,
            cached_tokens=2_000,
            cache_write_tokens=2_000,
            cache_write_ttl="5m",
            uncached_prompt_tokens=1_000,
        )
        assert cost_explicit == 0.01220

    def test_worst_case_reservation_prevents_cache_write_budget_exhaustion(self):
        """Validates that estimate_max_cost reserves at conservative 1-hour cache write rates,
        guaranteeing that in-flight cache writes cannot breach the $0.55 budget ceiling.
        """
        catalog = PricingCatalog()

        # Sonnet 5.5 reservation for 20k prompt tokens and 4k completion tokens:
        # Prompt reserved at max(input $2.00, 1h write $4.00) = $4.00/M
        # Output reserved at $10.00/M
        # Expected reservation: (20,000 * $4.00 + 4,000 * $10.00) / 1M = $0.080 + $0.040 = $0.120
        reservation_usd = catalog.estimate_max_cost(
            model="claude-sonnet-5-5",
            estimated_prompt_tokens=20_000,
            max_completion_tokens=4_000,
        )
        assert reservation_usd == 0.120

        # Actual execution using 5m cache write:
        # Actual cost: (20,000 * $2.50 + 4,000 * $10.00) / 1M = $0.050 + $0.040 = $0.090
        actual_cost = catalog.calculate_cost(
            model="claude-sonnet-5-5",
            prompt_tokens=20_000,
            completion_tokens=4_000,
            cache_write_tokens=20_000,
            cache_write_ttl="5m",
        )
        assert actual_cost == 0.090
        assert reservation_usd >= actual_cost

    def test_shared_evaluation_ledger_across_all_six_domains_extraction_and_supervisory(self):
        """Confirms that extraction, all 6 domain specialists, rechecks, and supervisory review
        share the exact same EvaluationCostLedger instance, and hard budget guards are maintained.
        """
        manager = CostLedgerManager.get_instance()
        eval_id = "eval-shared-lifecycle-audit"

        ledger = manager.get_or_create_ledger(
            evaluation_id=eval_id,
            max_budget_usd=0.55,
        )

        stages = [
            ("document_extractor", "claude-haiku-5-5", 4_000, 1_500, 0, 0),
            ("ProblemSolutionDomainExpert", "claude-sonnet-5-5", 10_000, 2_000, 0, 10_000),
            ("TechnologyTRLDomainExpert", "claude-sonnet-5-5", 10_000, 2_000, 8_000, 0),
            ("MarketCompetitionDomainExpert", "claude-sonnet-5-5", 10_000, 2_000, 8_000, 0),
            ("FoundersTeamDomainExpert", "claude-sonnet-5-5", 10_000, 2_000, 8_000, 0),
            ("BusinessEconomicsDomainExpert", "claude-sonnet-5-5", 10_000, 2_000, 8_000, 0),
            ("DefensibilityImpactDomainExpert", "claude-sonnet-5-5", 10_000, 2_000, 8_000, 0),
            ("targeted_recheck_loop", "claude-sonnet-5-5", 8_000, 1_000, 6_000, 0),
            ("supervisory_reviewer", "claude-sonnet-5-5", 15_000, 3_000, 10_000, 0),
        ]

        for agent_name, model, inp, out, cached, write in stages:
            # All agents obtain the same ledger
            agent_ledger = manager.get_ledger(eval_id)
            assert agent_ledger is ledger

            res_id = agent_ledger.reserve_budget(0.06, agent_name=agent_name)
            agent_ledger.reconcile_operation(
                reservation_id=res_id,
                agent_name=agent_name,
                provider="mock",
                model=model,
                input_tokens=inp,
                output_tokens=out,
                cached_tokens=cached,
                cache_write_tokens=write,
                cache_write_ttl="5m",
            )

        summary = ledger.get_summary()
        assert summary["total_operations"] == 9
        assert summary["is_exhausted"] is False
        assert summary["under_max_usd_ceiling"] is True
        assert summary["total_spent_usd"] < 0.55
        assert summary["total_cached_tokens"] == 56_000
        assert summary["total_cache_write_tokens"] == 10_000
        assert summary["cache_pricing_policy"] == "conservative_1h"

    def test_conservative_cache_pricing_policy_when_ttl_unspecified(self):
        """Validates that when usage cannot distinguish cache write duration,
        the system applies the conservative 1-hour rate so costs are never undercounted.
        """
        catalog = PricingCatalog()

        # Sonnet 5.5: 10k cache write tokens
        # 5m rate = 10,000 * $2.50 / 1M = $0.025
        # 1h rate = 10,000 * $4.00 / 1M = $0.040
        cost_unspecified = catalog.calculate_cost(
            model="claude-sonnet-5-5",
            prompt_tokens=10_000,
            completion_tokens=0,
            cache_write_tokens=10_000,
            cache_write_ttl=None,
        )
        assert cost_unspecified == 0.040

    def test_provider_response_with_both_5m_and_1h_cache_write_tokens(self):
        """Validates that when a provider response exposes separate ephemeral_5m_input_tokens
        and ephemeral_1h_input_tokens within the usage.cache_creation object, both counts are
        preserved, reconciled simultaneously, and billed at their exact respective rates.
        """
        catalog = PricingCatalog()
        ledger = EvaluationCostLedger(
            evaluation_id="eval-split-ttl-test",
            max_budget_usd=0.55,
        )

        class MockCacheCreation:
            ephemeral_5m_input_tokens = 3_000
            ephemeral_1h_input_tokens = 2_000

        class MockUsageWithSplit:
            prompt_tokens = 15_000  # Gross: 6,000 regular + 4,000 cached + 3,000 (5m) + 2,000 (1h)
            completion_tokens = 1_000
            cache_read_input_tokens = 4_000
            cache_creation_input_tokens = 5_000
            cache_creation = MockCacheCreation()

        usage = MockUsageWithSplit()
        w_5m, w_1h, w_total, resolved_ttl = resolve_cache_attribution(
            usage=usage,
            request_metadata={},
            default_ttl="5m",
            pricing_policy="conservative_1h",
        )

        assert w_5m == 3_000
        assert w_1h == 2_000
        assert w_total == 5_000
        assert resolved_ttl == "provider_reported_split"

        res_id = ledger.reserve_budget(0.05, agent_name="SplitAgent")
        record = ledger.reconcile_operation(
            reservation_id=res_id,
            agent_name="SplitAgent",
            provider="mock",
            model="claude-sonnet-5-5",
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            cached_tokens=usage.cache_read_input_tokens,
            cache_write_tokens=w_total,
            cache_write_5m_tokens=w_5m,
            cache_write_1h_tokens=w_1h,
            cache_write_ttl=resolved_ttl,
        )

        # Cost arithmetic for Sonnet 5.5:
        # Regular prompt: 15,000 - (4,000 + 5,000) = 6,000 * $2.00 / 1M = $0.01200
        # Cached read:    4,000 * $0.10 / 1M = $0.00040
        # 5m write:       3,000 * $2.50 / 1M = $0.00750
        # 1h write:       2,000 * $4.00 / 1M = $0.00800
        # Completion:     1,000 * $10.00 / 1M = $0.01000
        # Expected Total: 0.01200 + 0.00040 + 0.00750 + 0.00800 + 0.01000 = $0.03790
        assert record.final_cost_usd == 0.03790
        assert record.cache_write_5m_tokens == 3_000
        assert record.cache_write_1h_tokens == 2_000

        summary = ledger.get_summary()
        assert summary["total_cache_write_5m_tokens"] == 3_000
        assert summary["total_cache_write_1h_tokens"] == 2_000
        assert summary["operations"][0]["cache_write_5m_tokens"] == 3_000
        assert summary["operations"][0]["cache_write_1h_tokens"] == 2_000

    def test_provider_response_with_only_aggregate_cache_write_tokens(self):
        """Validates reconciliation when the provider reports only an aggregate
        cache_creation_input_tokens count, checking both explicit request TTLs (5m and 1h).
        """
        catalog = PricingCatalog()

        class MockAggregateUsage:
            prompt_tokens = 15_000  # Gross: 5k regular + 5k cached + 5k write
            completion_tokens = 1_000
            cache_read_input_tokens = 5_000
            cache_creation_input_tokens = 5_000

        usage = MockAggregateUsage()

        # Case A: Request explicitly configured for 1h TTL
        req_meta_1h = {"cache_control": {"type": "ephemeral", "ttl": "1h"}}
        w_5m, w_1h, w_total, ttl_1h = resolve_cache_attribution(
            usage=usage,
            request_metadata=req_meta_1h,
            default_ttl="5m",
            pricing_policy="conservative_1h",
        )
        assert w_5m == 0
        assert w_1h == 5_000
        assert w_total == 5_000
        assert ttl_1h == "1h"

        cost_1h = catalog.calculate_cost(
            model="claude-sonnet-5-5",
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            cached_tokens=usage.cache_read_input_tokens,
            cache_write_tokens=w_total,
            cache_write_1h_tokens=w_1h,
            cache_write_ttl=ttl_1h,
        )
        # 5k regular * 2.00 + 5k read * 0.10 + 5k write * 4.00 + 1k out * 10.00
        # = 0.01000 + 0.00050 + 0.02000 + 0.01000 = 0.04050
        assert cost_1h == 0.04050

        # Case B: Request explicitly configured for 5m TTL
        req_meta_5m = {"cache_control": {"type": "ephemeral", "ttl": "5m"}}
        w_5m, w_1h, w_total, ttl_5m = resolve_cache_attribution(
            usage=usage,
            request_metadata=req_meta_5m,
            default_ttl="5m",
            pricing_policy="conservative_1h",
        )
        assert w_5m == 5_000
        assert w_1h == 0
        assert ttl_5m == "5m"

        cost_5m = catalog.calculate_cost(
            model="claude-sonnet-5-5",
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            cached_tokens=usage.cache_read_input_tokens,
            cache_write_tokens=w_total,
            cache_write_5m_tokens=w_5m,
            cache_write_ttl=ttl_5m,
        )
        # 5k regular * 2.00 + 5k read * 0.10 + 5k write * 2.50 + 1k out * 10.00
        # = 0.01000 + 0.00050 + 0.01250 + 0.01000 = 0.03300
        assert cost_5m == 0.03300

    def test_configuration_defaults_must_not_bypass_conservative_fallback(self):
        """Validates that when cache write duration is missing or ambiguous,
        the system applies conservative 1-hour pricing and configured defaults
        (such as ai_default_cache_write_ttl='5m') CANNOT inadvertently force 5m pricing.
        """
        catalog = PricingCatalog()

        class MockAmbiguousUsage:
            prompt_tokens = 10_000
            completion_tokens = 1_000
            cache_read_input_tokens = 0
            cache_creation_input_tokens = 5_000

        usage = MockAmbiguousUsage()
        # Request has no explicit TTL declaration
        req_meta_ambiguous = {}

        w_5m, w_1h, w_total, resolved_ttl = resolve_cache_attribution(
            usage=usage,
            request_metadata=req_meta_ambiguous,
            default_ttl="5m",  # static default configured as 5m
            pricing_policy="conservative_1h",  # conservative budget policy
        )

        # Policy guarantee: ambiguous usage maps to 1h rate to prevent undercounting
        assert w_1h == 5_000
        assert w_5m == 0
        assert resolved_ttl == "1h"

        cost = catalog.calculate_cost(
            model="claude-sonnet-5-5",
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            cache_write_tokens=w_total,
            cache_write_1h_tokens=w_1h,
            cache_write_ttl=resolved_ttl,
        )
        # 5k regular * $2.00 + 5k write * $4.00 (1h rate) + 1k out * $10.00
        # = $0.01000 + $0.02000 + $0.01000 = $0.04000
        assert cost == 0.04000
        # Assert it was NOT undercounted at 5m rate ($0.03250)
        assert cost > 0.03250

    def test_response_with_no_cache_write_breakdown(self):
        """Validates reconciliation when the provider response contains no cache write tokens
        at all, ensuring standard prompt tokens and cached reads operate cleanly.
        """
        catalog = PricingCatalog()

        class MockReadOnlyUsage:
            prompt_tokens = 10_000
            completion_tokens = 1_000
            cache_read_input_tokens = 6_000
            cache_creation_input_tokens = 0

        usage = MockReadOnlyUsage()
        w_5m, w_1h, w_total, ttl = resolve_cache_attribution(
            usage=usage,
            request_metadata={},
            default_ttl="5m",
            pricing_policy="conservative_1h",
        )
        assert w_5m == 0
        assert w_1h == 0
        assert w_total == 0

        cost = catalog.calculate_cost(
            model="claude-sonnet-5-5",
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            cached_tokens=usage.cache_read_input_tokens,
            cache_write_tokens=0,
        )
        # 4k regular * 2.00 + 6k read * 0.10 + 1k out * 10.00
        # = 0.00800 + 0.00060 + 0.01000 = 0.01860
        assert cost == 0.01860

    def test_haiku_100k_threshold_with_ttl_split_uses_gross_prompt_length(self):
        """Validates that Haiku 5.5's 100k boundary is evaluated using gross prompt length
        (regular + cached reads + 5m writes + 1h writes), triggering tiered rates across all categories.
        """
        catalog = PricingCatalog()

        # Regular: 70k, Cached Read: 20k, 5m Write: 10k, 1h Write: 5k
        # Gross prompt = 70k + 20k + 10k + 5k = 105,000 tokens (> 100,000 threshold)
        # Tiered rates: in $0.50, cached read $0.05, 5m write $0.625, 1h write $1.00, out $2.50
        cost = catalog.calculate_cost(
            model="claude-haiku-5-5",
            prompt_tokens=105_000,
            completion_tokens=1_000,
            cached_tokens=20_000,
            cache_write_tokens=15_000,
            cache_write_5m_tokens=10_000,
            cache_write_1h_tokens=5_000,
        )

        # Expected:
        # Regular prompt: 105,000 - (20,000 + 15,000) = 70,000 * $0.50/M = $0.03500
        # Cached read:    20,000 * $0.05/M = $0.00100
        # 5m write:       10,000 * $0.625/M = $0.00625
        # 1h write:       5,000 * $1.00/M = $0.00500
        # Output:         1,000 * $2.50/M = $0.00250
        # Total:          0.03500 + 0.00100 + 0.00625 + 0.00500 + 0.00250 = $0.04975
        assert cost == 0.04975

    def test_litellm_gateway_actual_response_aggregate_accounting(self):
        """Gateway-level regression test verifying real installed LiteLLM ModelResponse and Usage:
        1. Missing/mixed TTL breakdown does NOT receive 5m pricing, but is safely priced at 1h rate.
        2. Separate TTL counts are reconciled cleanly when available without double-counting.
        3. Budget ceiling ($0.55 USD) is strictly preserved without leaking reservations.
        """
        # Ensure contextvars are clean
        evaluation_cost.set(0.0)
        evaluation_prompt_tokens.set(0)
        evaluation_completion_tokens.set(0)
        evaluation_total_tokens.set(0)
        evaluation_latency.set(0.0)

        gateway = LiteLLMAIGateway(model="claude-sonnet-5-5", api_key="test-key")

        # ── 1. Mixed / Ambiguous TTL in Real LiteLLM Response ──
        # LiteLLM 1.49.0 constructs Usage with prompt_tokens = (input + creation + read)
        # and leaves cache_creation breakdown absent (aggregate cache_creation_input_tokens only).
        eval_id_mixed = "eval_gw_mixed_ttl_test"
        ledger_mixed = CostLedgerManager.get_instance().get_or_create_ledger(
            evaluation_id=eval_id_mixed,
            max_budget_usd=0.55,
        )

        real_litellm_usage_mixed = Usage(
            prompt_tokens=15_000,  # Gross: 5k regular + 5k cached read + 5k aggregate write
            completion_tokens=1_000,
            total_tokens=16_000,
            cache_creation_input_tokens=5_000,
            cache_read_input_tokens=5_000,
        )
        resp_mixed = ModelResponse(
            id="chatcmpl-gw-mixed",
            choices=[Choices(message=Message(content=DummyResponseModel(message="mixed_ok", score=90).model_dump_json()))],
            created=100001,
            model="claude-sonnet-5-5",
            usage=real_litellm_usage_mixed,
        )

        req_mixed = AICompletionRequest(
            agent_name="MixedTtlAgent",
            evaluation_id=eval_id_mixed,
            system_prompt="Test system prompt",
            user_prompt="Test user prompt",
            metadata={"mixed_ttl": True},  # mixed TTL possible
        )

        with patch("litellm.completion", return_value=resp_mixed):
            res_mixed = gateway.complete_json(req_mixed, DummyResponseModel)

        # Expected Sonnet 5.5 cost at conservative 1h write rate:
        # Regular prompt: 15,000 - (5,000 read + 5,000 write) = 5,000 * $2.00/M = $0.01000
        # Cached read: 5,000 * $0.10/M = $0.00050
        # Cache write: 5,000 * $4.00/M (1h rate) = $0.02000
        # Output: 1,000 * $10.00/M = $0.01000
        # Total cost: 0.01000 + 0.00050 + 0.02000 + 0.01000 = $0.04050
        assert res_mixed.metadata.cost_usd == 0.04050
        # Crucial check: Assert it did NOT receive 5m write pricing ($0.03300)
        assert res_mixed.metadata.cost_usd > 0.03300

        summary_mixed = ledger_mixed.get_summary()
        assert summary_mixed["total_cache_write_1h_tokens"] == 5_000
        assert summary_mixed["total_cache_write_5m_tokens"] == 0
        assert summary_mixed["operations"][0]["cache_write_ttl"] == "1h"
        assert summary_mixed["total_spent_usd"] == 0.04050

        # ── 2. Separate TTL Counts Reconciled When Available ──
        evaluation_cost.set(0.0)
        eval_id_split = "eval_gw_split_test"
        ledger_split = CostLedgerManager.get_instance().get_or_create_ledger(
            evaluation_id=eval_id_split,
            max_budget_usd=0.55,
        )

        real_litellm_usage_split = Usage(
            prompt_tokens=15_000,
            completion_tokens=1_000,
            total_tokens=16_000,
            cache_creation_input_tokens=5_000,
            cache_read_input_tokens=5_000,
        )
        # When provider or future gateway exposes separate breakdowns on usage
        real_litellm_usage_split.ephemeral_5m_input_tokens = 3_000
        real_litellm_usage_split.ephemeral_1h_input_tokens = 2_000

        resp_split = ModelResponse(
            id="chatcmpl-gw-split",
            choices=[Choices(message=Message(content=DummyResponseModel(message="split_ok", score=95).model_dump_json()))],
            created=100002,
            model="claude-sonnet-5-5",
            usage=real_litellm_usage_split,
        )

        req_split = AICompletionRequest(
            agent_name="SplitAgent",
            evaluation_id=eval_id_split,
            system_prompt="Test system prompt",
            user_prompt="Test user prompt",
        )

        with patch("litellm.completion", return_value=resp_split):
            res_split = gateway.complete_json(req_split, DummyResponseModel)

        # Expected Sonnet 5.5 cost with reconciled split:
        # Regular: 5,000 * $2.00/M = $0.01000
        # Cached read: 5,000 * $0.10/M = $0.00050
        # 5m write: 3,000 * $2.50/M = $0.00750
        # 1h write: 2,000 * $4.00/M = $0.00800
        # Output: 1,000 * $10.00/M = $0.01000
        # Total cost: 0.01000 + 0.00050 + 0.00750 + 0.00800 + 0.01000 = $0.03600
        assert res_split.metadata.cost_usd == 0.03600

        summary_split = ledger_split.get_summary()
        assert summary_split["total_cache_write_5m_tokens"] == 3_000
        assert summary_split["total_cache_write_1h_tokens"] == 2_000
        assert summary_split["operations"][0]["cache_write_ttl"] == "provider_reported_split"
        assert summary_split["total_spent_usd"] == 0.03600

        # ── 3. Budget Ceiling ($0.55 USD) Is Strictly Preserved ──
        evaluation_cost.set(0.0)
        eval_id_ceiling = "eval_gw_ceiling_test"
        ledger_ceiling = CostLedgerManager.get_instance().get_or_create_ledger(
            evaluation_id=eval_id_ceiling,
            max_budget_usd=0.55,
        )

        # Pre-commit $0.53 USD in the ledger, leaving only $0.02 remaining
        prior_res = ledger_ceiling.reserve_budget(0.53, agent_name="PriorOperation")
        ledger_ceiling.reconcile_operation(
            reservation_id=prior_res,
            agent_name="PriorOperation",
            provider="litellm",
            model="claude-sonnet-5-5",
            input_tokens=10_000,
            output_tokens=1_000,
            actual_cost_usd=0.53,
        )
        assert ledger_ceiling.spent_usd == 0.53
        assert ledger_ceiling.remaining_budget_usd == 0.02

        # An operation requesting substantial input/output tokens would plan > $0.02
        req_overflow = AICompletionRequest(
            agent_name="OverflowAgent",
            evaluation_id=eval_id_ceiling,
            system_prompt="Massive prompt context " * 500,
            user_prompt="Evaluate entire platform dataset",
            estimated_input_tokens=80_000,
            max_output_tokens=4_096,
        )

        with pytest.raises(AIBudgetExhaustedError) as exc_info:
            gateway.complete_json(req_overflow, DummyResponseModel)

        assert "exceed budget ceiling" in str(exc_info.value).lower() or "budget" in str(exc_info.value).lower()
        # Ensure budget ceiling is not breached and no dangling reservations remain
        assert ledger_ceiling.spent_usd == 0.53
        assert ledger_ceiling.reserved_usd == 0.0
        assert ledger_ceiling.spent_usd <= 0.55

    def test_operation_id_idempotency_across_ledger_and_restore(self):
        """Repeated reconciliation with the same operation_id must never double-charge."""
        ledger = EvaluationCostLedger(evaluation_id="eval-idempotent-01", max_budget_usd=0.55)

        res1 = ledger.reserve_budget(0.05, agent_name="AgentAlpha")
        rec1 = ledger.reconcile_operation(
            reservation_id=res1,
            agent_name="AgentAlpha",
            provider="anthropic",
            model="claude-haiku-5-5",
            input_tokens=1_000,
            output_tokens=200,
            actual_cost_usd=0.04,
            operation_id="op_fixed_123",
        )
        assert ledger.spent_usd == 0.04
        assert ledger.reserved_usd == 0.0
        assert len(ledger.get_summary()["operations"]) == 1

        # Simulate duplicate delivery / replay with a new reservation and identical operation_id
        res2 = ledger.reserve_budget(0.05, agent_name="AgentAlpha")
        rec2 = ledger.reconcile_operation(
            reservation_id=res2,
            agent_name="AgentAlpha",
            provider="anthropic",
            model="claude-haiku-5-5",
            input_tokens=1_000,
            output_tokens=200,
            actual_cost_usd=0.04,
            operation_id="op_fixed_123",
        )
        assert rec2.operation_id == rec1.operation_id == "op_fixed_123"
        assert ledger.spent_usd == 0.04
        assert ledger.reserved_usd == 0.0
        assert len(ledger.get_summary()["operations"]) == 1

        # Restore into fresh ledger and verify idempotency persists across recovery boundary
        summary = ledger.get_summary()
        restored = EvaluationCostLedger(evaluation_id="eval-idempotent-01", max_budget_usd=0.55)
        restored.restore_from_summary(summary)
        res3 = restored.reserve_budget(0.05, agent_name="AgentAlpha")
        rec3 = restored.reconcile_operation(
            reservation_id=res3,
            agent_name="AgentAlpha",
            provider="anthropic",
            model="claude-haiku-5-5",
            input_tokens=1_000,
            output_tokens=200,
            actual_cost_usd=0.04,
            operation_id="op_fixed_123",
        )
        assert rec3.operation_id == "op_fixed_123"
        assert restored.spent_usd == 0.04
        assert restored.reserved_usd == 0.0
        assert len(restored.get_summary()["operations"]) == 1

    def test_exact_budget_boundary_precision_and_overage(self):
        """Exact boundary ($0.53 + $0.02 == $0.55) succeeds; tiny overage raises AIBudgetExhaustedError."""
        ledger = EvaluationCostLedger(evaluation_id="eval-boundary-01", max_budget_usd=0.55)
        res1 = ledger.reserve_budget(0.53, agent_name="AgentBase")
        ledger.reconcile_operation(
            reservation_id=res1,
            agent_name="AgentBase",
            provider="mock",
            model="mock-model",
            input_tokens=100,
            output_tokens=10,
            actual_cost_usd=0.53,
        )

        # Classic IEEE-754 float trap: 0.1 + 0.2 or 0.53 + 0.02
        res_exact = ledger.reserve_budget(0.02, agent_name="ExactBoundaryAgent")
        assert ledger.reserved_usd == 0.02
        assert ledger.remaining_budget_usd == 0.0
        ledger.release_reservation(res_exact)

        with pytest.raises(AIBudgetExhaustedError):
            ledger.reserve_budget(0.020001, agent_name="TinyOverBudgetAgent")

    def test_litellm_timeout_and_malformed_responses_never_leak_reservations(self):
        """Timeouts, truncated outputs, and malformed provider responses release reservations cleanly."""
        from app.services.ai.exceptions import AIProviderError, AIResponseParseError

        CostLedgerManager.get_instance().clear_all()
        gateway = LiteLLMGateway(api_key="test-fake-key", max_retries=0)
        eval_id = "eval-gw-cleanup-01"
        ledger = CostLedgerManager.get_instance().get_or_create_ledger(
            evaluation_id=eval_id,
            max_budget_usd=0.55,
        )

        req = AICompletionRequest(
            agent_name="TimeoutAgent",
            evaluation_id=eval_id,
            system_prompt="System prompt",
            user_prompt="User prompt",
            estimated_input_tokens=500,
            max_output_tokens=200,
        )

        # 1. Timeout exception releases reservation
        with patch("litellm.completion", side_effect=TimeoutError("upstream timed out")):
            with pytest.raises(AIProviderError):
                gateway.complete_json(req, DummyResponseModel)
        assert ledger.reserved_usd == 0.0
        assert ledger.spent_usd == 0.0

        # 2. Malformed response object (missing .choices / attribute error) releases reservation
        bad_resp = object()
        with patch("litellm.completion", return_value=bad_resp):
            with pytest.raises(AIResponseParseError):
                gateway.complete_json(req, DummyResponseModel)
        assert ledger.reserved_usd == 0.0

        # 3. Malformed JSON string reconciles reservation without leaving reserved_usd > 0
        malformed_json_resp = ModelResponse(
            id="chatcmpl-malformed",
            choices=[Choices(message=Message(content="{not valid json"))],
            created=100010,
            model="claude-haiku-5-5",
            usage=Usage(prompt_tokens=100, completion_tokens=20, total_tokens=120),
        )
        with patch("litellm.completion", return_value=malformed_json_resp):
            with pytest.raises(AIResponseParseError):
                gateway.complete_json(req, DummyResponseModel)
        assert ledger.reserved_usd == 0.0

    def test_litellm_restored_ledger_ceiling_and_operation_id_dedup(self):
        """LiteLLM enforces restored ledger ceiling even when evaluation_cost ContextVar starts at 0.0."""
        CostLedgerManager.get_instance().clear_all()
        evaluation_cost.set(0.0)
        gateway = LiteLLMGateway(api_key="test-fake-key", max_retries=0)
        eval_id = "eval-gw-restored-ceiling"
        ledger = CostLedgerManager.get_instance().get_or_create_ledger(
            evaluation_id=eval_id,
            max_budget_usd=0.10,
        )
        ledger.restore_from_summary(
            {
                "total_spent_usd": 0.095,
                "operations": [
                    {
                        "operation_id": "op_restored_01",
                        "agent_name": "PriorAgent",
                        "model": "claude-haiku-5-5",
                        "input_tokens": 1000,
                        "output_tokens": 100,
                        "final_cost_usd": 0.095,
                        "buffered_cost_inr": 10.76,
                    }
                ],
            }
        )

        # Replay of existing operation_id must be idempotent even on restored ledger
        ok_resp = ModelResponse(
            id="chatcmpl-replay",
            choices=[Choices(message=Message(content=DummyResponseModel(message="ok", score=1).model_dump_json()))],
            created=100020,
            model="claude-haiku-5-5",
            usage=Usage(prompt_tokens=500, completion_tokens=50, total_tokens=550),
        )
        replay_req = AICompletionRequest(
            agent_name="PriorAgent",
            evaluation_id=eval_id,
            system_prompt="s",
            user_prompt="u",
            estimated_input_tokens=100,
            max_output_tokens=100,
            metadata={"operation_id": "op_restored_01"},
        )
        with patch("litellm.completion", return_value=ok_resp):
            res = gateway.complete_json(replay_req, DummyResponseModel)
        assert res.metadata.cumulative_cost_usd == 0.095
        assert ledger.spent_usd == 0.095

        # New operation whose actual spend pushes restored $0.095 past $0.10 must abort with AIBudgetExhaustedError
        expensive_resp = ModelResponse(
            id="chatcmpl-over",
            choices=[Choices(message=Message(content=DummyResponseModel(message="over", score=2).model_dump_json()))],
            created=100021,
            model="claude-sonnet-5-5",
            usage=Usage(prompt_tokens=20_000, completion_tokens=1_000, total_tokens=21_000),
        )
        over_req = AICompletionRequest(
            agent_name="OverAgent",
            evaluation_id=eval_id,
            system_prompt="s",
            user_prompt="u",
            estimated_input_tokens=10,
            max_output_tokens=10,
            metadata={"operation_id": "op_new_over"},
        )
        with patch("litellm.completion", return_value=expensive_resp):
            with pytest.raises(AIBudgetExhaustedError):
                gateway.complete_json(over_req, DummyResponseModel)
        assert ledger.reserved_usd == 0.0


