from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TransitionRequest(BaseModel):
    """Schema model for executing lifecycle state transitions via REST APIs."""
    to_state: str = Field(..., description="Target lifecycle state to transition into")
    actor: str = Field(..., description="ID or username of the user triggering the transition")
    role: str = Field(..., description="The RBAC role of the actor")
    justification: str = Field(..., description="Explanation/reasoning for this transition")
    evidence: List[str] = Field(default_factory=list, description="Associated document references or evidence IDs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata context parameters and gate details")


class RollbackRequest(BaseModel):
    """Schema model for executing rollbacks via REST APIs."""
    target_state: str = Field(..., description="Target lifecycle state to revert back to")
    actor: str = Field(..., description="ID or username of the user triggering the rollback")
    role: str = Field(..., description="The RBAC role of the actor")
    reason: str = Field(..., description="Detailed explanation/reasoning for the rollback")


# Lifecycle state constant IDs
class StateName:
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    DOCUMENT_VERIFICATION = "Document Verification"
    EXPERT_EVALUATION = "Expert Evaluation"
    COMMITTEE_REVIEW = "Committee Review"
    DUE_DILIGENCE = "Due Diligence"
    INVESTMENT_DECISION = "Investment Decision"
    INCUBATION = "Incubation"
    PORTFOLIO_MONITORING = "Portfolio Monitoring"
    GRADUATED = "Graduated"
    ARCHIVED = "Archived"
