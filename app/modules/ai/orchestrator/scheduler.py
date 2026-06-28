from typing import List, Dict, Set
from app.modules.ai.agents.base_agent import BaseAgent

class Scheduler:
    @staticmethod
    def get_execution_phases(agents: List[BaseAgent]) -> List[List[BaseAgent]]:
        """Groups agents into sequential execution phases. Agents in the same phase can run concurrently."""
        agent_map = {a.agent_name: a for a in agents}
        
        # Track registered dependencies
        dependencies: Dict[str, Set[str]] = {}
        for a in agents:
            dependencies[a.agent_name] = {dep for dep in a.dependencies if dep in agent_map}
            
        phases: List[List[BaseAgent]] = []
        executed: Set[str] = set()
        
        while len(executed) < len(agents):
            current_phase: List[BaseAgent] = []
            for name, deps in dependencies.items():
                if name in executed:
                    continue
                # Ready if all dependencies are satisfied
                if deps.issubset(executed):
                    current_phase.append(agent_map[name])
                    
            if not current_phase:
                # Cycle fallback: execution order might be broken but we schedule remaining to avoid hang
                remaining = [agent_map[name] for name in dependencies if name not in executed]
                phases.append(remaining)
                break
                
            phases.append(current_phase)
            executed.update(a.agent_name for a in current_phase)
            
        return phases
