"""readiness.py - Dynamic Live-Readiness Verification & Inspection.

Generates authoritative live-readiness status directly from active platform configuration
and the pricing catalog. Eliminates stale duplicate hardcoded model IDs.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from app.core.config import Settings, get_settings
from app.services.ai.pricing import PricingCatalog, get_pricing_catalog

logger = logging.getLogger(__name__)


def get_live_readiness_report(settings: Settings | None = None) -> Dict[str, Any]:
    """Generates an authoritative live-readiness report directly from active runtime configuration.

    Verifies:
    1. Active Claude model IDs for extraction and reasoning/review.
    2. Pricing catalog entry validity and active (non-deprecated) status.
    3. Evaluation cost ledger budget controls and mathematical INR ceiling guarantees.
    4. Pluggable research provider status.
    5. Non-leaking credential presence flags.
    """
    cfg = settings or get_settings()
    pricing_catalog = get_pricing_catalog(cfg.ai_pricing_catalog_version)

    # 1. Inspect Model IDs
    fast_model = cfg.ai_fast_model
    reasoning_model = cfg.ai_reasoning_model
    litellm_default = cfg.litellm_model

    # 2. Verify Pricing Entries
    fast_pricing = pricing_catalog.get_pricing(fast_model, allow_fallback=False)
    reasoning_pricing = pricing_catalog.get_pricing(reasoning_model, allow_fallback=False)

    models_ready = (
        fast_pricing.is_active
        and not fast_pricing.is_deprecated
        and reasoning_pricing.is_active
        and not reasoning_pricing.is_deprecated
    )

    # 3. Budget & Currency Controls
    max_usd = cfg.ai_max_evaluation_budget_usd
    fx_rate = cfg.ai_inr_exchange_rate
    buffer_mult = cfg.ai_inr_buffer_multiplier
    hard_inr_ceiling = cfg.ai_absolute_cost_inr_ceiling

    unbuffered_inr = round(max_usd * fx_rate, 2)
    buffered_inr = round(unbuffered_inr * buffer_mult, 2)
    budget_guaranteed = buffered_inr <= hard_inr_ceiling

    # 4. Research Provider Configuration
    research_prov = cfg.research_provider
    tavily_configured = bool(cfg.tavily_api_key and cfg.tavily_api_key.strip())

    # 5. Non-leaking Credential Checks
    anthropic_configured = bool(cfg.anthropic_api_key and cfg.anthropic_api_key.strip())

    checks: List[Dict[str, Any]] = [
        {
            "name": "Extraction Model Routing",
            "model_id": fast_model,
            "status": "PASS" if fast_pricing.is_active and not fast_pricing.is_deprecated else "FAIL",
            "rates_usd_per_m": {
                "input": fast_pricing.input_cost_per_m,
                "output": fast_pricing.output_cost_per_m,
            },
            "pricing_status": fast_pricing.pricing_status,
        },
        {
            "name": "Reasoning & Review Model Routing",
            "model_id": reasoning_model,
            "status": "PASS" if reasoning_pricing.is_active and not reasoning_pricing.is_deprecated else "FAIL",
            "rates_usd_per_m": {
                "input": reasoning_pricing.input_cost_per_m,
                "output": reasoning_pricing.output_cost_per_m,
            },
            "pricing_status": reasoning_pricing.pricing_status,
        },
        {
            "name": "Default Gateway Model",
            "model_id": litellm_default,
            "status": "PASS" if litellm_default in (reasoning_model, fast_model) else "INFO",
        },
        {
            "name": "Hard Cost Ceiling Enforcement",
            "max_budget_usd": max_usd,
            "exchange_rate": fx_rate,
            "buffered_inr": buffered_inr,
            "hard_inr_ceiling": hard_inr_ceiling,
            "status": "PASS" if budget_guaranteed else "FAIL",
        },
        {
            "name": "Anthropic API Key Configured",
            "is_configured": anthropic_configured,
            "status": "READY" if anthropic_configured else "SAFELY_EMPTY (OFFLINE MODE)",
        },
        {
            "name": "External Research Provider",
            "configured_provider": research_prov,
            "tavily_key_configured": tavily_configured,
            "status": "READY" if research_prov != "tavily" or tavily_configured else "NEEDS_KEY",
        },
    ]

    all_models_active = all(
        c["status"] == "PASS"
        for c in checks
        if "Model" in c["name"] or "Ceiling" in c["name"]
    )

    return {
        "status": "READY_FOR_CREDENTIALS" if (all_models_active and not anthropic_configured) else ("READY_FOR_LIVE_EVALUATION" if all_models_active else "CONFIGURATION_ERROR"),
        "models": {
            "fast_extraction": {
                "model_id": fast_model,
                "is_active": fast_pricing.is_active,
                "is_deprecated": fast_pricing.is_deprecated,
                "input_cost_per_m": fast_pricing.input_cost_per_m,
                "output_cost_per_m": fast_pricing.output_cost_per_m,
            },
            "reasoning_review": {
                "model_id": reasoning_model,
                "is_active": reasoning_pricing.is_active,
                "is_deprecated": reasoning_pricing.is_deprecated,
                "input_cost_per_m": reasoning_pricing.input_cost_per_m,
                "output_cost_per_m": reasoning_pricing.output_cost_per_m,
            },
            "gateway_default": litellm_default,
        },
        "budget": {
            "max_budget_usd": max_usd,
            "exchange_rate": fx_rate,
            "buffered_multiplier": buffer_mult,
            "buffered_inr": buffered_inr,
            "hard_ceiling_inr": hard_inr_ceiling,
            "mathematically_guaranteed": budget_guaranteed,
        },
        "research": {
            "provider": research_prov,
            "tavily_key_present": tavily_configured,
            "cost_per_query_usd": cfg.tavily_cost_per_credit_usd,
            "max_queries": cfg.research_max_queries_per_eval,
        },
        "credentials": {
            "anthropic_key_present": anthropic_configured,
            "tavily_key_present": tavily_configured,
        },
        "checks": checks,
    }
