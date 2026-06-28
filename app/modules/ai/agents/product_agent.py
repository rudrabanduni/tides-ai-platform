from typing import List, Optional
from app.modules.ai.agents.base_agent import BaseAgent
from app.modules.ai.agents.models import AgentAssessment

class ProductExpert(BaseAgent):
    def __init__(self, dependencies: Optional[List[str]] = None):
        super().__init__(
            agent_name="ProductExpert",
            response_schema=AgentAssessment,
            dependencies=dependencies or ["FounderExpert"],
            relevant_fields=[
                "product_deck", "architecture", "demo", "patents", 
                "technical_claims", "scalability", "product_roadmap", 
                "defensibility", "maturity", "validation"
            ],
            prompt_template_name="product"
        )
