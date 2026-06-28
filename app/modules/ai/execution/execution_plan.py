from typing import List, Dict, Set
from pydantic import BaseModel, Field

class ExecutionStep(BaseModel):
    agent_name: str
    dependencies: List[str] = Field(default_factory=list)

class ExecutionPlan(BaseModel):
    workflow_id: str
    steps: List[ExecutionStep] = Field(default_factory=list)
