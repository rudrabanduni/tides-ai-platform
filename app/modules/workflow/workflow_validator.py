import json
import hashlib
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.modules.workflow.workflow_models import Workflow
from app.modules.workflow.workflow_state_machine import WorkflowStateMachine
from app.security.roles import role_manager


class WorkflowValidationError(Exception):
    """Exception raised for workflow validation failures."""
    def __init__(self, message: str, errors: Optional[List[str]] = None) -> None:
        super().__init__(message)
        self.errors = errors or [message]


class WorkflowValidator:
    """Validator for verifying workflow states, transitions, authorization, and integrity."""

    @staticmethod
    def validate_transition(
        workflow: Workflow,
        to_state: str,
        actor_role: str,
        approval_metadata: Dict[str, Any],
        state_machine: WorkflowStateMachine,
        db: Optional[Session] = None
    ) -> Dict[str, List[str]]:
        """Validate if the proposed transition is allowed and meets all authorization/gate criteria."""
        errors = []

        # 1. State existence check
        from_state = workflow.current_state
        target_state = state_machine.get_state(to_state)
        if not target_state:
            errors.append(f"State '{to_state}' does not exist.")

        if from_state:
            source_state = state_machine.get_state(from_state)
            if not source_state:
                errors.append(f"Current state '{from_state}' does not exist.")
            # 2. Terminal state cannot transition check
            elif source_state.terminal:
                errors.append(f"Terminal state '{from_state}' cannot initiate transitions.")

        # 3. Transition existence check
        if target_state and not state_machine.is_transition_allowed(from_state, to_state):
            errors.append(f"Transition from '{from_state}' to '{to_state}' is not allowed in state machine.")

        # 4. Actor authorization check
        if target_state:
            # Check if actor_role is recognized and has the authority to enter the target state.
            # We enforce that actor_role must satisfy at least one of the allowed_roles for the target state.
            if target_state.allowed_roles:
                authorized = False
                for allowed in target_state.allowed_roles:
                    if role_manager.has_role(actor_role, allowed):
                        authorized = True
                        break
                if not authorized:
                    errors.append(f"Actor with role '{actor_role}' is not authorized to transition to '{to_state}'.")

        # 5. Approval gate check
        if target_state and target_state.requires_approval:
            if not state_machine.validate_approval_gate(to_state, approval_metadata):
                errors.append(f"Approval gate requirements not satisfied for state '{to_state}'.")

        # 6. Startup existence check (if DB session provided)
        if db:
            from app.modules.startups.models import StartupApplication
            from sqlalchemy import select
            import uuid
            
            startup_id = workflow.startup_id
            try:
                parsed_uuid = uuid.UUID(startup_id)
                stmt = select(StartupApplication).where(StartupApplication.id == parsed_uuid)
            except ValueError:
                stmt = select(StartupApplication).where(StartupApplication.id == startup_id)
            
            startup = db.scalars(stmt).first()
            if not startup:
                errors.append(f"Startup application with ID '{startup_id}' does not exist in DB.")

        return {"errors": errors}

    @staticmethod
    def validate_hash(workflow: Workflow, computed_hash: str) -> bool:
        """Validate if the workflow hash matches computed hash."""
        return workflow.workflow_hash == computed_hash

    @staticmethod
    def validate_rollback(workflow: Workflow, target_state: str, history: List[Any], state_machine: WorkflowStateMachine) -> Dict[str, List[str]]:
        """Verify if a rollback to a target state is valid."""
        errors = []
        
        if target_state not in state_machine.states:
            errors.append(f"Rollback target state '{target_state}' does not exist.")
            
        # Check if target state exists in history
        has_visited = False
        for entry in history:
            # Entry is history entry model or dict
            entry_state = getattr(entry, "new_state", None) or entry.get("new_state")
            if entry_state == target_state:
                has_visited = True
                break
                
        if not has_visited and target_state != "Draft":
            errors.append(f"Rollback target state '{target_state}' has not been visited in the workflow history.")
            
        return {"errors": errors}
