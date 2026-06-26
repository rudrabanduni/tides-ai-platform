from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class WorkflowState(BaseModel):
    state_id: str = Field(..., description="Unique state ID (e.g. DRAFT, SUBMITTED)")
    name: str = Field(..., description="Friendly name of the state")
    description: str = Field(..., description="Description of the state's role in the lifecycle")
    order: int = Field(..., description="Sequential order in the default pipeline")
    terminal: bool = Field(default=False, description="Flag indicating if this is a terminal state")
    requires_approval: bool = Field(default=False, description="Flag indicating if this state requires approval gates")
    allowed_roles: List[str] = Field(default_factory=list, description="Roles authorized to transition into/out of this state")


class WorkflowTransition(BaseModel):
    transition_id: str = Field(..., description="Unique ID of the transition execution")
    from_state: Optional[str] = Field(None, description="Source state name/ID")
    to_state: str = Field(..., description="Destination state name/ID")
    triggered_by: str = Field(..., description="User ID or identifier who triggered the transition")
    timestamp: datetime = Field(..., description="Timestamp when the transition occurred")
    justification: str = Field(..., description="Human justification for the transition")
    evidence: List[str] = Field(default_factory=list, description="Citations/documents/IDs as evidence for the transition")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context parameters")


class WorkflowHistoryEntry(BaseModel):
    transition_id: str = Field(..., description="Reference to the WorkflowTransition ID")
    actor: str = Field(..., description="User ID or username who triggered this change")
    role: str = Field(..., description="Role of the actor who performed the transition")
    previous_state: Optional[str] = Field(None, description="Previous state name/ID")
    new_state: str = Field(..., description="New state name/ID")
    timestamp: datetime = Field(..., description="Time of status update")
    reason: str = Field(..., description="Reason/justification description")
    audit_reference: str = Field(..., description="Associated Security Audit Log resource/action signature")


class Workflow(BaseModel):
    workflow_id: str = Field(..., description="Unique ID of this workflow process")
    startup_id: str = Field(..., description="Associated startup application ID")
    startup_name: str = Field(..., description="Name of the startup")
    current_state: str = Field(..., description="Current state in the lifecycle")
    previous_state: Optional[str] = Field(None, description="Previous state in the lifecycle")
    created_at: datetime = Field(..., description="Timestamp when the workflow was created")
    updated_at: datetime = Field(..., description="Timestamp of the latest transition")
    created_by: str = Field(..., description="User ID who created the workflow")
    last_modified_by: str = Field(..., description="User ID who last edited the workflow state")
    workflow_version: str = Field(default="1.0.0", description="Version of the workflow structure")
    workflow_hash: str = Field(..., description="SHA-256 integrity signature of the workflow data")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom properties and workflow context")
