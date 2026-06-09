from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class AICompletionRequest(BaseModel):
    system_prompt: str
    user_prompt: str
    model: str | None = None
    prompt_version: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AICompletionMetadata(BaseModel):
    model: str
    provider: str
    latency_ms: float
    prompt_version: str | None = None


class AICompletionResult(BaseModel, Generic[T]):
    data: T
    metadata: AICompletionMetadata
    raw_text: str | None = None
