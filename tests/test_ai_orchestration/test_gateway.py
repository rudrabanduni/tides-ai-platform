import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from app.modules.ai.gateway.models import AIRequest, AIResponse, TokenUsage
from app.modules.ai.gateway.provider import MockProvider, BaseProvider
from app.modules.ai.gateway.gateway import AIGateway
from app.modules.ai.config import get_ai_settings
from pydantic import BaseModel

class DummyResponseSchema(BaseModel):
    name: str
    value: float

@pytest.mark.anyio
async def test_mock_provider_generation():
    provider = MockProvider()
    request = AIRequest(user_prompt="Hello", response_schema=DummyResponseSchema)
    
    response = await provider.generate(request)
    assert response.provider == "mock"
    assert response.parsed is not None
    assert isinstance(response.parsed, DummyResponseSchema)
    assert response.parsed.name == "Mock name"
    assert response.parsed.value == 0.95
    assert response.token_usage.total_tokens == 25
    assert response.latency_ms >= 0.0

@pytest.mark.anyio
async def test_gateway_failover_routing():
    gateway = AIGateway()
    
    # We will simulate a failure in the primary provider "openai"
    # and verify that it falls back to the configured fallback "mock".
    settings = get_ai_settings()
    settings.ai_default_provider = "openai"
    settings.ai_fallback_provider = "mock"
    
    # Mock the OpenAI provider to raise an exception
    failing_provider = AsyncMock()
    failing_provider.generate.side_effect = ValueError("OpenAI connection failed")
    gateway.providers["openai"] = failing_provider
    
    request = AIRequest(user_prompt="Hello Failover", response_schema=DummyResponseSchema)
    response = await gateway.generate(request)
    
    assert failing_provider.generate.called
    assert response.provider == "mock"
    assert isinstance(response.parsed, DummyResponseSchema)

@pytest.mark.anyio
async def test_gateway_retry_and_timeout():
    gateway = AIGateway()
    settings = get_ai_settings()
    settings.ai_default_provider = "openai"
    settings.ai_fallback_provider = "mock"
    settings.ai_max_retries = 2
    settings.ai_request_timeout_seconds = 1
    
    # Mock OpenAI provider to fail twice then succeed
    openai_provider = AsyncMock()
    call_count = 0
    
    async def mock_generate(request):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise ConnectionError("Temporary failure")
        return AIResponse(
            content='{"name": "Succeed", "value": 1.23}',
            parsed=DummyResponseSchema(name="Succeed", value=1.23),
            provider="openai",
            model="gpt-4o"
        )
        
    openai_provider.generate.side_effect = mock_generate
    gateway.providers["openai"] = openai_provider
    
    request = AIRequest(user_prompt="Retry Test", response_schema=DummyResponseSchema)
    response = await gateway.generate(request)
    
    assert call_count == 3
    assert response.provider == "openai"
    assert response.parsed.name == "Succeed"

@pytest.mark.anyio
async def test_gateway_timeout_expiration():
    gateway = AIGateway()
    settings = get_ai_settings()
    settings.ai_default_provider = "openai"
    settings.ai_fallback_provider = "mock" # Don't fallback, just test that timeout triggers
    settings.ai_max_retries = 0
    settings.ai_request_timeout_seconds = 0.05
    
    # Mock OpenAI provider to sleep longer than timeout
    slow_provider = AsyncMock()
    async def slow_generate(request):
        await asyncio.sleep(0.2)
        return AIResponse(content="slow", provider="openai", model="slow")
        
    slow_provider.generate.side_effect = slow_generate
    gateway.providers["openai"] = slow_provider
    
    # If primary fails with timeout, it might try fallback. Let's make fallback raise exception as well to check timeout propagation
    mock_provider = AsyncMock()
    mock_provider.generate.side_effect = ValueError("Timeout mock")
    gateway.providers["mock"] = mock_provider
    
    request = AIRequest(user_prompt="Slow prompt", timeout_seconds=0.05)
    with pytest.raises(RuntimeError) as excinfo:
        await gateway.generate(request)
    assert "Timeout mock" in str(excinfo.value) or "All attempted providers failed" in str(excinfo.value)
