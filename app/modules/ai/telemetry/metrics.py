from typing import Dict, Any
from pydantic import BaseModel, Field

class WorkflowMetrics(BaseModel):
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_latency_ms: float = 0.0
    retry_count: int = 0
    success_count: int = 0
    failure_count: int = 0

    def add_call_metrics(self, prompt_t: int, completion_t: int, latency: float, retries: int, success: bool):
        self.prompt_tokens += prompt_t
        self.completion_tokens += completion_t
        self.total_tokens += (prompt_t + completion_t)
        self.total_latency_ms += latency
        self.retry_count += retries
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
