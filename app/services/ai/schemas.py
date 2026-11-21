from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)


class AICompletionRequest(BaseModel):
    system_prompt: str
    user_prompt: str
    model: str | None = None
    prompt_version: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Cost observability & budget tracking fields
    evaluation_id: str | None = None
    startup_id: str | None = None
    agent_name: str = "unknown"
    operation_type: str = "general"  # "extraction", "reasoning", "review", "tool"
    max_output_tokens: int | None = None
    estimated_input_tokens: int | None = None


class AICompletionMetadata(BaseModel):
    model: str
    provider: str
    latency_ms: float
    prompt_version: str | None = None

    # Cost observability & token telemetry fields
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    cache_write_tokens: int = 0
    cost_usd: float = 0.0
    cost_inr: float = 0.0
    buffered_cost_inr: float = 0.0
    evaluation_id: str | None = None
    cumulative_cost_usd: float | None = None
    cumulative_cost_inr: float | None = None
    pricing_version: str | None = None


class AICompletionResult(BaseModel, Generic[T]):
    data: T
    metadata: AICompletionMetadata
    raw_text: str | None = None
