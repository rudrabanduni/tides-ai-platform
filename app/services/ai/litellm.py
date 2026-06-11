import json
import time
from typing import TypeVar
from pydantic import BaseModel, ValidationError
import litellm

from app.services.ai.exceptions import AIProviderError, AIResponseParseError
from app.services.ai.schemas import AICompletionMetadata, AICompletionRequest, AICompletionResult

T = TypeVar("T", bound=BaseModel)


class LiteLLMGateway:
    """LiteLLM AI gateway targeting Claude and other LLM models."""

    provider_name = "litellm"

    def __init__(
        self,
        *,
        model: str = "claude-3-5-sonnet-20241022",
        timeout: int = 120,
        max_retries: int = 2,
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

        try:
            response = litellm.completion(
                model=model,
                messages=messages,
                response_format=response_model,
                timeout=self._timeout,
                num_retries=self._max_retries,
            )
        except Exception as exc:
            raise AIProviderError(f"LiteLLM call failed: {exc}") from exc

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
