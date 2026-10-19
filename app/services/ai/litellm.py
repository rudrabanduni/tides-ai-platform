import json
import re
import time
import os
import logging
import contextvars
from typing import TypeVar
from pydantic import BaseModel, ValidationError
import litellm

from app.core.config import get_settings
from app.services.ai.exceptions import AIProviderError, AIResponseParseError
from app.services.ai.schemas import AICompletionMetadata, AICompletionRequest, AICompletionResult

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)

# Context variables to track cumulative metrics per evaluation
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

def get_evaluation_metrics() -> dict:
    return {
        "prompt_tokens": evaluation_prompt_tokens.get(),
        "completion_tokens": evaluation_completion_tokens.get(),
        "total_tokens": evaluation_total_tokens.get(),
        "cost": evaluation_cost.get(),
        "latency_ms": evaluation_latency.get()
    }

# Drop unsupported params (e.g. response_format on Anthropic) silently
litellm.drop_params = True


class LiteLLMGateway:
    """LiteLLM AI gateway targeting Claude and other LLM models."""

    provider_name = "litellm"

    def __init__(
        self,
        *,
        model: str = "claude-3-5-sonnet-20241022",
        timeout: int = 120,
        max_retries: int = 2,
        api_key: str | None = None,
    ) -> None:
        self._model = model
        self._timeout = timeout
        self._max_retries = max_retries
        self._api_key = api_key

    def _is_transient_error(self, exc: Exception) -> bool:
        cls_name = type(exc).__name__
        msg = str(exc)
        
        # Never retry authentication or validation errors
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

    def _handle_and_raise_error(self, exc: Exception):
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

        # Inject the JSON schema into the system prompt so providers that do not
        # support response_format (e.g. Anthropic) still produce valid JSON.
        schema_json = json.dumps(
            response_model.model_json_schema(), indent=2, ensure_ascii=False
        )
        augmented_system = (
            f"{request.system_prompt}\n\n"
            "OUTPUT FORMAT:\n"
            "You MUST respond with a single valid JSON object that conforms exactly to the "
            "following JSON Schema. Do not include any explanation, markdown fences, or prose "
            "before or after the JSON object.\n\n"
            f"```json-schema\n{schema_json}\n```"
        )

        messages = [
            {"role": "system", "content": augmented_system},
            {"role": "user", "content": request.user_prompt},
        ]

        model = request.model or self._model

        # Clean/strip API key
        api_key_to_use = self._api_key
        if api_key_to_use:
            api_key_to_use = api_key_to_use.strip()
        else:
            settings_key = get_settings().anthropic_api_key
            api_key_to_use = settings_key.strip() if settings_key else None
            
        if not api_key_to_use:
            env_key = os.environ.get("ANTHROPIC_API_KEY")
            api_key_to_use = env_key.strip() if env_key else None

        # Automatic Retry with custom schedule: Attempt 1 -> 2s delay -> Attempt 2 -> 5s delay -> Attempt 3 -> Fail
        retry_delays = [2.0, 5.0]
        max_attempts = 3
        last_exc: Exception | None = None
        response = None
        
        for attempt in range(max_attempts):
            try:
                response = litellm.completion(
                    model=model,
                    messages=messages,
                    response_format=response_model,
                    timeout=self._timeout,
                    num_retries=0,  # We manage retries manually
                    api_key=api_key_to_use,
                )
                last_exc = None
                break  # success — exit retry loop
            except Exception as exc:
                last_exc = exc
                is_transient = self._is_transient_error(exc)
                
                # If it's a non-transient error or we've exhausted all attempts, raise
                if not is_transient or attempt >= max_attempts - 1:
                    logger.error(f"LiteLLM call failed (attempt {attempt + 1}/{max_attempts}): {exc}")
                    self._handle_and_raise_error(exc)
                
                delay = retry_delays[attempt]
                logger.warning(
                    f"LiteLLM transient error encountered on attempt {attempt + 1}/{max_attempts}: {exc}. "
                    f"Retrying in {delay} seconds..."
                )
                time.sleep(delay)

        if last_exc is not None:
            self._handle_and_raise_error(last_exc)

        # Parse and validate response
        try:
            choice = response.choices[0]
            raw_text = choice.message.content or ""

            # Fallback if raw content is empty but tool_calls exist
            if not raw_text and hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                raw_text = choice.message.tool_calls[0].function.arguments

            # Robust JSON extraction: locate first '{' or '[' and last '}' or ']'
            raw_text = raw_text.strip()
            start_brace = raw_text.find('{')
            start_bracket = raw_text.find('[')
            
            if start_brace != -1 and (start_bracket == -1 or start_brace < start_bracket):
                start_idx = start_brace
                end_idx = raw_text.rfind('}')
            elif start_bracket != -1:
                start_idx = start_bracket
                end_idx = raw_text.rfind(']')
            else:
                start_idx, end_idx = -1, -1
                
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                raw_text = raw_text[start_idx:end_idx + 1]

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
                raise AIResponseParseError(f"Failed to parse AI response JSON: {json_exc}") from json_exc

            try:
                json_data = self._make_ontology_compliant(json_data)
                data = response_model.model_validate(json_data)
            except ValidationError as val_exc:
                raise AIResponseParseError(f"Response model validation failed: {val_exc}") from val_exc

        except AIResponseParseError:
            raise
        except Exception as exc:
            raise AIResponseParseError(f"Failed to parse AI response JSON: {exc}") from exc

        elapsed_ms = (time.perf_counter() - started) * 1000
        
        # Calculate tokens and cost
        actual_model = getattr(response, "model", model)
        usage = getattr(response, "usage", None)
        prompt_tokens = usage.prompt_tokens if usage else 0
        completion_tokens = usage.completion_tokens if usage else 0
        total_tokens = usage.total_tokens if usage else 0
        
        try:
            cost = litellm.completion_cost(completion_response=response) or 0.0
        except Exception:
            # Fallback manual calculation for claude-3-5-sonnet-20241022 or similar
            cost = (prompt_tokens * 3.0 + completion_tokens * 15.0) / 1_000_000.0

        # Log individual request cost observability
        logger.info(
            f"[COST OBSERVABILITY] Model: {actual_model} | "
            f"Input/Prompt Tokens: {prompt_tokens} | Output/Completion Tokens: {completion_tokens} | "
            f"Total Tokens: {total_tokens} | Request Latency: {elapsed_ms:.2f}ms | "
            f"Estimated Cost: ${cost:.6f}"
        )
        print(
            f"[COST OBSERVABILITY] Model: {actual_model} | "
            f"Input/Prompt Tokens: {prompt_tokens} | Output/Completion Tokens: {completion_tokens} | "
            f"Total Tokens: {total_tokens} | Request Latency: {elapsed_ms:.2f}ms | "
            f"Estimated Cost: ${cost:.6f}"
        )

        # Update evaluation cumulative metrics
        new_prompt_tokens = evaluation_prompt_tokens.get() + prompt_tokens
        new_completion_tokens = evaluation_completion_tokens.get() + completion_tokens
        new_total_tokens = evaluation_total_tokens.get() + total_tokens
        new_cost = evaluation_cost.get() + cost
        new_latency = evaluation_latency.get() + elapsed_ms
        
        evaluation_prompt_tokens.set(new_prompt_tokens)
        evaluation_completion_tokens.set(new_completion_tokens)
        evaluation_total_tokens.set(new_total_tokens)
        evaluation_cost.set(new_cost)
        evaluation_latency.set(new_latency)

        # Enforce budget safety threshold
        budget_limit = get_settings().ai_max_evaluation_budget
        if new_cost > budget_limit:
            raise AIProviderError(
                f"Evaluation aborted: Estimated cumulative cost of ${new_cost:.4f} "
                f"exceeds the budget safety limit of ${budget_limit:.4f}."
            )

        metadata = AICompletionMetadata(
            model=model,
            provider=self.provider_name,
            latency_ms=round(elapsed_ms, 3),
            prompt_version=request.prompt_version,
        )
        return AICompletionResult(data=data, metadata=metadata, raw_text=raw_text)
