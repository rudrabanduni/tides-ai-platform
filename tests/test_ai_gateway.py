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
    """Validate field-level defaults in isolation from any .env file.

    We use model_construct (no env loading) to assert what the *schema* defaults
    are, regardless of whatever is in the developer's local .env.
    """
    settings = Settings.model_construct(
        ai_enabled=False,
        ai_provider="mock",
        litellm_model="claude-3-5-sonnet-20241022",
        ai_request_timeout_seconds=120,
        ai_max_retries=2,
        anthropic_api_key=None,
    )
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
        create_ai_gateway(settings=_settings(ai_provider="unsupported", ai_enabled=True))



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


# ---------------------------------------------------------------------------
# LiteLLMGateway Tests
# ---------------------------------------------------------------------------

from unittest.mock import patch
from app.services.ai import LiteLLMGateway


def test_create_ai_gateway_returns_litellm_when_enabled() -> None:
    gateway = create_ai_gateway(settings=_settings(ai_provider="litellm", ai_enabled=True))
    assert isinstance(gateway, LiteLLMGateway)
    assert gateway._model == "claude-3-5-sonnet-20241022"
    assert gateway._timeout == 120
    assert gateway._max_retries == 2


class MockMessage:
    def __init__(self, content):
        self.content = content


class MockChoice:
    def __init__(self, content):
        self.message = MockMessage(content)


class MockCompletionResponse:
    def __init__(self, content):
        self.choices = [MockChoice(content)]


@patch("litellm.completion")
def test_litellm_gateway_success(mock_completion) -> None:
    # Setup mock response
    mock_completion.return_value = MockCompletionResponse(
        content='{"executive_summary": "Grid analytics.", "strengths": ["Strong team"]}'
    )

    gateway = LiteLLMGateway(model="claude-3-5-sonnet-20241022", timeout=60, max_retries=1)
    request = AICompletionRequest(
        system_prompt="System instructions",
        user_prompt="User input",
        prompt_version="v1",
    )

    result = gateway.complete_json(request, SampleAgentOutput)

    assert result.data.executive_summary == "Grid analytics."
    assert result.data.strengths == ["Strong team"]
    assert result.metadata.provider == "litellm"
    assert result.metadata.model == "claude-3-5-sonnet-20241022"
    assert result.metadata.prompt_version == "v1"

    # Verify litellm.completion call parameters
    import json
    schema_json = json.dumps(SampleAgentOutput.model_json_schema(), indent=2, ensure_ascii=False)
    expected_system = (
        "System instructions\n\n"
        "OUTPUT FORMAT:\n"
        "You MUST respond with a single valid JSON object that conforms exactly to the "
        "following JSON Schema. Do not include any explanation, markdown fences, or prose "
        "before or after the JSON object.\n\n"
        f"```json-schema\n{schema_json}\n```"
    )
    mock_completion.assert_called_once_with(
        model="claude-3-5-sonnet-20241022",
        messages=[
            {"role": "system", "content": expected_system},
            {"role": "user", "content": "User input"},
        ],
        response_format=SampleAgentOutput,
        timeout=60,
        num_retries=0,
    )



@patch("litellm.completion")
def test_litellm_gateway_raises_aiprovidererror_on_litellm_error(mock_completion) -> None:
    from litellm.exceptions import BadRequestError
    # Mock LiteLLM exception
    mock_completion.side_effect = BadRequestError(message="Invalid API Key", model="claude-3-5-sonnet-20241022", llm_provider="anthropic")

    gateway = LiteLLMGateway()
    request = AICompletionRequest(system_prompt="sys", user_prompt="user")

    with pytest.raises(AIProviderError, match="LiteLLM call failed"):
        gateway.complete_json(request, SampleAgentOutput)


@patch("litellm.completion")
def test_litellm_gateway_raises_airesponseparseerror_on_invalid_json(mock_completion) -> None:
    # Non-JSON response
    mock_completion.return_value = MockCompletionResponse(content="plain text response")

    gateway = LiteLLMGateway()
    request = AICompletionRequest(system_prompt="sys", user_prompt="user")

    with pytest.raises(AIResponseParseError, match="Failed to parse"):
        gateway.complete_json(request, SampleAgentOutput)


@patch("litellm.completion")
def test_litellm_gateway_raises_airesponseparseerror_on_schema_mismatch(mock_completion) -> None:
    # JSON but incorrect schema
    mock_completion.return_value = MockCompletionResponse(content='{"strengths": []}')

    gateway = LiteLLMGateway()
    request = AICompletionRequest(system_prompt="sys", user_prompt="user")

    with pytest.raises(AIResponseParseError, match="validation failed"):
        gateway.complete_json(request, SampleAgentOutput)

