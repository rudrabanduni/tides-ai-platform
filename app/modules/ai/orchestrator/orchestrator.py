import uuid
import logging
import time
import asyncio
from typing import Dict, Any, List, Optional
from app.modules.ai.agents.registry import AgentRegistry
from app.modules.ai.gateway.gateway import AIGateway
from app.modules.ai.prompts.registry import PromptRegistry
from app.modules.ai.orchestrator.state import WorkflowState
from app.modules.ai.orchestrator.scheduler import Scheduler
from app.modules.ai.orchestrator.context import build_context
from app.modules.ai.telemetry.metrics import WorkflowMetrics
from app.modules.ai.telemetry.tracing import WorkflowTracer

logger = logging.getLogger(__name__)

class AIOrchestrator:
    def __init__(
        self,
        agent_registry: Optional[AgentRegistry] = None,
        ai_gateway: Optional[AIGateway] = None,
        prompt_registry: Optional[PromptRegistry] = None
    ):
        self.agent_registry = agent_registry or AgentRegistry()
        if agent_registry is None:
            # Pre-register default core agents
            from app.modules.ai.agents.founder_agent import FounderExpert
            from app.modules.ai.agents.product_agent import ProductExpert
            from app.modules.ai.agents.market_agent import MarketExpert
            self.agent_registry.register(FounderExpert())
            self.agent_registry.register(ProductExpert())
            self.agent_registry.register(MarketExpert())
        self.ai_gateway = ai_gateway or AIGateway()
        self.prompt_registry = prompt_registry or PromptRegistry()

    async def execute_workflow(
        self,
        startup_profile: Dict[str, Any],
        claims: List[Any],
        evidence: List[Any],
        run_id: Optional[str] = None
    ) -> WorkflowState:
        """Orchestrates execution of the entire multi-agent network topologically, supporting parallel execution."""
        run_id = run_id or f"RUN-{str(uuid.uuid4())[:8].upper()}"
        startup_id = str(startup_profile.get("id") or startup_profile.get("startup_id") or "unknown")
        
        # Initialize state, tracer and metrics
        state = WorkflowState(run_id=run_id, startup_id=startup_id)
        tracer = WorkflowTracer(run_id=run_id)
        metrics = WorkflowMetrics()
        
        # Discover registered agents
        agents = self.agent_registry.get_all_agents()
        if not agents:
            logger.warning("No agents registered. Workflow complete.")
            return state
            
        # Group into parallel execution phases
        phases = Scheduler.get_execution_phases(agents)
        
        for phase_idx, phase_agents in enumerate(phases):
            logger.info(f"Executing Phase {phase_idx + 1}/{len(phases)}: {[a.agent_name for a in phase_agents]}")
            
            # Run all agents in the current phase concurrently
            tasks = [
                self._run_single_agent(agent, startup_profile, claims, evidence, state, tracer, metrics)
                for agent in phase_agents
            ]
            await asyncio.gather(*tasks)
            
        state.metadata["metrics"] = metrics.model_dump()
        state.metadata["traces"] = [t.model_dump() for t in tracer.traces]
        return state

    async def _run_single_agent(
        self,
        agent: Any,
        startup_profile: Dict[str, Any],
        claims: List[Any],
        evidence: List[Any],
        state: WorkflowState,
        tracer: WorkflowTracer,
        metrics: WorkflowMetrics
    ):
        """Runs a single agent under error handling, context filtering, and telemetry logging."""
        start_time = time.perf_counter()
        
        # Build context pruned for this agent
        context = build_context(
            startup_profile=startup_profile,
            claims=claims,
            evidence=evidence,
            previous_outputs=state.outputs,
            relevant_fields=agent.relevant_fields
        )
        
        # Record trace start
        trace_entry = tracer.start_agent(
            agent_name=agent.agent_name,
            inputs={
                "relevant_fields": agent.relevant_fields,
                "dependencies": agent.dependencies
            }
        )
        
        try:
            # Execute agent run
            result = await agent.run(context, self.ai_gateway, self.prompt_registry)
            
            # Serialize result output
            serialized_output = result.model_dump()
            state.outputs[agent.agent_name] = serialized_output
            state.completed_agents.append(agent.agent_name)
            
            # Record trace success (mocking provider metrics where appropriate)
            provider = "mock"
            model = "mock-model"
            latency = (time.perf_counter() - start_time) * 1000.0
            
            tracer.end_agent_success(
                entry=trace_entry,
                outputs=serialized_output,
                provider=provider,
                model=model,
                latency=latency
            )
            
            # Accumulate metrics
            metrics.add_call_metrics(
                prompt_t=15,
                completion_t=25,
                latency=latency,
                retries=0,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Agent '{agent.agent_name}' failed to execute: {str(e)}")
            latency = (time.perf_counter() - start_time) * 1000.0
            state.errors[agent.agent_name] = str(e)
            state.failed_agents.append(agent.agent_name)
            
            tracer.end_agent_failure(
                entry=trace_entry,
                error=str(e),
                latency=latency
            )
            
            metrics.add_call_metrics(
                prompt_t=0,
                completion_t=0,
                latency=latency,
                retries=0,
                success=False
            )
