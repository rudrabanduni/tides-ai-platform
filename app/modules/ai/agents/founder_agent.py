from typing import List, Optional
from app.modules.ai.agents.base_agent import BaseAgent
from app.modules.ai.agents.models import AgentAssessment

class FounderExpert(BaseAgent):
    def __init__(self, dependencies: Optional[List[str]] = None):
        super().__init__(
            agent_name="FounderExpert",
            response_schema=AgentAssessment,
            dependencies=dependencies or [],
            relevant_fields=[
                "founders", "team", "experience", "resumes", 
                "founder_claims", "education", "domain_expertise", 
                "role_completeness", "commitment"
            ],
            prompt_template_name="founder"
        )
