import uuid
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.modules.workflow.workflow_models import Workflow, WorkflowTransition, WorkflowHistoryEntry
from app.modules.workflow.workflow_state_machine import WorkflowStateMachine
from app.modules.workflow.workflow_validator import WorkflowValidator, WorkflowValidationError
from app.modules.workflow import workflow_events
from app.modules.workflow.workflow_queries import register_workflow, register_history_entry, get_workflow, get_history
from app.security.audit import security_audit_service


class WorkflowEngine:
    """Core orchestration engine for workflow lifecycle operations."""

    @staticmethod
    def _compute_hash(workflow_data: dict) -> str:
        """Compute deterministic SHA-256 hash over workflow fields, ignoring volatile fields."""
        data = workflow_data.copy()
        data.pop("workflow_hash", None)
        data.pop("workflow_id", None)
        data.pop("created_at", None)
        data.pop("updated_at", None)
        # Convert datetimes/UUIDs to string
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def create_workflow(
        startup_id: str,
        startup_name: str,
        created_by: str,
        state_machine: Optional[WorkflowStateMachine] = None,
        metadata: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None
    ) -> Workflow:
        """Create and start a new workflow process in the initial 'Draft' state."""
        # Prevent duplicate workflows for the same startup
        from app.modules.workflow.workflow_queries import list_workflows
        for w in list_workflows():
            if w.startup_id == startup_id:
                raise WorkflowValidationError(f"Workflow for startup '{startup_id}' already exists.")

        workflow_id = f"WF-{str(uuid.uuid4())[:8].upper()}"
        now = datetime.now(timezone.utc)
        
        # Build raw dict to calculate hash
        workflow_data = {
            "workflow_id": workflow_id,
            "startup_id": startup_id,
            "startup_name": startup_name,
            "current_state": "Draft",
            "previous_state": None,
            "created_at": now,
            "updated_at": now,
            "created_by": created_by,
            "last_modified_by": created_by,
            "workflow_version": "1.0.0",
            "metadata": metadata or {}
        }
        
        workflow_hash = WorkflowEngine._compute_hash(workflow_data)
        workflow_data["workflow_hash"] = workflow_hash
        
        workflow = Workflow(**workflow_data)

        # Validate startup existence if DB session is provided
        if db:
            from app.modules.startups.models import StartupApplication
            from sqlalchemy import select
            
            try:
                parsed_uuid = uuid.UUID(startup_id)
                stmt = select(StartupApplication).where(StartupApplication.id == parsed_uuid)
            except ValueError:
                stmt = select(StartupApplication).where(StartupApplication.id == startup_id)
                
            startup = db.scalars(stmt).first()
            if not startup:
                raise WorkflowValidationError(f"Startup application with ID '{startup_id}' does not exist.")

        # Register in global registry
        register_workflow(workflow)

        # Write security audit log
        security_audit_service.log(
            actor=created_by,
            action="workflow.create",
            resource=f"workflow:{workflow_id}",
            status="success",
            details={
                "startup_id": startup_id,
                "startup_name": startup_name,
                "initial_state": "Draft"
            }
        )

        # Publish events
        workflow_events.publish_workflow_created(workflow_id, startup_id, startup_name, {"created_by": created_by})
        workflow_events.publish_workflow_started(workflow_id, startup_id, {"started_by": created_by})

        return workflow

    @staticmethod
    def execute_transition(
        workflow_id: str,
        to_state: str,
        actor: str,
        role: str,
        justification: str,
        evidence: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        state_machine: Optional[WorkflowStateMachine] = None,
        db: Optional[Session] = None
    ) -> Workflow:
        """Executes state transition in the lifecycle, auditing progress and checking rules."""
        workflow = get_workflow(workflow_id)
        if not workflow:
            raise WorkflowValidationError(f"Workflow '{workflow_id}' does not exist.")

        if not state_machine:
            state_machine = WorkflowStateMachine()

        from_state = workflow.current_state

        # Validate transition rules
        val_res = WorkflowValidator.validate_transition(
            workflow=workflow,
            to_state=to_state,
            actor_role=role,
            approval_metadata=metadata or {},
            state_machine=state_machine,
            db=db
        )

        if val_res["errors"]:
            # Publish failed event
            workflow_events.publish_workflow_transition_failed(
                workflow_id=workflow_id,
                from_state=from_state,
                to_state=to_state,
                error="; ".join(val_res["errors"]),
                payload={"actor": actor, "role": role}
            )
            # Security audit logging failure
            security_audit_service.log(
                actor=actor,
                action="workflow.transition",
                resource=f"workflow:{workflow_id}",
                status="failure",
                details={
                    "from_state": from_state,
                    "to_state": to_state,
                    "reason": "; ".join(val_res["errors"])
                }
            )
            raise WorkflowValidationError(
                f"Transition from '{from_state}' to '{to_state}' failed validation checks.",
                errors=val_res["errors"]
            )

        # Publish started event
        workflow_events.publish_workflow_transition_started(
            workflow_id=workflow_id,
            from_state=from_state,
            to_state=to_state,
            payload={"actor": actor, "role": role}
        )

        now = datetime.now(timezone.utc)
        transition_id = f"TR-{str(uuid.uuid4())[:8].upper()}"

        # Update workflow parameters
        workflow.previous_state = from_state
        workflow.current_state = to_state
        workflow.last_modified_by = actor
        workflow.updated_at = now
        
        # Merge metadata
        if metadata:
            workflow.metadata.update(metadata)

        # Compute new workflow hash
        workflow.workflow_hash = WorkflowEngine._compute_hash(workflow.model_dump())

        # Construct transition detail
        transition = WorkflowTransition(
            transition_id=transition_id,
            from_state=from_state,
            to_state=to_state,
            triggered_by=actor,
            timestamp=now,
            justification=justification,
            evidence=evidence or [],
            metadata=metadata or {}
        )

        # Construct history entry
        audit_reference = f"audit:{transition_id}"
        history_entry = WorkflowHistoryEntry(
            transition_id=transition_id,
            actor=actor,
            role=role,
            previous_state=from_state,
            new_state=to_state,
            timestamp=now,
            reason=justification,
            audit_reference=audit_reference
        )

        # Register changes in registries
        register_workflow(workflow)
        register_history_entry(workflow_id, history_entry)

        # Log transition to audit service
        security_audit_service.log(
            actor=actor,
            action="workflow.transition",
            resource=f"workflow:{workflow_id}",
            status="success",
            details={
                "transition_id": transition_id,
                "from_state": from_state,
                "to_state": to_state,
                "justification": justification,
                "audit_ref": audit_reference
            }
        )

        # Publish completed events
        workflow_events.publish_workflow_transition_completed(
            workflow_id=workflow_id,
            from_state=from_state,
            to_state=to_state,
            payload={"actor": actor, "role": role, "transition_id": transition_id}
        )

        # Terminal state specific event emissions
        target_state_config = state_machine.get_state(to_state)
        if target_state_config and target_state_config.terminal:
            if to_state == "Archived":
                workflow_events.publish_workflow_archived(workflow_id, {"archived_by": actor})
            else:
                workflow_events.publish_workflow_completed(workflow_id, {"completed_by": actor})

        return workflow

    @staticmethod
    def rollback_workflow(
        workflow_id: str,
        target_state: str,
        actor: str,
        role: str,
        reason: str,
        state_machine: Optional[WorkflowStateMachine] = None,
        db: Optional[Session] = None
    ) -> Workflow:
        """Rollback the workflow current state to a previously visited state, maintaining history."""
        workflow = get_workflow(workflow_id)
        if not workflow:
            raise WorkflowValidationError(f"Workflow '{workflow_id}' does not exist.")

        if not state_machine:
            state_machine = WorkflowStateMachine()

        history = get_history(workflow_id)

        # Validate rollback target eligibility
        val_res = WorkflowValidator.validate_rollback(workflow, target_state, history, state_machine)
        if val_res["errors"]:
            raise WorkflowValidationError(
                f"Rollback to state '{target_state}' failed validation checks.",
                errors=val_res["errors"]
            )

        from_state = workflow.current_state
        now = datetime.now(timezone.utc)
        transition_id = f"RB-{str(uuid.uuid4())[:8].upper()}"

        # Revert state values
        workflow.previous_state = from_state
        workflow.current_state = target_state
        workflow.last_modified_by = actor
        workflow.updated_at = now

        # Re-compute workflow hash
        workflow.workflow_hash = WorkflowEngine._compute_hash(workflow.model_dump())

        # Construct rollback history entry
        audit_reference = f"audit:{transition_id}"
        history_entry = WorkflowHistoryEntry(
            transition_id=transition_id,
            actor=actor,
            role=role,
            previous_state=from_state,
            new_state=target_state,
            timestamp=now,
            reason=f"ROLLBACK: {reason}",
            audit_reference=audit_reference
        )

        # Persist reverted changes
        register_workflow(workflow)
        register_history_entry(workflow_id, history_entry)

        # Log rollback to audit service
        security_audit_service.log(
            actor=actor,
            action="workflow.rollback",
            resource=f"workflow:{workflow_id}",
            status="success",
            details={
                "transition_id": transition_id,
                "from_state": from_state,
                "to_state": target_state,
                "reason": reason,
                "audit_ref": audit_reference
            }
        )

        # Publish rolled back event
        workflow_events.publish_workflow_rolled_back(
            workflow_id=workflow_id,
            from_state=from_state,
            to_state=target_state,
            payload={"actor": actor, "role": role, "reason": reason}
        )

        return workflow
