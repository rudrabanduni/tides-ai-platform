import pytest
from app.modules.ai.orchestrator.orchestrator import AIOrchestrator
from app.modules.ai.orchestrator.context import build_context
from app.modules.ai.orchestrator.scheduler import Scheduler
from app.modules.ai.agents.registry import AgentRegistry
from app.modules.ai.agents.echo_agent import EchoAssessmentAgent, EchoAssessmentResponse
from app.modules.ai.gateway.gateway import AIGateway
from app.modules.ai.prompts.registry import PromptRegistry
from pydantic import BaseModel

class DummyClaim:
    def __init__(self, id, field_key, value):
        self.id = id
        self.field_key = field_key
        self.value = value

class DummyEvidence:
    def __init__(self, id, claim_id, snippet):
        self.id = id
        self.claim_id = claim_id
        self.snippet = snippet

@pytest.mark.anyio
async def test_scheduler_grouping():
    agent_a = EchoAssessmentAgent(dependencies=[])
    agent_b = EchoAssessmentAgent(dependencies=["AgentX"])  # Not registered
    agent_c = EchoAssessmentAgent(dependencies=[])
    
    # Assign custom names to test grouping
    agent_a.agent_name = "AgentA"
    agent_b.agent_name = "AgentB"
    agent_c.agent_name = "AgentC"
    
    # Register them
    registry = AgentRegistry()
    registry.register(agent_a)
    registry.register(agent_b)
    registry.register(agent_c)
    
    phases = Scheduler.get_execution_phases(registry.get_all_agents())
    # Since AgentB has no valid dependencies registered, it has 0 dependencies
    # All three agents should be scheduled in the same parallel phase
    assert len(phases) == 1
    assert len(phases[0]) == 3

@pytest.mark.anyio
async def test_scheduler_sequential_phases():
    agent_a = EchoAssessmentAgent()
    agent_a.agent_name = "AgentA"
    agent_b = EchoAssessmentAgent(dependencies=["AgentA"])
    agent_b.agent_name = "AgentB"
    
    registry = AgentRegistry()
    registry.register(agent_a)
    registry.register(agent_b)
    
    phases = Scheduler.get_execution_phases(registry.get_all_agents())
    assert len(phases) == 2
    assert phases[0][0].agent_name == "AgentA"
    assert phases[1][0].agent_name == "AgentB"

def test_context_pruning():
    startup_profile = {"id": "startup-1", "name": "Test Startup"}
    claims = [
        DummyClaim("claim-1", "sector", "SaaS"),
        DummyClaim("claim-2", "revenue", 50000)
    ]
    evidence = [
        DummyEvidence("ev-1", "claim-1", "The company operates in SaaS."),
        DummyEvidence("ev-2", "claim-2", "MRR is $4k.")
    ]
    
    # Prune context for EchoAssessmentAgent which specifies relevant_fields = ["sector", "startup_name"]
    context = build_context(
        startup_profile=startup_profile,
        claims=claims,
        evidence=evidence,
        previous_outputs={},
        relevant_fields=["sector", "startup_name"]
    )
    
    assert len(context.claims) == 1
    assert context.claims[0]["field_key"] == "sector"
    assert len(context.evidence) == 1
    assert context.evidence[0]["snippet"] == "The company operates in SaaS."

@pytest.mark.anyio
async def test_orchestrator_mock_agent_end_to_end():
    # Setup orchestrator with custom temporary template directories if needed
    # But since we populated the actual template directory under prompts/templates/,
    # the prompts should render successfully
    registry = AgentRegistry()
    agent = EchoAssessmentAgent()
    registry.register(agent)
    
    orchestrator = AIOrchestrator(agent_registry=registry)
    
    startup_profile = {"id": "startup-123", "name": "EchoCorp"}
    claims = [{"id": "c1", "field_key": "sector", "value_string": "DefenseTech"}]
    evidence = [{"id": "e1", "claim_id": "c1", "evidence_snippet": "Defense operations."}]
    
    state = await orchestrator.execute_workflow(
        startup_profile=startup_profile,
        claims=claims,
        evidence=evidence
    )
    
    # Verify execution state
    assert "EchoAssessmentAgent" in state.completed_agents
    assert len(state.failed_agents) == 0
    assert "EchoAssessmentAgent" in state.outputs
    
    output = state.outputs["EchoAssessmentAgent"]
    # Check that output conforms to EchoAssessmentResponse fields
    assert "status" in output
    assert "startup_name" in output
    
    # Check telemetry traces
    assert "traces" in state.metadata
    assert len(state.metadata["traces"]) == 1
    trace = state.metadata["traces"][0]
    assert trace["agent_name"] == "EchoAssessmentAgent"
    assert trace["status"] == "success"
    
    # Check metrics
    assert "metrics" in state.metadata
    metrics = state.metadata["metrics"]
    assert metrics["success_count"] == 1
    assert metrics["total_tokens"] > 0
