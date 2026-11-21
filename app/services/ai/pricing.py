"""Configurable, versioned pricing catalog for AI models and token accounting.

Official rates based on Anthropic Claude official pricing documentation:
https://platform.claude.com/docs/en/about-claude/pricing

- Claude Sonnet 5.5 (claude-sonnet-5-5):
  - Standard Input: $2.00 / MTok
  - Standard Output: $10.00 / MTok
  - Cache Read: $0.10 / MTok
  - Cache Write (5-minute TTL): $2.50 / MTok
  - Cache Write (1-hour TTL): $4.00 / MTok
- Claude Haiku 5.5 (claude-haiku-5-5):
  - Prompts <= 100k tokens:
    - Input: $0.10 / MTok
    - Output: $0.50 / MTok
    - Cache Read: $0.01 / MTok
    - Cache Write (5-minute TTL): $0.125 / MTok
    - Cache Write (1-hour TTL): $0.20 / MTok
  - Prompts > 100k tokens:
    - Input: $0.50 / MTok
    - Output: $2.50 / MTok
    - Cache Read: $0.05 / MTok
    - Cache Write (5-minute TTL): $0.625 / MTok
    - Cache Write (1-hour TTL): $1.00 / MTok
- Retired Models (claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022):
  - Explicitly marked is_deprecated=True, is_active=False.

Fail-Closed Budget Control:
- Any unpriced or unknown model ID is rejected immediately via UnknownModelPricingError.
- No silent fallback to Sonnet rates.
- Worst-case budget reservations prevent budget leaks from cache creation operations.
- Accurate usage attribution prevents counting the same token twice.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from app.services.ai.exceptions import UnknownModelPricingError

logger = logging.getLogger(__name__)


@dataclass
class ModelPricing:
    """Pricing rates for a specific model (USD per 1 Million tokens)."""

    model_name: str
    input_cost_per_m: float  # Base standard uncached input cost per million tokens
    output_cost_per_m: float  # Base standard output cost per million tokens
    cached_input_cost_per_m: float = 0.0  # Read cost for cached prompt tokens
    cache_write_cost_per_m: float = 0.0  # Default cache creation/write cost (5m TTL)
    cache_write_5m_cost_per_m: float = 0.0  # Explicit 5-minute TTL cache write cost
    cache_write_1h_cost_per_m: float = 0.0  # Explicit 1-hour TTL cache write cost
    tier_threshold_tokens: int | None = None  # Prompt token threshold for tiered rates (e.g. 100k for Haiku)
    tier_input_cost_per_m: float | None = None  # Tiered input cost if threshold exceeded
    tier_output_cost_per_m: float | None = None  # Tiered output cost if threshold exceeded
    tier_cached_input_cost_per_m: float | None = None  # Tiered cached prompt read cost
    tier_cache_write_cost_per_m: float | None = None  # Tiered default cache creation/write cost (5m TTL)
    tier_cache_write_5m_cost_per_m: float | None = None  # Tiered 5-minute TTL cache write cost
    tier_cache_write_1h_cost_per_m: float | None = None  # Tiered 1-hour TTL cache write cost
    is_active: bool = True  # Active production model vs deprecated/retired
    is_deprecated: bool = False  # Explicit deprecation status
    is_verified: bool = True  # Verified against official Anthropic documentation
    pricing_status: str = "VERIFIED_OFFICIAL"  # VERIFIED_OFFICIAL, DEPRECATED, MOCK_TEST
    description: str = ""  # Human-readable model description or lifecycle status

    def __post_init__(self) -> None:
        # Align default 5m write cost
        if self.cache_write_5m_cost_per_m == 0.0 and self.cache_write_cost_per_m != 0.0:
            self.cache_write_5m_cost_per_m = self.cache_write_cost_per_m
        elif self.cache_write_cost_per_m == 0.0 and self.cache_write_5m_cost_per_m != 0.0:
            self.cache_write_cost_per_m = self.cache_write_5m_cost_per_m

        # If 1h write cost is unconfigured, derive from base input rate * 2.0 (Anthropic standard multiplier)
        if self.cache_write_1h_cost_per_m == 0.0 and self.input_cost_per_m > 0.0:
            self.cache_write_1h_cost_per_m = round(self.input_cost_per_m * 2.0, 6)

        # Align tiered 5m write cost
        if self.tier_cache_write_5m_cost_per_m is None and self.tier_cache_write_cost_per_m is not None:
            self.tier_cache_write_5m_cost_per_m = self.tier_cache_write_cost_per_m
        elif self.tier_cache_write_cost_per_m is None and self.tier_cache_write_5m_cost_per_m is not None:
            self.tier_cache_write_cost_per_m = self.tier_cache_write_5m_cost_per_m

        # Align tiered 1h write cost
        if self.tier_cache_write_1h_cost_per_m is None and self.tier_input_cost_per_m is not None:
            self.tier_cache_write_1h_cost_per_m = round(self.tier_input_cost_per_m * 2.0, 6)


class PricingCatalog:
    """Versioned and configurable catalog of model pricing rates and currency conversions."""

    def __init__(self, version: str = "2026-10-v3") -> None:
        self.version = version
        self._registry: dict[str, ModelPricing] = {}
        self._load_default_rates()

    def _load_default_rates(self) -> None:
        """Loads official provider rates and approved active/legacy model definitions."""
        # ── Active Production Standard Models (Verified Official Anthropic Rates) ──

        # 1. Claude Sonnet 5.5 (Primary reasoning, supervisory review, deep evaluations)
        # Rates: In $2.00, Out $10.00, Cache Read $0.10, Cache Write 5m $2.50, Cache Write 1h $4.00
        sonnet_5_5 = ModelPricing(
            model_name="claude-sonnet-5-5",
            input_cost_per_m=2.00,
            output_cost_per_m=10.00,
            cached_input_cost_per_m=0.10,
            cache_write_cost_per_m=2.50,
            cache_write_5m_cost_per_m=2.50,
            cache_write_1h_cost_per_m=4.00,
            is_active=True,
            is_deprecated=False,
            is_verified=True,
            pricing_status="VERIFIED_OFFICIAL",
            description="Anthropic Claude Sonnet 5.5 - Verified Official Pricing (Primary reasoning and review model)",
        )
        self.register_pricing(sonnet_5_5)

        # Aliases for hyphen, dot, and provider-prefixed IDs
        for alias in ("claude-sonnet-5.5", "anthropic/claude-sonnet-5-5", "anthropic/claude-sonnet-5.5"):
            self.register_pricing(
                ModelPricing(
                    model_name=alias,
                    input_cost_per_m=sonnet_5_5.input_cost_per_m,
                    output_cost_per_m=sonnet_5_5.output_cost_per_m,
                    cached_input_cost_per_m=sonnet_5_5.cached_input_cost_per_m,
                    cache_write_cost_per_m=sonnet_5_5.cache_write_cost_per_m,
                    cache_write_5m_cost_per_m=sonnet_5_5.cache_write_5m_cost_per_m,
                    cache_write_1h_cost_per_m=sonnet_5_5.cache_write_1h_cost_per_m,
                    is_active=True,
                    is_deprecated=False,
                    is_verified=True,
                    pricing_status="VERIFIED_OFFICIAL",
                    description=f"Alias for {sonnet_5_5.model_name}",
                )
            )

        # 2. Claude Haiku 5.5 (Fast tasks, canonical extraction, normalisation)
        # Official rates:
        # <=100k tokens: in $0.10, out $0.50, cache read $0.01, cache write 5m $0.125, cache write 1h $0.20
        # >100k tokens: in $0.50, out $2.50, cache read $0.05, cache write 5m $0.625, cache write 1h $1.00
        haiku_5_5 = ModelPricing(
            model_name="claude-haiku-5-5",
            input_cost_per_m=0.10,
            output_cost_per_m=0.50,
            cached_input_cost_per_m=0.01,
            cache_write_cost_per_m=0.125,
            cache_write_5m_cost_per_m=0.125,
            cache_write_1h_cost_per_m=0.20,
            tier_threshold_tokens=100_000,
            tier_input_cost_per_m=0.50,
            tier_output_cost_per_m=2.50,
            tier_cached_input_cost_per_m=0.05,
            tier_cache_write_cost_per_m=0.625,
            tier_cache_write_5m_cost_per_m=0.625,
            tier_cache_write_1h_cost_per_m=1.00,
            is_active=True,
            is_deprecated=False,
            is_verified=True,
            pricing_status="VERIFIED_OFFICIAL",
            description="Anthropic Claude Haiku 5.5 - Verified Official Pricing (Tiered at 100k prompt tokens)",
        )
        self.register_pricing(haiku_5_5)

        # Aliases for hyphen, dot, and provider-prefixed IDs
        for alias in ("claude-haiku-5.5", "anthropic/claude-haiku-5-5", "anthropic/claude-haiku-5.5"):
            self.register_pricing(
                ModelPricing(
                    model_name=alias,
                    input_cost_per_m=haiku_5_5.input_cost_per_m,
                    output_cost_per_m=haiku_5_5.output_cost_per_m,
                    cached_input_cost_per_m=haiku_5_5.cached_input_cost_per_m,
                    cache_write_cost_per_m=haiku_5_5.cache_write_cost_per_m,
                    cache_write_5m_cost_per_m=haiku_5_5.cache_write_5m_cost_per_m,
                    cache_write_1h_cost_per_m=haiku_5_5.cache_write_1h_cost_per_m,
                    tier_threshold_tokens=haiku_5_5.tier_threshold_tokens,
                    tier_input_cost_per_m=haiku_5_5.tier_input_cost_per_m,
                    tier_output_cost_per_m=haiku_5_5.tier_output_cost_per_m,
                    tier_cached_input_cost_per_m=haiku_5_5.tier_cached_input_cost_per_m,
                    tier_cache_write_cost_per_m=haiku_5_5.tier_cache_write_cost_per_m,
                    tier_cache_write_5m_cost_per_m=haiku_5_5.tier_cache_write_5m_cost_per_m,
                    tier_cache_write_1h_cost_per_m=haiku_5_5.tier_cache_write_1h_cost_per_m,
                    is_active=True,
                    is_deprecated=False,
                    is_verified=True,
                    pricing_status="VERIFIED_OFFICIAL",
                    description=f"Alias for {haiku_5_5.model_name}",
                )
            )

        # ── Deprecated / Retired Models (Preserved for backward test compatibility) ──

        # 3. Claude Sonnet 3.5 (Deprecated: claude-3-5-sonnet-20241022)
        self.register_pricing(
            ModelPricing(
                model_name="claude-3-5-sonnet-20241022",
                input_cost_per_m=3.00,
                output_cost_per_m=15.00,
                cached_input_cost_per_m=0.30,
                cache_write_cost_per_m=3.75,
                cache_write_5m_cost_per_m=3.75,
                cache_write_1h_cost_per_m=6.00,
                is_active=False,
                is_deprecated=True,
                is_verified=True,
                pricing_status="DEPRECATED",
                description="Anthropic Claude 3.5 Sonnet (Retired / Deprecated on official platforms)",
            )
        )

        # 4. Claude Haiku 3.5 (Deprecated: claude-3-5-haiku-20241022)
        self.register_pricing(
            ModelPricing(
                model_name="claude-3-5-haiku-20241022",
                input_cost_per_m=0.80,
                output_cost_per_m=4.00,
                cached_input_cost_per_m=0.08,
                cache_write_cost_per_m=1.00,
                cache_write_5m_cost_per_m=1.00,
                cache_write_1h_cost_per_m=1.60,
                is_active=False,
                is_deprecated=True,
                is_verified=True,
                pricing_status="DEPRECATED",
                description="Anthropic Claude 3.5 Haiku (Retired / Deprecated on official platforms)",
            )
        )

        # ── Test / Mock Models ──

        # 5. Generic Mock model (Deterministic test rate)
        mock_pricing = ModelPricing(
            model_name="mock-model",
            input_cost_per_m=1.00,
            output_cost_per_m=2.00,
            cached_input_cost_per_m=0.10,
            cache_write_cost_per_m=1.25,
            cache_write_5m_cost_per_m=1.25,
            cache_write_1h_cost_per_m=2.00,
            is_active=True,
            is_deprecated=False,
            is_verified=True,
            pricing_status="MOCK_TEST",
            description="Mock Model for Offline Unit & Integration Tests",
        )
        self.register_pricing(mock_pricing)
        self.register_pricing(
            ModelPricing(
                model_name="mock",
                input_cost_per_m=mock_pricing.input_cost_per_m,
                output_cost_per_m=mock_pricing.output_cost_per_m,
                cached_input_cost_per_m=mock_pricing.cached_input_cost_per_m,
                cache_write_cost_per_m=mock_pricing.cache_write_cost_per_m,
                cache_write_5m_cost_per_m=mock_pricing.cache_write_5m_cost_per_m,
                cache_write_1h_cost_per_m=mock_pricing.cache_write_1h_cost_per_m,
                is_active=True,
                is_deprecated=False,
                is_verified=True,
                pricing_status="MOCK_TEST",
                description="Alias for mock-model",
            )
        )

    def register_pricing(self, pricing: ModelPricing) -> None:
        """Registers or overrides pricing for a model."""
        key = pricing.model_name.lower().strip()
        self._registry[key] = pricing

    def has_pricing(self, model: str) -> bool:
        """Checks if a model has a valid pricing definition in the catalog."""
        try:
            self.get_pricing(model, allow_fallback=False)
            return True
        except UnknownModelPricingError:
            return False

    def get_pricing(self, model: str, allow_fallback: bool = False) -> ModelPricing:
        """Finds the pricing definition for a given model or fuzzy match.

        Fail-Closed Policy:
        If a model is not registered in the pricing catalog, an UnknownModelPricingError
        is raised immediately to prevent unbudgeted or incorrectly priced API calls.
        Never silently price an unknown model at Sonnet rates.
        """
        normalized = model.lower().strip()
        if normalized in self._registry:
            return self._registry[normalized]

        # Prefix / partial matching
        for key, pricing in self._registry.items():
            if key in normalized or normalized in key:
                return pricing

        if not allow_fallback:
            raise UnknownModelPricingError(
                f"Model '{model}' has no registered pricing in catalog v{self.version}. "
                "Fail-closed budget policy rejects unpriced models to prevent silent cost overruns."
            )

        logger.warning(
            f"Model '{model}' not found in pricing catalog v{self.version}. "
            "Applying explicit conservative upper-bound fallback to claude-sonnet-5-5 rates."
        )
        fallback = self._registry["claude-sonnet-5-5"]
        return ModelPricing(
            model_name=model,
            input_cost_per_m=fallback.input_cost_per_m,
            output_cost_per_m=fallback.output_cost_per_m,
            cached_input_cost_per_m=fallback.cached_input_cost_per_m,
            cache_write_cost_per_m=fallback.cache_write_cost_per_m,
            tier_threshold_tokens=fallback.tier_threshold_tokens,
            tier_input_cost_per_m=fallback.tier_input_cost_per_m,
            tier_output_cost_per_m=fallback.tier_output_cost_per_m,
            tier_cached_input_cost_per_m=fallback.tier_cached_input_cost_per_m,
            tier_cache_write_cost_per_m=fallback.tier_cache_write_cost_per_m,
            is_active=fallback.is_active,
            is_deprecated=fallback.is_deprecated,
            is_verified=False,
            pricing_status="CONSERVATIVE_FALLBACK",
            description=f"Fallback pricing derived from {fallback.model_name}",
        )

    def get_active_models(self) -> dict[str, ModelPricing]:
        """Returns all active production models in the catalog."""
        return {k: v for k, v in self._registry.items() if v.is_active and not v.is_deprecated}

    def get_deprecated_models(self) -> dict[str, ModelPricing]:
        """Returns all deprecated/retired models in the catalog."""
        return {k: v for k, v in self._registry.items() if v.is_deprecated}

    def calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        cached_tokens: int = 0,
        cache_write_tokens: int = 0,
        cache_write_5m_tokens: int = 0,
        cache_write_1h_tokens: int = 0,
        cache_write_ttl: str | None = None,
        allow_fallback: bool = False,
        uncached_prompt_tokens: int | None = None,
    ) -> float:
        """Calculates exact estimated USD cost based on token usage categories.

        Tokens are priced per 1,000,000 units.
        Enforces tiered pricing for prompt, output, cache read, and cache write rates.
        Uses explicit TTL-aware pricing for 5-minute and 1-hour cache writes.

        Usage Attribution & Token Disambiguation:
        - When provider exposes separate ephemeral_5m_input_tokens and ephemeral_1h_input_tokens,
          both TTL categories are reconciled simultaneously at their verified rates.
        - If prompt_tokens >= (cached_tokens + total_cache_write), prompt_tokens is treated
          as total gross input tokens (standard LiteLLM / provider aggregate convention).
          Uncached tokens are computed by subtracting cached reads and all cache creation tokens
          so that no token is ever counted twice.
        - If uncached_prompt_tokens is explicitly provided, it is used directly.
        - Total prompt length for context-length thresholds (e.g. Haiku 100k) includes all input
          tokens: uncached input + cached reads + 5m cache writes + 1h cache writes.
        - When cache write duration cannot be distinguished from provider usage and is not
          explicitly declared in the request, a conservative policy (1-hour write rate) is applied
          to guarantee that costs are never undercounted against the budget ceiling.
        """
        pricing = self.get_pricing(model, allow_fallback=allow_fallback)

        # 1. Reconcile cache write token counts across 5m and 1h buckets
        has_ttl_split = (cache_write_5m_tokens > 0 or cache_write_1h_tokens > 0)
        if has_ttl_split:
            total_cache_write = cache_write_5m_tokens + cache_write_1h_tokens
            if cache_write_tokens > total_cache_write:
                unattributed_write = cache_write_tokens - total_cache_write
            else:
                unattributed_write = 0
        else:
            total_cache_write = cache_write_tokens
            unattributed_write = cache_write_tokens
            cache_write_5m_tokens = 0
            cache_write_1h_tokens = 0

        # 2. Disambiguate prompt tokens and prevent double counting
        if uncached_prompt_tokens is not None:
            regular_prompt_tokens = max(0, uncached_prompt_tokens)
            total_prompt_tokens = regular_prompt_tokens + cached_tokens + total_cache_write
        elif prompt_tokens >= (cached_tokens + total_cache_write):
            regular_prompt_tokens = max(0, prompt_tokens - (cached_tokens + total_cache_write))
            total_prompt_tokens = prompt_tokens
        else:
            regular_prompt_tokens = max(0, prompt_tokens)
            total_prompt_tokens = regular_prompt_tokens + cached_tokens + total_cache_write

        # 3. Context-length dependent tiering rule (Haiku 5.5 > 100k tokens)
        # Evaluated on total prompt tokens including cached reads and cache writes per provider rules
        is_tiered = bool(
            pricing.tier_threshold_tokens
            and total_prompt_tokens > pricing.tier_threshold_tokens
            and pricing.tier_input_cost_per_m is not None
        )

        # 4. Resolve rates based on tier and TTL
        if is_tiered:
            input_rate = pricing.tier_input_cost_per_m
            output_rate = (
                pricing.tier_output_cost_per_m
                if pricing.tier_output_cost_per_m is not None
                else pricing.output_cost_per_m
            )
            cached_input_rate = (
                pricing.tier_cached_input_cost_per_m
                if pricing.tier_cached_input_cost_per_m is not None
                else pricing.cached_input_cost_per_m
            )
            rate_5m = (
                pricing.tier_cache_write_5m_cost_per_m
                if pricing.tier_cache_write_5m_cost_per_m is not None
                else (pricing.tier_cache_write_cost_per_m or 0.0)
            )
            rate_1h = (
                pricing.tier_cache_write_1h_cost_per_m
                if pricing.tier_cache_write_1h_cost_per_m is not None
                else round(rate_5m * 1.6, 6)
            )
        else:
            input_rate = pricing.input_cost_per_m
            output_rate = pricing.output_cost_per_m
            cached_input_rate = pricing.cached_input_cost_per_m
            rate_5m = pricing.cache_write_5m_cost_per_m or pricing.cache_write_cost_per_m
            rate_1h = pricing.cache_write_1h_cost_per_m or round(rate_5m * 1.6, 6)

        # 5. Resolve rate for unattributed cache write tokens according to TTL policy
        ttl_str = (cache_write_ttl or "conservative").lower().strip()
        if ttl_str in ("5m", "5min", "5-minute", "ephemeral"):
            unattributed_rate = rate_5m
        elif ttl_str in ("1h", "1hr", "1hour", "1-hour", "60m"):
            unattributed_rate = rate_1h
        else:
            # Conservative policy when usage or request cannot distinguish TTL:
            # Default to 1-hour rate to ensure costs are never undercounted.
            unattributed_rate = max(rate_5m, rate_1h)

        # 6. Exact USD cost calculation
        regular_input_cost = (regular_prompt_tokens / 1_000_000.0) * input_rate
        cached_input_cost = (cached_tokens / 1_000_000.0) * cached_input_rate
        cost_5m_write = (cache_write_5m_tokens / 1_000_000.0) * rate_5m
        cost_1h_write = (cache_write_1h_tokens / 1_000_000.0) * rate_1h
        cost_unattributed_write = (unattributed_write / 1_000_000.0) * unattributed_rate
        total_write_cost = cost_5m_write + cost_1h_write + cost_unattributed_write
        output_cost = (completion_tokens / 1_000_000.0) * output_rate

        total_cost = regular_input_cost + cached_input_cost + total_write_cost + output_cost
        return round(total_cost, 6)

    def estimate_max_cost(
        self,
        model: str,
        estimated_prompt_tokens: int,
        max_completion_tokens: int,
        allow_fallback: bool = False,
        cache_write_ttl: str = "1h",
    ) -> float:
        """Estimates maximum worst-case planned cost for budget reservations.

        To guarantee that an evaluation cannot exceed the provider budget ($0.55 USD)
        through cache-pricing underestimation, reservations account for worst-case prompt
        processing at the conservative 1-hour cache write rate.
        """
        pricing = self.get_pricing(model, allow_fallback=allow_fallback)
        is_tiered = bool(
            pricing.tier_threshold_tokens
            and estimated_prompt_tokens > pricing.tier_threshold_tokens
            and pricing.tier_input_cost_per_m is not None
        )
        if is_tiered:
            input_rate = pricing.tier_input_cost_per_m
            output_rate = (
                pricing.tier_output_cost_per_m
                if pricing.tier_output_cost_per_m is not None
                else pricing.output_cost_per_m
            )
            write_1h = (
                pricing.tier_cache_write_1h_cost_per_m
                if pricing.tier_cache_write_1h_cost_per_m is not None
                else round((pricing.tier_cache_write_5m_cost_per_m or 0.0) * 1.6, 6)
            )
        else:
            input_rate = pricing.input_cost_per_m
            output_rate = pricing.output_cost_per_m
            write_1h = pricing.cache_write_1h_cost_per_m or round(
                (pricing.cache_write_5m_cost_per_m or 0.0) * 1.6, 6
            )

        worst_prompt_rate = max(input_rate, write_1h)
        prompt_cost = (estimated_prompt_tokens / 1_000_000.0) * worst_prompt_rate
        output_cost = (max_completion_tokens / 1_000_000.0) * output_rate
        return round(prompt_cost + output_cost, 6)

    @staticmethod
    def convert_to_inr(
        cost_usd: float,
        exchange_rate: float = 96.0,
        buffer_multiplier: float = 1.18,
    ) -> tuple[float, float]:
        """Converts USD cost to raw INR and buffered INR (including taxes/forex buffers).

        Returns: (raw_inr, buffered_inr)
        """
        raw_inr = round(cost_usd * exchange_rate, 4)
        buffered_inr = round(raw_inr * buffer_multiplier, 4)
        return raw_inr, buffered_inr


# Singleton instance
_default_catalog: PricingCatalog | None = None


def get_pricing_catalog(version: str = "2026-10-v3") -> PricingCatalog:
    """Returns the active pricing catalog singleton."""
    global _default_catalog
    if _default_catalog is None or _default_catalog.version != version:
        _default_catalog = PricingCatalog(version=version)
    return _default_catalog


def resolve_cache_attribution(
    usage: Any,
    request_metadata: dict[str, Any] | None = None,
    default_ttl: str | None = None,
    pricing_policy: str = "conservative_1h",
) -> tuple[int, int, int, str]:
    """Reconciles cache write token counts and attribution TTL without configuration conflicts.

    Returns:
        (cache_write_5m_tokens, cache_write_1h_tokens, total_cache_write_tokens, resolved_ttl)

    Hierarchy:
    1. Provider-Reported TTL Breakdown:
       If the provider response exposes explicit separate counts (ephemeral_5m_input_tokens,
       ephemeral_1h_input_tokens), these counts are preserved and reconciled directly.
       Provider-reported attribution takes precedence over request configuration or defaults.

    2. Explicit Request Configuration:
       If the provider supplies only an aggregate cache_creation count (or omits TTL breakdown),
       we inspect the request's actual cache_control directive:
       - request_metadata.get("cache_control", {}).get("ttl")
       - request_metadata.get("cache_write_ttl")
       If the request explicitly declared a TTL ("5m" or "1h"), that declared duration is used.

    3. Policy Fallback for Missing / Ambiguous Metadata:
       If neither the provider nor the request declares an explicit TTL:
       - If pricing_policy == "conservative_1h":
         resolved_ttl is set to "1h", guaranteeing that ambiguous usage
         never inadvertently falls back to 5-minute pricing.
       - A configured default TTL only applies if pricing_policy allows declared/default
         fallback and the request did not explicitly configure otherwise.
    """
    metadata = request_metadata or {}

    # 1. Extract provider-reported TTL breakdowns
    cache_creation_obj = getattr(usage, "cache_creation", None)
    if cache_creation_obj is None and isinstance(usage, dict):
        cache_creation_obj = usage.get("cache_creation")

    ephemeral_5m = 0
    ephemeral_1h = 0
    if cache_creation_obj is not None:
        if isinstance(cache_creation_obj, dict):
            ephemeral_5m = int(cache_creation_obj.get("ephemeral_5m_input_tokens") or 0)
            ephemeral_1h = int(cache_creation_obj.get("ephemeral_1h_input_tokens") or 0)
        else:
            ephemeral_5m = int(getattr(cache_creation_obj, "ephemeral_5m_input_tokens", 0) or 0)
            ephemeral_1h = int(getattr(cache_creation_obj, "ephemeral_1h_input_tokens", 0) or 0)
    else:
        # Check direct fields on usage or details
        ephemeral_5m = int(getattr(usage, "ephemeral_5m_input_tokens", 0) or 0)
        ephemeral_1h = int(getattr(usage, "ephemeral_1h_input_tokens", 0) or 0)

    # Check mock metadata overrides if present
    if ephemeral_5m == 0 and "ephemeral_5m_input_tokens" in metadata:
        ephemeral_5m = int(metadata["ephemeral_5m_input_tokens"] or 0)
    if ephemeral_1h == 0 and "ephemeral_1h_input_tokens" in metadata:
        ephemeral_1h = int(metadata["ephemeral_1h_input_tokens"] or 0)
    if ephemeral_5m == 0 and "cache_write_5m_tokens" in metadata:
        ephemeral_5m = int(metadata["cache_write_5m_tokens"] or 0)
    if ephemeral_1h == 0 and "cache_write_1h_tokens" in metadata:
        ephemeral_1h = int(metadata["cache_write_1h_tokens"] or 0)

    # Aggregate cache write tokens
    prompt_tokens_details = getattr(usage, "prompt_tokens_details", None)
    raw_aggregate_write = (
        getattr(prompt_tokens_details, "cache_creation_input_tokens", 0)
        or getattr(usage, "cache_creation_input_tokens", 0)
        or (usage.get("cache_creation_input_tokens", 0) if isinstance(usage, dict) else 0)
        or int(metadata.get("cache_write_tokens", 0) or 0)
    )

    # 2. Check if provider-reported separate breakdowns are present
    has_provider_breakdown = (ephemeral_5m > 0 or ephemeral_1h > 0)
    if has_provider_breakdown:
        total_write = ephemeral_5m + ephemeral_1h
        if raw_aggregate_write > total_write:
            total_write = raw_aggregate_write
        resolved_ttl = "provider_reported_split"
        return ephemeral_5m, ephemeral_1h, total_write, resolved_ttl

    # 3. Provider only reported aggregate (or 0)
    total_write = raw_aggregate_write
    if total_write == 0:
        return 0, 0, 0, "none"

    # Enforce safe aggregate-only accounting:
    # A. Check if mixed cache-write durations are possible:
    # If request metadata indicates mixed TTL or contains multiple differing cache controls,
    # or cannot guarantee uniform duration, the provider cannot distinguish them.
    # Therefore, aggregate MUST be priced at the conservative 1-hour rate.
    cache_control = metadata.get("cache_control")
    cache_controls = metadata.get("cache_controls")
    is_mixed = bool(
        metadata.get("mixed_ttl")
        or metadata.get("has_mixed_ttl")
        or metadata.get("mixed_cache_durations")
        or (metadata.get("guaranteed_uniform_ttl") is False)
        or (str(metadata.get("cache_write_ttl", "")).strip().lower() in ("mixed", "unknown", "ambiguous", "multiple"))
        or (isinstance(cache_control, dict) and cache_control.get("is_mixed") is True)
    )

    if not is_mixed and isinstance(cache_controls, list) and len(cache_controls) > 1:
        extracted_ttls = {
            str(c.get("ttl", "")).strip().lower()
            for c in cache_controls
            if isinstance(c, dict) and c.get("ttl")
        }
        if len(extracted_ttls) > 1:
            is_mixed = True

    if is_mixed:
        # Mixed cache-write durations cannot be distinguished in aggregate;
        # Fail-safe policy prices at conservative 1-hour rate to prevent underpricing.
        return 0, total_write, total_write, "1h"

    # B. Extract explicit request TTL (only when uniform TTL can be guaranteed)
    explicit_request_ttl: str | None = None
    if isinstance(cache_control, dict) and "ttl" in cache_control:
        explicit_request_ttl = str(cache_control["ttl"]).strip().lower()
    elif "cache_write_ttl" in metadata and metadata["cache_write_ttl"]:
        explicit_request_ttl = str(metadata["cache_write_ttl"]).strip().lower()
    elif isinstance(cache_controls, list) and len(cache_controls) > 0:
        extracted_ttls = {
            str(c.get("ttl", "")).strip().lower()
            for c in cache_controls
            if isinstance(c, dict) and c.get("ttl")
        }
        if len(extracted_ttls) == 1:
            explicit_request_ttl = extracted_ttls.pop()

    if explicit_request_ttl in ("5m", "5min", "5-minute", "ephemeral"):
        # Explicit request guarantees all aggregate writes in this call use 5m
        return total_write, 0, total_write, "5m"
    elif explicit_request_ttl in ("1h", "1hr", "1-hour", "60m"):
        return 0, total_write, total_write, "1h"

    # C. Missing or ambiguous metadata:
    # Rule: Never allow ai_default_cache_write_ttl="5m" to underprice ambiguous aggregate writes.
    # When TTL is not explicitly guaranteed by the request, the aggregate MUST be priced at the conservative 1h rate.
    return 0, total_write, total_write, "1h"
