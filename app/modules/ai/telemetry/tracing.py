import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AgentTraceEntry(BaseModel):
    agent_name: str
    run_id: str
    timestamp: float
    status: str  # "success", "failed", "running"
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    latency_ms: float = 0.0

class WorkflowTracer:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.traces: List[AgentTraceEntry] = []

    def start_agent(self, agent_name: str, inputs: Dict[str, Any]) -> AgentTraceEntry:
        entry = AgentTraceEntry(
            agent_name=agent_name,
            run_id=self.run_id,
            timestamp=time.time(),
            status="running",
            inputs=inputs
        )
        self.traces.append(entry)
        return entry

    def end_agent_success(self, entry: AgentTraceEntry, outputs: Dict[str, Any], provider: str, model: str, latency: float):
        entry.status = "success"
        entry.outputs = outputs
        entry.provider = provider
        entry.model = model
        entry.latency_ms = latency

    def end_agent_failure(self, entry: AgentTraceEntry, error: str, latency: float):
        entry.status = "failed"
        entry.error = error
        entry.latency_ms = latency
