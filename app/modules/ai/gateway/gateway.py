import logging
from typing import Dict
from app.modules.ai.config import get_ai_settings
from app.modules.ai.gateway.models import AIRequest, AIResponse
from app.modules.ai.gateway.provider import (
    BaseProvider, OpenAIProvider, AnthropicProvider, GeminiProvider,
    LocalOpenAIProvider, OllamaProvider, LMStudioProvider, MockProvider
)
from app.modules.ai.execution.retry_policy import execute_with_retry
from app.modules.ai.execution.timeout import execute_with_timeout

logger = logging.getLogger(__name__)

class AIGateway:
    def __init__(self):
        self.providers: Dict[str, BaseProvider] = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "gemini": GeminiProvider(),
            "local": LocalOpenAIProvider(),
            "ollama": OllamaProvider(),
            "lmstudio": LMStudioProvider(),
            "mock": MockProvider()
        }

    async def generate(self, request: AIRequest) -> AIResponse:
        settings = get_ai_settings()
        
        # Determine provider sequence
        primary_name = request.provider_override or settings.ai_default_provider
        fallback_name = settings.ai_fallback_provider
        
        # Assemble providers to try
        providers_to_try = [primary_name]
        if fallback_name and fallback_name != primary_name:
            providers_to_try.append(fallback_name)
            
        last_error = None
        for provider_name in providers_to_try:
            provider = self.providers.get(provider_name.lower())
            if not provider:
                logger.error(f"Provider '{provider_name}' is not registered.")
                continue
                
            # Build execution parameters
            max_retries = request.max_retries if request.max_retries is not None else settings.ai_max_retries
            timeout = request.timeout_seconds if request.timeout_seconds is not None else settings.ai_request_timeout_seconds
            
            async def run_call():
                return await provider.generate(request)
                
            try:
                # Wrap with retry and timeout policies
                # Run with timeout first, then retry inside:
                async def run_with_timeout_check():
                    return await execute_with_timeout(run_call(), timeout_seconds=float(timeout))
                    
                response = await execute_with_retry(
                    run_with_timeout_check, 
                    max_retries=max_retries,
                    exceptions_to_retry=(Exception,)
                )
                return response
            except Exception as e:
                logger.warning(f"Provider '{provider_name}' failed during generation: {str(e)}")
                last_error = e
                
        # If all failed
        raise RuntimeError(f"All attempted providers failed. Last error: {str(last_error)}")
