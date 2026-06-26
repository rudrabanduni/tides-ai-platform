from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StartupVersion(BaseModel):
    version_id: str = Field(..., description="Unique version identifier (e.g. VER-{startup_id}-{version_number})")
    startup_id: str = Field(..., description="Associated startup application ID")
    startup_name: str = Field(..., description="Name of the startup")
    version_number: int = Field(..., description="Sequential version number")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of version creation")
    created_by: str = Field(..., description="Actor ID who triggered the version creation")
    graph_hash: str = Field(..., description="Deterministic hash of the observation graph")
    workflow_id: str = Field(..., description="Associated workflow state machine identifier")
    committee_report_id: str = Field(..., description="Associated committee report identifier")
    executive_report_id: str = Field(..., description="Associated executive summary report identifier")
    investment_report_id: str = Field(..., description="Associated investment assessment report identifier")
    portfolio_snapshot_id: str = Field(..., description="Associated portfolio entry identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata tags (e.g. request_id)")


class VersionSnapshot(BaseModel):
    startup_profile: Dict[str, Any] = Field(..., description="Snapshot of the startup intelligence profile")
    observation_graph: Dict[str, Any] = Field(..., description="Snapshot of the observation graph")
    claims: List[Dict[str, Any]] = Field(default_factory=list, description="Snapshot list of startup claims")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Snapshot list of startup evidence")
    expert_assessments: List[Dict[str, Any]] = Field(default_factory=list, description="Snapshot list of expert assessments")
    risks: List[Dict[str, Any]] = Field(default_factory=list, description="Snapshot list of risks")
    questions: List[Dict[str, Any]] = Field(default_factory=list, description="Snapshot list of due diligence questions")
    conflicts: List[Dict[str, Any]] = Field(default_factory=list, description="Snapshot list of conflicts")
    committee_report: Optional[Dict[str, Any]] = Field(None, description="Snapshot of the committee report/decision")
    executive_report: Optional[Dict[str, Any]] = Field(None, description="Snapshot of the executive report")
    investment_report: Optional[Dict[str, Any]] = Field(None, description="Snapshot of the investment assessment")
    workflow_state: Optional[Dict[str, Any]] = Field(None, description="Snapshot of the workflow state")
    portfolio_snapshot: Optional[Dict[str, Any]] = Field(None, description="Snapshot of the portfolio entry ranking state")


class DeltaItem(BaseModel):
    category: str = Field(..., description="Category of change (e.g. Founder, Product, TRL, etc.)")
    field: str = Field(..., description="Field name or item identifier that changed")
    previous_value: Any = Field(None, description="Value in the starting version")
    current_value: Any = Field(None, description="Value in the ending version")
    change_type: str = Field(..., description="Type of change: ADDED, REMOVED, or MODIFIED")
    confidence: float = Field(..., description="Confidence score of this delta item")
    reasoning: str = Field(..., description="Qualitative justification of change detection")


class DeltaReport(BaseModel):
    delta_id: str = Field(..., description="Unique identifier of this delta comparison")
    from_version: int = Field(..., description="Starting version number")
    to_version: int = Field(..., description="Ending version number")
    summary: str = Field(..., description="Narrative summary highlighting major changes")
    changed_fields: List[str] = Field(default_factory=list, description="Summary list of fields that changed")
    added_items: List[DeltaItem] = Field(default_factory=list, description="Catalog of added items")
    removed_items: List[DeltaItem] = Field(default_factory=list, description="Catalog of removed items")
    modified_items: List[DeltaItem] = Field(default_factory=list, description="Catalog of modified items")
    overall_change_confidence: float = Field(..., description="Weighted average change confidence")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of report generation")
