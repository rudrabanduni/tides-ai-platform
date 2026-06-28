import pytest
from app.modules.ai.agents.registry import AgentRegistry
from app.modules.ai.agents.base_agent import BaseAgent
from pydantic import BaseModel

class DummyAgentResponse(BaseModel):
    ok: bool

class DummyAgent(BaseAgent):
    def __init__(self, name: str, dependencies=None):
        super().__init__(
            agent_name=name,
            response_schema=DummyAgentResponse,
            dependencies=dependencies or []
        )

def test_agent_registration():
    registry = AgentRegistry()
    agent_a = DummyAgent("AgentA")
    agent_b = DummyAgent("AgentB", dependencies=["AgentA"])
    
    registry.register(agent_a)
    registry.register(agent_b)
    
    assert registry.get_agent("AgentA") == agent_a
    assert registry.get_agent("AgentB") == agent_b
    assert len(registry.get_all_agents()) == 2
    
    registry.unregister("AgentA")
    with pytest.raises(KeyError):
        registry.get_agent("AgentA")

def test_topological_sort_and_execution_order():
    registry = AgentRegistry()
    agent_a = DummyAgent("AgentA")
    agent_b = DummyAgent("AgentB", dependencies=["AgentA"])
    agent_c = DummyAgent("AgentC", dependencies=["AgentB", "AgentA"])
    
    registry.register(agent_c)
    registry.register(agent_a)
    registry.register(agent_b)
    
    order = registry.get_execution_order()
    assert order == ["AgentA", "AgentB", "AgentC"]

def test_cyclic_dependency_detection():
    registry = AgentRegistry()
    agent_a = DummyAgent("AgentA", dependencies=["AgentB"])
    agent_b = DummyAgent("AgentB", dependencies=["AgentA"])
    
    registry.register(agent_a)
    registry.register(agent_b)
    
    with pytest.raises(ValueError) as excinfo:
        registry.get_execution_order()
    assert "Cyclic dependency detected" in str(excinfo.value)
