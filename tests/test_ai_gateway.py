import pytest
from pydantic import BaseModel, Field

from app.core.config import Settings
from app.services.ai import (
    AIDisabledError,
    AIProviderError,
    AIResponseParseError,
    MockAIGateway,
    create_ai_gateway,
)
from app.services.ai.schemas import AICompletionRequest


class SampleAgentOutput(BaseModel):
    executive_summary: str
    strengths: list[str] = Field(default_factory=list)


def test_settings_load_ai_defaults() -> None:
    settings = Settings()
    assert settings.ai_enabled is False
    assert settings.ai_provider == "mock"
    assert settings.litellm_model == "claude-3-5-sonnet-20241022"
    assert settings.ai_request_timeout_seconds == 120
    assert settings.ai_max_retries == 2
    assert settings.anthropic_api_key is None


def _settings(**overrides: object) -> Settings:
    values = {
        "ai_enabled": False,
        "ai_provider": "mock",
        "litellm_model": "claude-3-5-sonnet-20241022",
        "ai_request_timeout_seconds": 120,
        "ai_max_retries": 2,
        "anthropic_api_key": None,
    }
    values.update(overrides)
    return Settings.model_construct(**values)


def test_create_ai_gateway_returns_mock_by_default() -> None:
    gateway = create_ai_gateway(settings=_settings())
    assert isinstance(gateway, MockAIGateway)


def test_create_ai_gateway_force_mock_overrides_provider() -> None:
    gateway = create_ai_gateway(
        settings=_settings(ai_provider="litellm", ai_enabled=True),
        force_mock=True,
    )
    assert isinstance(gateway, MockAIGateway)


def test_create_ai_gateway_raises_when_provider_not_implemented() -> None:
    with pytest.raises(AIProviderError, match="not implemented"):
        create_ai_gateway(settings=_settings(ai_provider="litellm", ai_enabled=True))


def test_create_ai_gateway_raises_when_disabled_non_mock_provider() -> None:
    with pytest.raises(AIDisabledError, match="disabled"):
        create_ai_gateway(settings=_settings(ai_provider="litellm", ai_enabled=False))


def test_mock_gateway_returns_validated_structured_output() -> None:
    gateway = MockAIGateway(
        fixed_response={
            "executive_summary": "Battery analytics for industrial users.",
            "strengths": ["Clear problem", "Defined market"],
        }
    )
    request = AICompletionRequest(
        system_prompt="You are a startup analyst.",
        user_prompt='{"startup_name": "BatteryX"}',
        prompt_version="startup_profile_v1",
    )

    result = gateway.complete_json(request, SampleAgentOutput)

    assert result.data.executive_summary == "Battery analytics for industrial users."
    assert result.data.strengths == ["Clear problem", "Defined market"]
    assert result.metadata.provider == "mock"
    assert result.metadata.prompt_version == "startup_profile_v1"
    assert result.raw_text is not None


def test_mock_gateway_uses_response_factory() -> None:
    def factory(request: AICompletionRequest) -> dict[str, str]:
        return {"executive_summary": f"Generated for: {request.user_prompt}"}

    gateway = MockAIGateway(response_factory=factory)
    request = AICompletionRequest(system_prompt="system", user_prompt="BatteryX")

    result = gateway.complete_json(request, SampleAgentOutput)

    assert result.data.executive_summary == "Generated for: BatteryX"


def test_mock_gateway_raises_on_invalid_response() -> None:
    gateway = MockAIGateway(fixed_response={"executive_summary": 123})
    request = AICompletionRequest(system_prompt="system", user_prompt="BatteryX")

    with pytest.raises(AIResponseParseError, match="does not match"):
        gateway.complete_json(request, SampleAgentOutput)
