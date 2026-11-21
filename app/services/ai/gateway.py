import os
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
    app_env_norm = (getattr(resolved_settings, "app_env", "development") or "development").strip().lower()

    if force_mock:
        return MockAIGateway(model=resolved_settings.litellm_model)

    if resolved_settings.ai_provider == "mock":
        if app_env_norm == "production":
            raise AIProviderError("Mock AI provider is disabled in production mode (APP_ENV=production).")
        return MockAIGateway(model=resolved_settings.litellm_model)

    if not resolved_settings.ai_enabled:
        raise AIDisabledError("AI features are disabled")

    if resolved_settings.ai_provider in ("litellm", "anthropic"):
        api_key = resolved_settings.anthropic_api_key
        if not api_key or not api_key.strip():
            env_key = os.environ.get("ANTHROPIC_API_KEY")
            api_key = env_key.strip() if env_key else None
        else:
            api_key = api_key.strip()

        if (resolved_settings.ai_provider == "anthropic" or app_env_norm == "production") and not api_key:
            raise AIProviderError(
                "Missing ANTHROPIC_API_KEY for live AI provider. Refusing to initialize gateway without credentials."
            )

        return LiteLLMGateway(
            model=resolved_settings.litellm_model,
            timeout=resolved_settings.ai_request_timeout_seconds,
            max_retries=resolved_settings.ai_max_retries,
            api_key=api_key,
        )

    raise AIProviderError(f"AI provider '{resolved_settings.ai_provider}' is not implemented")
