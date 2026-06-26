from typing import Dict, List, Optional, Set
from app.modules.workflow.workflow_models import WorkflowState


class WorkflowStateMachine:
    """Manages the directed transition graph, approval gates, and terminal states."""

    def __init__(
        self,
        states: Optional[List[WorkflowState]] = None,
        transitions: Optional[Dict[str, List[str]]] = None
    ) -> None:
        # Load default states if none provided
        if states is None:
            states = self._get_default_states()
        self.states: Dict[str, WorkflowState] = {s.state_id: s for s in states}

        # Load default transitions if none provided
        if transitions is None:
            transitions = self._get_default_transitions()
        self.transitions: Dict[str, List[str]] = transitions

    def _get_default_states(self) -> List[WorkflowState]:
        return [
            WorkflowState(
                state_id="Draft",
                name="Draft",
                description="Initial application draft",
                order=1,
                terminal=False,
                requires_approval=False,
                allowed_roles=["admin", "incubation_manager", "evaluator", "reviewer", "analyst", "viewer"]
            ),
            WorkflowState(
                state_id="Submitted",
                name="Submitted",
                description="Application submitted by startup",
                order=2,
                terminal=False,
                requires_approval=True,
                allowed_roles=["admin", "incubation_manager", "evaluator", "reviewer", "analyst"]
            ),
            WorkflowState(
                state_id="Document Verification",
                name="Document Verification",
                description="Verifying submitted credentials and documents",
                order=3,
                terminal=False,
                requires_approval=True,
                allowed_roles=["admin", "incubation_manager", "reviewer"]
            ),
            WorkflowState(
                state_id="Expert Evaluation",
                name="Expert Evaluation",
                description="Expert agents run domain analyses",
                order=4,
                terminal=False,
                requires_approval=True,
                allowed_roles=["admin", "incubation_manager", "evaluator"]
            ),
            WorkflowState(
                state_id="Committee Review",
                name="Committee Review",
                description="Incubation committee decision review",
                order=5,
                terminal=False,
                requires_approval=True,
                allowed_roles=["admin", "incubation_manager", "committee_member"]
            ),
            WorkflowState(
                state_id="Due Diligence",
                name="Due Diligence",
                description="Deep dive audits and validation",
                order=6,
                terminal=False,
                requires_approval=True,
                allowed_roles=["admin", "incubation_manager", "reviewer"]
            ),
            WorkflowState(
                state_id="Investment Decision",
                name="Investment Decision",
                description="Final investment scoring and checks",
                order=7,
                terminal=False,
                requires_approval=True,
                allowed_roles=["admin", "incubation_manager"]
            ),
            WorkflowState(
                state_id="Incubation",
                name="Incubation",
                description="Startup accepted into incubation",
                order=8,
                terminal=False,
                requires_approval=True,
                allowed_roles=["admin", "incubation_manager"]
            ),
            WorkflowState(
                state_id="Portfolio Monitoring",
                name="Portfolio Monitoring",
                description="Active portfolio tracking and ranking",
                order=9,
                terminal=False,
                requires_approval=False,
                allowed_roles=["admin", "incubation_manager", "analyst"]
            ),
            WorkflowState(
                state_id="Graduated",
                name="Graduated",
                description="Successfully finished incubation",
                order=10,
                terminal=False, # Can be archived next
                requires_approval=True,
                allowed_roles=["admin", "incubation_manager"]
            ),
            WorkflowState(
                state_id="Archived",
                name="Archived",
                description="Archived and read-only",
                order=11,
                terminal=True, # Cannot transition out
                requires_approval=True,
                allowed_roles=["admin", "incubation_manager"]
            ),
        ]

    def _get_default_transitions(self) -> Dict[str, List[str]]:
        return {
            "Draft": ["Submitted", "Archived"],
            "Submitted": ["Document Verification", "Draft", "Archived"],
            "Document Verification": ["Expert Evaluation", "Draft", "Archived"],
            "Expert Evaluation": ["Committee Review", "Draft", "Archived"],
            "Committee Review": ["Due Diligence", "Investment Decision", "Draft", "Archived"],
            "Due Diligence": ["Investment Decision", "Draft", "Archived"],
            "Investment Decision": ["Incubation", "Draft", "Archived"],
            "Incubation": ["Portfolio Monitoring", "Archived"],
            "Portfolio Monitoring": ["Graduated", "Archived"],
            "Graduated": ["Archived"],
            "Archived": []
        }

    def is_transition_allowed(self, from_state: Optional[str], to_state: str) -> bool:
        """Verify if transition is defined in the directed graph."""
        if not from_state:
            # Creation transition (entering Draft)
            return to_state in self.states

        if from_state not in self.states or to_state not in self.states:
            return False

        # Terminal state check
        if self.states[from_state].terminal:
            return False

        allowed = self.transitions.get(from_state, [])
        return to_state in allowed

    def get_state(self, state_id: str) -> Optional[WorkflowState]:
        return self.states.get(state_id)

    def validate_approval_gate(self, to_state_id: str, approval_metadata: Dict[str, Any]) -> bool:
        """Enforces gate checks if required by target state."""
        state = self.get_state(to_state_id)
        if not state:
            return False
        if not state.requires_approval:
            return True
        
        # Must have approval flag in metadata or transition payload
        approved = approval_metadata.get("approved") or approval_metadata.get("gate_approved")
        return bool(approved)
