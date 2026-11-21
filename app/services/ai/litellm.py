from __future__ import annotations

import contextvars
import json
import logging
import math
import os
import re
import time
from typing import Any, TypeVar

import litellm
from pydantic import BaseModel, ValidationError

from app.core.config import get_settings
from app.services.ai.cost_ledger import CostLedgerManager, EvaluationCostLedger
from app.services.ai.exceptions import AIBudgetExhaustedError, AIProviderError, AIResponseParseError
from app.services.ai.pricing import get_pricing_catalog, resolve_cache_attribution
from app.services.ai.router import ModelRouter
from app.services.ai.schemas import AICompletionMetadata, AICompletionRequest, AICompletionResult

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)

# Context variables to track cumulative metrics per evaluation (backward compatibility)
evaluation_prompt_tokens = contextvars.ContextVar("evaluation_prompt_tokens", default=0)
evaluation_completion_tokens = contextvars.ContextVar("evaluation_completion_tokens", default=0)
evaluation_total_tokens = contextvars.ContextVar("evaluation_total_tokens", default=0)
evaluation_cost = contextvars.ContextVar("evaluation_cost", default=0.0)
evaluation_latency = contextvars.ContextVar("evaluation_latency", default=0.0)


def reset_evaluation_metrics() -> None:
    evaluation_prompt_tokens.set(0)
    evaluation_completion_tokens.set(0)
    evaluation_total_tokens.set(0)
    evaluation_cost.set(0.0)
    evaluation_latency.set(0.0)


def get_evaluation_metrics() -> dict[str, Any]:
    return {
        "prompt_tokens": evaluation_prompt_tokens.get(),
        "completion_tokens": evaluation_completion_tokens.get(),
        "total_tokens": evaluation_total_tokens.get(),
        "cost": evaluation_cost.get(),
        "latency_ms": evaluation_latency.get(),
    }


# Drop unsupported params (e.g. response_format on Anthropic) silently.
# NOTE (verified against installed litellm 1.49.0): `response_format` is NOT in the Anthropic
# provider's supported OpenAI params, so it is dropped. Structured output is therefore enforced
# by the injected schema instructions plus strict local Pydantic validation, not by the provider.
litellm.drop_params = True


def resolve_structured_output_thinking_kwargs(model: str, mode: str | None = None) -> dict[str, Any]:
    """Returns provider kwargs that stop extended/adaptive thinking from consuming the
    completion budget of a structured JSON call.

    Root cause of the PETREVOLT domain truncation (eval 1a8036ae): Claude 5.5-generation models
    run adaptive thinking by default when `thinking` is omitted, and thinking tokens count toward
    `max_tokens`. Every 5-criterion domain batch stopped at exactly the 900-token cap.

    mode:
      - "off" (default): disable thinking where the model allows it.
          * claude-sonnet-5-5 -> {"type": "between_tools"} (Sonnet 5.5 rejects {"type": "disabled"})
          * claude-haiku-5-5  -> {"type": "disabled"} (accepted at effort <= high; default effort is medium)
          * other models      -> no thinking kwarg (provider default)
      - "provider_default": send nothing (previous behavior).

    Extra kwargs are passed through by litellm 1.49 to the Anthropic request body
    (`utils.get_optional_params` forwards non-OpenAI kwargs). Live acceptance is NOT verified
    offline; see docs/REAL_PROVIDER_READINESS.md.
    """
    resolved_mode = (mode or "off").strip().lower()
    if resolved_mode != "off":
        return {}
    normalized = (model or "").lower().replace("anthropic/", "").replace(".", "-")
    if normalized.startswith("claude-sonnet-5-5"):
        return {"thinking": {"type": "between_tools"}}
    if normalized.startswith("claude-haiku-5-5"):
        return {"thinking": {"type": "disabled"}}
    return {}


class LiteLLMGateway:
    """LiteLLM AI gateway targeting Claude and other LLM models with cost guards."""

    provider_name = "litellm"

    def __init__(
        self,
        *,
        model: str = "claude-sonnet-5-5",
        timeout: int = 120,
        max_retries: int = 2,
        api_key: str | None = None,
    ) -> None:
        self._model = model
        self._timeout = timeout
        self._max_retries = max_retries
        self._api_key = api_key
        self._router = ModelRouter()

    def _is_transient_error(self, exc: Exception) -> bool:
        cls_name = type(exc).__name__
        msg = str(exc)

        # Never retry budget exhaustion, authentication or validation errors
        if isinstance(exc, AIBudgetExhaustedError):
            return False
        if "Authentication" in cls_name or "Auth" in cls_name or "InvalidAPIKey" in msg or "API key" in msg.lower():
            return False
        if "ValidationError" in cls_name or "JSONDecodeError" in cls_name:
            return False

        # Retry on HTTP 429, Timeout, and Temporary provider errors
        transient_indicators = [
            "RateLimitError", "Timeout", "APIConnectionError", "ServiceUnavailableError",
            "503", "429", "500", "502", "504", "UNAVAILABLE", "high demand", "temporary"
        ]

        return any(indicator.lower() in cls_name.lower() or indicator.lower() in msg.lower() for indicator in transient_indicators)

    def _handle_and_raise_error(self, exc: Exception) -> None:
        if isinstance(exc, AIBudgetExhaustedError):
            raise exc

        cls_name = type(exc).__name__
        msg = str(exc)

        if "Authentication" in cls_name or "Auth" in cls_name or "InvalidAPIKey" in msg or "API key" in msg.lower():
            raise AIProviderError(f"Authentication failed: Invalid Anthropic API Key. Details: {exc}") from exc

        if "RateLimitError" in cls_name or "429" in msg:
            raise AIProviderError(f"Rate limit exceeded: The Anthropic API returned a 429 rate limit error. Details: {exc}") from exc

        if "InsufficientFunds" in cls_name or "credit" in msg.lower() or "fund" in msg.lower() or "billing" in msg.lower():
            raise AIProviderError(f"Insufficient funds: The Anthropic account has insufficient credits. Details: {exc}") from exc

        raise AIProviderError(f"LiteLLM call failed: {exc}") from exc

    def _make_ontology_compliant(self, val: Any) -> Any:
        if isinstance(val, str):
            forbidden_replacements = {
                r"\bviability rating\b": "viability level",
                r"\bfunding recommendation\b": "funding proposal",
                r"\bincubation verdict\b": "incubation finding",
                r"\bincubation decision\b": "incubation finding",
                r"\bfunding decision\b": "funding finding",
                r"\bdo not incubate\b": "do not support",
                r"\bdo not invest\b": "do not fund",
                r"\bscore\b": "metric",
                r"\bapproval\b": "support",
                r"\brejection\b": "decline",
                r"\brecommendation\b": "suggestion",
                r"\bverdict\b": "finding",
                r"\brating\b": "assessment",
                r"\brank\b": "grade",
                r"\breject\b": "decline",
                r"\bincubate\b": "nurture",
                r"\binvest\b": "support"
            }
            for pattern, replacement in forbidden_replacements.items():
                val = re.sub(pattern, replacement, val, flags=re.IGNORECASE)
            return val
        elif isinstance(val, dict):
            return {k: self._make_ontology_compliant(v) for k, v in val.items()}
        elif isinstance(val, list):
            return [self._make_ontology_compliant(item) for item in val]
        return val

    def complete_json(
        self,
        request: AICompletionRequest,
        response_model: type[T],
    ) -> AICompletionResult[T]:
        started = time.perf_counter()
        settings = get_settings()

        # 1. Resolve Model via Cost-Aware Routing
        model = self._router.resolve_model(request, default_model=self._model) or self._model

        # Fail-closed pricing verification: reject unpriced model before dispatch
        pricing_catalog = get_pricing_catalog(settings.ai_pricing_catalog_version)
        pricing_catalog.get_pricing(model, allow_fallback=False)

        # 2. Inject JSON Schema into System Prompt (compact separators to conserve input tokens).
        # Callers may supply a compact wire-format description (metadata["compact_schema"]) to avoid
        # paying ~870 input tokens per call for the full Pydantic JSON Schema; the response is still
        # validated strictly against `response_model` below.
        compact_schema = (request.metadata or {}).get("compact_schema")
        if isinstance(compact_schema, str) and compact_schema.strip():
            schema_label = "compact JSON format"
            schema_block = f"```json-format\n{compact_schema.strip()}\n```"
        else:
            schema_json = json.dumps(
                response_model.model_json_schema(), separators=(",", ":"), ensure_ascii=False
            )
            schema_label = "JSON Schema"
            schema_block = f"```json-schema\n{schema_json}\n```"
        augmented_system = (
            f"{request.system_prompt}\n\n"
            "OUTPUT FORMAT:\n"
            "You MUST respond with a single valid JSON object that conforms exactly to the "
            f"following {schema_label}. Do not include any explanation, markdown fences, or prose "
            "before or after the JSON object.\n\n"
            f"{schema_block}"
        )

        messages = [
            {"role": "system", "content": augmented_system},
            {"role": "user", "content": request.user_prompt},
        ]

        # 3. Pre-Call Budget Estimation & Reservation
        pricing_catalog = get_pricing_catalog(settings.ai_pricing_catalog_version)
        est_input_tokens = (
            request.estimated_input_tokens
            if request.estimated_input_tokens is not None
            else (len(augmented_system) + len(request.user_prompt)) // 4
        )
        planned_output_tokens = request.max_output_tokens if request.max_output_tokens is not None else 4096

        if (
            not isinstance(est_input_tokens, int)
            or isinstance(est_input_tokens, bool)
            or est_input_tokens < 0
            or not isinstance(planned_output_tokens, int)
            or isinstance(planned_output_tokens, bool)
            or planned_output_tokens <= 0
        ):
            raise AIProviderError(
                f"Invalid token budget parameters: est_input_tokens={est_input_tokens}, max_output_tokens={planned_output_tokens}"
            )

        planned_cost = pricing_catalog.estimate_max_cost(
            model=model,
            estimated_prompt_tokens=est_input_tokens,
            max_completion_tokens=planned_output_tokens,
        )
        if not math.isfinite(planned_cost) or planned_cost < 0.0:
            raise AIProviderError(f"Invalid non-finite planned cost estimate: {planned_cost}")

        ledger: EvaluationCostLedger | None = None
        reservation_id: str | None = None
        if request.evaluation_id:
            ledger = CostLedgerManager.get_instance().get_or_create_ledger(
                evaluation_id=request.evaluation_id,
                startup_id=request.startup_id,
                max_budget_usd=settings.ai_max_evaluation_budget_usd,
                exchange_rate=settings.ai_inr_exchange_rate,
                buffer_multiplier=settings.ai_inr_buffer_multiplier,
            )

            # Reserve budget (raises AIBudgetExhaustedError if limit exceeded)
            reservation_id = ledger.reserve_budget(
                estimated_cost_usd=planned_cost,
                agent_name=request.agent_name,
            )

        # 4. API Key Resolution
        api_key_to_use = self._api_key
        if api_key_to_use:
            api_key_to_use = api_key_to_use.strip()
        else:
            settings_key = settings.anthropic_api_key
            api_key_to_use = settings_key.strip() if settings_key else None

        if not api_key_to_use:
            env_key = os.environ.get("ANTHROPIC_API_KEY")
            api_key_to_use = env_key.strip() if env_key else None

        app_env_norm = (getattr(settings, "app_env", "development") or "development").strip().lower()
        if not api_key_to_use and (settings.ai_provider == "anthropic" or app_env_norm == "production"):
            if ledger and reservation_id:
                ledger.release_reservation(reservation_id)
            raise AIProviderError("ANTHROPIC_API_KEY is missing or empty. Failing closed before remote dispatch.")

        # 5. Execution Loop — THE single retry layer for transport-level failures.
        #
        # Unified retry policy (see docs/ARCHITECTURE.md "Retry policy"):
        #   * litellm internal retries: disabled (num_retries=0).
        #   * This gateway: retries ONLY transient transport errors (429 / 5xx / timeout / connection),
        #     where the provider returned no completion. Max attempts = AI_MAX_RETRIES + 1.
        #   * Every attempt reserves budget BEFORE dispatch, gets a distinct operation ID, and is
        #     written to the cost ledger (failed transport attempts as zero-token TRANSIENT_ERROR rows).
        #   * Truncated / unparseable completions are NEVER retried here (deterministic failures).
        #   * Domain layer: no identical retries; truncation triggers one budget-checked split recovery.
        thinking_kwargs = resolve_structured_output_thinking_kwargs(
            model, getattr(settings, "ai_structured_thinking_mode", "off")
        )
        retry_delays = [2.0, 5.0]
        max_attempts = self._max_retries + 1
        last_exc: Exception | None = None
        response = None
        retry_count = 0
        base_operation_id = (
            str(request.metadata["operation_id"]).strip()
            if request.metadata and request.metadata.get("operation_id")
            else None
        )

        for attempt in range(max_attempts):
            if attempt > 0 and ledger:
                try:
                    reservation_id = ledger.reserve_budget(
                        estimated_cost_usd=planned_cost,
                        agent_name=f"{request.agent_name}_retry_{attempt}",
                    )
                except AIBudgetExhaustedError as budget_err:
                    logger.error(
                        f"Cannot retry operation '{request.agent_name}' (attempt {attempt + 1}): "
                        f"Budget exhausted for retry reservation: {budget_err}"
                    )
                    raise

            try:
                response = litellm.completion(
                    model=model,
                    messages=messages,
                    response_format=response_model,
                    max_tokens=planned_output_tokens,
                    timeout=self._timeout,
                    num_retries=0,  # The gateway is the only retry layer
                    api_key=api_key_to_use,
                    **thinking_kwargs,
                )
                last_exc = None
                retry_count = attempt
                break  # Success
            except Exception as exc:
                last_exc = exc
                retry_count = attempt
                is_transient = self._is_transient_error(exc)
                will_retry = is_transient and attempt < max_attempts - 1

                if ledger and reservation_id:
                    # Account for the failed attempt explicitly (no usage reported -> zero tokens).
                    ledger.reconcile_operation(
                        reservation_id=reservation_id,
                        agent_name=request.agent_name,
                        provider=self.provider_name,
                        model=model,
                        input_tokens=0,
                        output_tokens=0,
                        retry_count=attempt,
                        latency_ms=(time.perf_counter() - started) * 1000,
                        status="TRANSIENT_ERROR" if is_transient else "PROVIDER_ERROR",
                        confidence="NO_USAGE_REPORTED",
                        finish_reason=None,
                        operation_id=(f"{base_operation_id}_a{attempt + 1}" if base_operation_id else None),
                    )
                    reservation_id = None

                if not will_retry:
                    logger.error(f"LiteLLM call failed (attempt {attempt + 1}/{max_attempts}): {type(exc).__name__}")
                    self._handle_and_raise_error(exc)

                delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                logger.warning(
                    f"[RETRY DISPATCH] '{request.agent_name}' transient provider error on attempt "
                    f"{attempt + 1}/{max_attempts} ({type(exc).__name__}). Retrying in {delay}s with a new "
                    f"budget reservation."
                )
                time.sleep(delay)

        if last_exc is not None:
            self._handle_and_raise_error(last_exc)

        # 6. Reconcile Token Usage & Cost (Immediately upon response reception)
        try:
            elapsed_ms = (time.perf_counter() - started) * 1000
            actual_model = getattr(response, "model", model)
            usage = getattr(response, "usage", None)
            choices = getattr(response, "choices", None)
            choice = choices[0] if response and choices else None
            if choice is None:
                raise ValueError("Missing response choices")
            raw_text = getattr(getattr(choice, "message", None), "content", "") or ""
            if not raw_text and choice and hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                raw_text = choice.message.tool_calls[0].function.arguments or ""

            # Extract provider stop/finish reason
            finish_reason = None
            if choice:
                finish_reason = (
                    getattr(choice, "finish_reason", None)
                    if hasattr(choice, "finish_reason")
                    else (choice.get("finish_reason") if isinstance(choice, dict) else None)
                )
                if not finish_reason and hasattr(choice, "message"):
                    msg = choice.message
                    finish_reason = (
                        getattr(msg, "stop_reason", None)
                        or getattr(msg, "finish_reason", None)
                        if hasattr(msg, "stop_reason") or hasattr(msg, "finish_reason")
                        else (msg.get("stop_reason") or msg.get("finish_reason") if isinstance(msg, dict) else None)
                    )

            if usage is not None:
                prompt_tokens = getattr(usage, "prompt_tokens", None)
                completion_tokens = getattr(usage, "completion_tokens", None)
                if (
                    not isinstance(prompt_tokens, int)
                    or isinstance(prompt_tokens, bool)
                    or prompt_tokens < 0
                    or not isinstance(completion_tokens, int)
                    or isinstance(completion_tokens, bool)
                    or completion_tokens < 0
                ):
                    raise ValueError(
                        f"Malformed provider usage metrics: prompt_tokens={prompt_tokens}, completion_tokens={completion_tokens}"
                    )
                raw_total = getattr(usage, "total_tokens", None)
                total_tokens = (
                    raw_total
                    if isinstance(raw_total, int) and not isinstance(raw_total, bool) and raw_total >= 0
                    else (prompt_tokens + completion_tokens)
                )
                call_confidence = None
            else:
                prompt_tokens = est_input_tokens
                completion_tokens = len(raw_text) // 4
                total_tokens = prompt_tokens + completion_tokens
                call_confidence = "UNVERIFIED_ESTIMATE"

            # Cached tokens extraction
            prompt_tokens_details = getattr(usage, "prompt_tokens_details", None)
            cached_tokens = (
                getattr(prompt_tokens_details, "cached_tokens", 0)
                or getattr(usage, "cache_read_input_tokens", 0)
                or 0
            ) if prompt_tokens_details or usage else 0

            # Resolve cache write breakdown and TTL attribution hierarchy
            w_5m, w_1h, w_total, resolved_ttl = resolve_cache_attribution(
                usage=usage,
                request_metadata=request.metadata,
                default_ttl=settings.ai_default_cache_write_ttl,
                pricing_policy=settings.ai_cache_pricing_policy,
            )

            actual_reported_cost: float | None = None
            if w_total == 0 and cached_tokens == 0 and response:
                try:
                    actual_reported_cost = litellm.completion_cost(completion_response=response)
                except Exception:
                    actual_reported_cost = None
        except Exception as resp_exc:
            if ledger and reservation_id:
                ledger.release_reservation(reservation_id)
            raise AIResponseParseError(f"Malformed provider response object: {resp_exc}") from resp_exc

        reconciled_cost_record: CostRecord | None = None
        operation_id = (
            (f"{base_operation_id}_a{retry_count + 1}" if retry_count > 0 else base_operation_id)
            if base_operation_id
            else None
        )

        def _record_cost(op_status: str) -> CostRecord | None:
            nonlocal reconciled_cost_record
            if reconciled_cost_record is not None:
                return reconciled_cost_record
            if ledger and reservation_id:
                already_recorded = bool(operation_id and ledger.has_operation(operation_id))
                rec = ledger.reconcile_operation(
                    reservation_id=reservation_id,
                    agent_name=request.agent_name,
                    provider=self.provider_name,
                    model=actual_model,
                    input_tokens=prompt_tokens,
                    output_tokens=completion_tokens,
                    cached_tokens=cached_tokens,
                    cache_write_tokens=w_total,
                    cache_write_5m_tokens=w_5m,
                    cache_write_1h_tokens=w_1h,
                    cache_write_ttl=resolved_ttl,
                    actual_cost_usd=actual_reported_cost,
                    retry_count=retry_count,
                    latency_ms=elapsed_ms,
                    status=op_status,
                    confidence=call_confidence,
                    finish_reason=finish_reason,
                    operation_id=operation_id,
                )
                if not already_recorded:
                    # Update Evaluation Cumulative Contextvars
                    evaluation_prompt_tokens.set(evaluation_prompt_tokens.get() + prompt_tokens)
                    evaluation_completion_tokens.set(evaluation_completion_tokens.get() + completion_tokens)
                    evaluation_total_tokens.set(evaluation_total_tokens.get() + total_tokens)
                    evaluation_cost.set(ledger.spent_usd)
                    evaluation_latency.set(evaluation_latency.get() + elapsed_ms)
                reconciled_cost_record = rec
                return rec
            return None

        # 7. Parse and Validate Response JSON
        try:
            # Check provider truncation
            is_truncated = str(finish_reason).lower() in ("length", "max_tokens")
            if is_truncated:
                # Never log raw completion text: it can contain applicant PII.
                logger.error(
                    f"LiteLLM output truncated by provider for agent '{request.agent_name}'. "
                    f"finish_reason='{finish_reason}', completion_tokens={completion_tokens}, "
                    f"max_tokens={planned_output_tokens}, raw_chars={len(raw_text)}."
                )
                _record_cost(op_status="PARSE_ERROR")
                raise AIResponseParseError(
                    f"Model output truncated by provider (finish_reason='{finish_reason}', tokens={completion_tokens}). "
                    f"Incomplete JSON cannot be parsed."
                )

            raw_text = raw_text.strip()
            start_brace = raw_text.find("{")
            start_bracket = raw_text.find("[")

            if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
                start_idx = start_brace
                end_idx = raw_text.rfind("}")
            elif start_bracket != -1:
                start_idx = start_bracket
                end_idx = raw_text.rfind("]")
            else:
                start_idx, end_idx = -1, -1

            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                raw_text = raw_text[start_idx : end_idx + 1]

            try:
                json_data = json.loads(raw_text)
                if isinstance(json_data, dict) and response_model.model_fields:
                    first_field = next(iter(response_model.model_fields.keys()))
                    if first_field not in json_data:
                        for k, v in json_data.items():
                            if isinstance(v, dict) and first_field in v:
                                json_data = v
                                break
            except Exception as json_exc:
                logger.error(
                    f"LiteLLM JSON parse error for agent '{request.agent_name}': {type(json_exc).__name__} "
                    f"[raw_chars: {len(raw_text)}]"
                )
                raise AIResponseParseError(f"Failed to parse AI response JSON: {json_exc}") from json_exc

            try:
                # Legacy vocabulary rewriting ("approval"->"support", "score"->"metric", ...) changes
                # the meaning of evidence-based rationales, so it is opt-in per request only.
                if (request.metadata or {}).get("ontology_rewrite"):
                    json_data = self._make_ontology_compliant(json_data)
                data = response_model.model_validate(json_data)
            except ValidationError as val_exc:
                raise AIResponseParseError(f"Response model validation failed: {val_exc}") from val_exc

        except AIResponseParseError:
            _record_cost(op_status="PARSE_ERROR")
            raise
        except Exception as exc:
            _record_cost(op_status="PARSE_ERROR")
            raise AIResponseParseError(f"Failed to parse AI response JSON: {exc}") from exc

        # Success reconciliation
        cost_record = _record_cost(op_status="SUCCESS")
        if cost_record:
            final_cost_usd = cost_record.final_cost_usd
            final_cost_inr = cost_record.cost_inr
            buffered_cost_inr = cost_record.buffered_cost_inr
        else:
            final_cost_usd = pricing_catalog.calculate_cost(
                model=actual_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cached_tokens=cached_tokens,
                cache_write_tokens=w_total,
                cache_write_5m_tokens=w_5m,
                cache_write_1h_tokens=w_1h,
                cache_write_ttl=resolved_ttl,
            )
            final_cost_inr, buffered_cost_inr = pricing_catalog.convert_to_inr(
                cost_usd=final_cost_usd,
                exchange_rate=settings.ai_inr_exchange_rate,
                buffer_multiplier=settings.ai_inr_buffer_multiplier,
            )
            evaluation_prompt_tokens.set(evaluation_prompt_tokens.get() + prompt_tokens)
            evaluation_completion_tokens.set(evaluation_completion_tokens.get() + completion_tokens)
            evaluation_total_tokens.set(evaluation_total_tokens.get() + total_tokens)
            evaluation_cost.set(evaluation_cost.get() + final_cost_usd)
            evaluation_latency.set(evaluation_latency.get() + elapsed_ms)

        # 8. Enforce Budget Safety Ceiling
        budget_limit = ledger.max_budget_usd if ledger else settings.ai_max_evaluation_budget_usd
        new_cost = ledger.spent_usd if ledger else round(evaluation_cost.get(), 6)
        if new_cost > round(budget_limit, 6):
            raise AIBudgetExhaustedError(
                f"Evaluation aborted: Cumulative cost of ${new_cost:.4f} "
                f"exceeds the budget safety limit of ${budget_limit:.4f}."
            )

        metadata = AICompletionMetadata(
            model=actual_model,
            provider=self.provider_name,
            latency_ms=round(elapsed_ms, 3),
            prompt_version=request.prompt_version,
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            cached_tokens=cached_tokens,
            cost_usd=final_cost_usd,
            cost_inr=final_cost_inr,
            buffered_cost_inr=buffered_cost_inr,
            evaluation_id=request.evaluation_id,
            cumulative_cost_usd=new_cost,
            cumulative_cost_inr=round(new_cost * settings.ai_inr_exchange_rate, 4),
            pricing_version=pricing_catalog.version,
        )
        return AICompletionResult(data=data, metadata=metadata, raw_text=raw_text)


# Backwards compatibility and alternative naming alias
LiteLLMAIGateway = LiteLLMGateway

