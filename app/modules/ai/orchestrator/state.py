from typing import Dict, Any, List
from pydantic import BaseModel, Field

class WorkflowState(BaseModel):
    run_id: str
    startup_id: str
    completed_agents: List[str] = Field(default_factory=list)
    failed_agents: List[str] = Field(default_factory=list)
    outputs: Dict[str, Any] = Field(default_factory=dict)  # Maps agent name -> serialized output dict
    errors: Dict[str, str] = Field(default_factory=dict)     # Maps agent name -> error message
    metadata: Dict[str, Any] = Field(default_factory=dict)
