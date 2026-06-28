from abc import ABC, abstractmethod
from typing import List, Type, Dict, Any, Optional
from pydantic import BaseModel
from app.modules.ai.orchestrator.context import AgentContext
from app.modules.ai.gateway.gateway import AIGateway
from app.modules.ai.gateway.models import AIRequest
from app.modules.ai.prompts.registry import PromptRegistry

class BaseAgent(ABC):
    def __init__(
        self,
        agent_name: str,
        response_schema: Type[BaseModel],
        dependencies: Optional[List[str]] = None,
        relevant_fields: Optional[List[str]] = None,
        prompt_template_name: Optional[str] = None
    ):
        self.agent_name = agent_name
        self.response_schema = response_schema
        self.dependencies = dependencies or []
        self.relevant_fields = relevant_fields or []
        self.prompt_template_name = prompt_template_name or f"{agent_name.lower()}"

    async def run(self, context: AgentContext, gateway: AIGateway, prompt_registry: PromptRegistry) -> BaseModel:
        """Executes agent execution logic: templates prompts, queries gateway, validates structured schema."""
        # Build template parameters from context
        variables = self._build_prompt_variables(context)
        
        # Resolve templates
        system_prompt = ""
        try:
            try:
                system_prompt = prompt_registry.render(f"{self.prompt_template_name}/system", variables)
            except FileNotFoundError:
                system_prompt = prompt_registry.render(f"{self.prompt_template_name}_system", variables)
        except FileNotFoundError:
            # System prompt is optional, fallback to generic
            system_prompt = f"You are the {self.agent_name} agent."
            
        user_prompt = ""
        try:
            user_prompt = prompt_registry.render(f"{self.prompt_template_name}/user", variables)
        except FileNotFoundError:
            user_prompt = prompt_registry.render(f"{self.prompt_template_name}_user", variables)
        
        # Prepare request
        request = AIRequest(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=self.response_schema
        )
        
        # Query Gateway
        response = await gateway.generate(request)
        
        # Validate output schema
        if response.parsed and isinstance(response.parsed, self.response_schema):
            return response.parsed
            
        # Fallback parsing
        validated = self.response_schema.model_validate_json(response.content)
        return validated

    def _build_prompt_variables(self, context: AgentContext) -> Dict[str, Any]:
        """Converts raw context collections to template format variables."""
        return {
            "startup_profile": str(context.startup_profile),
            "claims": str(context.claims),
            "evidence": str(context.evidence),
            "previous_outputs": str(context.previous_outputs),
            # Extract additional custom overrides if needed
            **context.metadata
        }
