import json
import time
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ValidationError

from app.services.ai.exceptions import AIResponseParseError
from app.services.ai.schemas import AICompletionMetadata, AICompletionRequest, AICompletionResult


ResponseFactory = Callable[[AICompletionRequest], dict[str, Any] | BaseModel]


class MockAIGateway:
    """Deterministic AI gateway for development and tests."""

    provider_name = "mock"

    def __init__(
        self,
        *,
        model: str = "mock-model",
        response_factory: ResponseFactory | None = None,
        fixed_response: dict[str, Any] | BaseModel | None = None,
        latency_ms: float = 0.0,
    ) -> None:
        self._model = model
        self._response_factory = response_factory
        self._fixed_response = fixed_response
        self._latency_ms = latency_ms

    def complete_json(
        self,
        request: AICompletionRequest,
        response_model: type[BaseModel],
    ) -> AICompletionResult[BaseModel]:
        started = time.perf_counter()
        payload = self._resolve_payload(request)
        raw_text = self._serialize_payload(payload)

        try:
            if isinstance(payload, BaseModel):
                data = response_model.model_validate(payload.model_dump())
            else:
                data = response_model.model_validate(payload)
        except ValidationError as exc:
            raise AIResponseParseError("Mock response does not match the expected schema") from exc

        elapsed_ms = self._latency_ms or ((time.perf_counter() - started) * 1000)
        metadata = AICompletionMetadata(
            model=request.model or self._model,
            provider=self.provider_name,
            latency_ms=round(elapsed_ms, 3),
            prompt_version=request.prompt_version,
        )
        return AICompletionResult(data=data, metadata=metadata, raw_text=raw_text)

    def _resolve_payload(self, request: AICompletionRequest) -> dict[str, Any] | BaseModel:
        if self._response_factory is not None:
            return self._response_factory(request)
        if self._fixed_response is not None:
            return self._fixed_response
        return {}

    @staticmethod
    def _serialize_payload(payload: dict[str, Any] | BaseModel) -> str:
        if isinstance(payload, BaseModel):
            return payload.model_dump_json()
        return json.dumps(payload)
