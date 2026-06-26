import json
import time
from typing import TypeVar
from pydantic import BaseModel, ValidationError
import litellm

from app.services.ai.exceptions import AIProviderError, AIResponseParseError
from app.services.ai.schemas import AICompletionMetadata, AICompletionRequest, AICompletionResult

T = TypeVar("T", bound=BaseModel)

# Error class names from LiteLLM that indicate transient server issues worth retrying
_RETRYABLE_ERROR_NAMES = (
    "ServiceUnavailableError",
    "RateLimitError",
    "Timeout",
    "APIConnectionError",
)


def _is_retryable(exc: Exception) -> bool:
    cls_name = type(exc).__name__
    msg = str(exc)
    return (
        any(name in cls_name for name in _RETRYABLE_ERROR_NAMES)
        or "503" in msg
        or "429" in msg
        or "UNAVAILABLE" in msg
        or "high demand" in msg.lower()
    )


class LiteLLMGateway:
    """LiteLLM AI gateway targeting Claude and other LLM models."""

    provider_name = "litellm"

    def __init__(
        self,
        *,
        model: str = "claude-3-5-sonnet-20241022",
        timeout: int = 120,
        max_retries: int = 3,
    ) -> None:
        self._model = model
        self._timeout = timeout
        self._max_retries = max_retries

    def complete_json(
        self,
        request: AICompletionRequest,
        response_model: type[T],
    ) -> AICompletionResult[T]:
        started = time.perf_counter()

        messages = [
            {"role": "system", "content": request.system_prompt},
            {"role": "user", "content": request.user_prompt},
        ]

        model = request.model or self._model

        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = litellm.completion(
                    model=model,
                    messages=messages,
                    response_format=response_model,
                    timeout=self._timeout,
                    num_retries=0,  # We manage retries here with exponential backoff
                )
                last_exc = None
                break  # success — exit retry loop
            except Exception as exc:
                last_exc = exc
                if _is_retryable(exc) and attempt < self._max_retries:
                    backoff_seconds = 2 ** attempt  # 1s, 2s, 4s ...
                    time.sleep(backoff_seconds)
                    continue
                raise AIProviderError(f"LiteLLM call failed: {exc}") from exc

        if last_exc is not None:
            raise AIProviderError(
                f"LiteLLM call failed after {self._max_retries + 1} attempts: {last_exc}"
            ) from last_exc

        try:
            choice = response.choices[0]
            raw_text = choice.message.content or ""

            # Fallback if raw content is empty but tool_calls exist (used by some LiteLLM routers for json schema)
            if not raw_text and hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                raw_text = choice.message.tool_calls[0].function.arguments

            # Parse raw text as JSON first to catch JSONDecodeErrors separately
            try:
                json_data = json.loads(raw_text)
            except Exception as json_exc:
                raise AIResponseParseError(f"Failed to parse AI response JSON: {json_exc}") from json_exc

            # Validate structural integrity against the Pydantic model
            try:
                data = response_model.model_validate(json_data)
            except ValidationError as val_exc:
                raise AIResponseParseError(f"Response model validation failed: {val_exc}") from val_exc

        except AIResponseParseError:
            raise
        except Exception as exc:
            raise AIResponseParseError(f"Failed to parse AI response JSON: {exc}") from exc

        elapsed_ms = (time.perf_counter() - started) * 1000
        metadata = AICompletionMetadata(
            model=model,
            provider=self.provider_name,
            latency_ms=round(elapsed_ms, 3),
            prompt_version=request.prompt_version,
        )
        return AICompletionResult(data=data, metadata=metadata, raw_text=raw_text)
