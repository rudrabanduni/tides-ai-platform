from typing import List, Optional
from app.modules.ai.agents.base_agent import BaseAgent
from app.modules.ai.agents.models import AgentAssessment

class MarketExpert(BaseAgent):
    def __init__(self, dependencies: Optional[List[str]] = None):
        super().__init__(
            agent_name="MarketExpert",
            response_schema=AgentAssessment,
            dependencies=dependencies or ["ProductExpert"],
            relevant_fields=[
                "market_slides", "customer_interviews", "competition", 
                "gtm", "tam", "sam", "som", "pricing", "distribution", 
                "demand_validation", "timing", "segments"
            ],
            prompt_template_name="market"
        )
