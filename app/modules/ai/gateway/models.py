from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field

class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class AIRequest(BaseModel):
    system_prompt: Optional[str] = None
    user_prompt: str
    temperature: float = 0.0
    max_tokens: int = 4096
    response_schema: Optional[Type[BaseModel]] = None  # Expected Pydantic output model
    timeout_seconds: Optional[float] = None
    max_retries: Optional[int] = None
    provider_override: Optional[str] = None
    model_override: Optional[str] = None

class AIResponse(BaseModel):
    content: str
    parsed: Optional[BaseModel] = None  # Structured output instance if schema was provided
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    provider: str
    model: str
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
