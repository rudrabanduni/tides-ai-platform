from typing import Protocol, runtime_checkable

from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.services.ai.exceptions import AIDisabledError, AIProviderError
from app.services.ai.mock import MockAIGateway
from app.services.ai.litellm import LiteLLMGateway
from app.services.ai.schemas import AICompletionRequest, AICompletionResult


@runtime_checkable
class AIGateway(Protocol):
    """Provider-agnostic interface for structured AI completions."""

    def complete_json(
        self,
        request: AICompletionRequest,
        response_model: type[BaseModel],
    ) -> AICompletionResult[BaseModel]:
        ...


def create_ai_gateway(*, settings: Settings | None = None, force_mock: bool = False) -> AIGateway:
    resolved_settings = settings or get_settings()

    if force_mock or resolved_settings.ai_provider == "mock":
        return MockAIGateway(model=resolved_settings.litellm_model)

    if not resolved_settings.ai_enabled:
        raise AIDisabledError("AI features are disabled")

    if resolved_settings.ai_provider == "litellm":
        return LiteLLMGateway(
            model=resolved_settings.litellm_model,
            timeout=resolved_settings.ai_request_timeout_seconds,
            max_retries=resolved_settings.ai_max_retries,
        )

    raise AIProviderError(f"AI provider '{resolved_settings.ai_provider}' is not implemented")

