from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.modules.ai.agents.base_agent import BaseAgent

class EchoAssessmentResponse(BaseModel):
    agent_name: str = Field(..., description="Name of the executing agent")
    status: str = Field(..., description="Success or validation status")
    startup_name: str = Field(..., description="Name of the startup applications")
    evidence_count: int = Field(..., description="Number of evidence pieces passed")
    received_previous_outputs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class EchoAssessmentAgent(BaseAgent):
    def __init__(self, dependencies: Optional[List[str]] = None):
        super().__init__(
            agent_name="EchoAssessmentAgent",
            response_schema=EchoAssessmentResponse,
            dependencies=dependencies or [],
            relevant_fields=["sector", "startup_name"],
            prompt_template_name="echo_agent"
        )
