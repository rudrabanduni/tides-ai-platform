from typing import Dict, List
from app.modules.ai.agents.base_agent import BaseAgent

class AgentRegistry:
    def __init__(self):
        self._registry: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent):
        """Registers a BaseAgent instance."""
        self._registry[agent.agent_name] = agent

    def unregister(self, name: str):
        """Unregisters an agent."""
        if name in self._registry:
            del self._registry[name]

    def get_agent(self, name: str) -> BaseAgent:
        """Retrieves a registered agent instance."""
        if name not in self._registry:
            raise KeyError(f"Agent '{name}' is not registered.")
        return self._registry[name]

    def get_all_agents(self) -> List[BaseAgent]:
        return list(self._registry.values())

    def get_execution_order(self) -> List[str]:
        """Resolves execution order using topological sorting with cycle detection."""
        # Build dependency graph representation
        graph: Dict[str, List[str]] = {}
        for name, agent in self._registry.items():
            graph[name] = [dep for dep in agent.dependencies if dep in self._registry]

        visited = {}  # False = visiting, True = visited
        order = []

        def dfs(node: str):
            if node in visited:
                if not visited[node]:
                    raise ValueError(f"Cyclic dependency detected involving agent '{node}'.")
                return
            visited[node] = False
            for dep in graph.get(node, []):
                dfs(dep)
            visited[node] = True
            order.append(node)

        for name in self._registry:
            dfs(name)

        return order
