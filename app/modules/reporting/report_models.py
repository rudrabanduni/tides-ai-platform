from typing import Dict, Any
from pydantic import BaseModel, Field


class Report(BaseModel):
    report_id: str = Field(..., description="Unique ID for this report")
    startup_id: str = Field(..., description="Target startup ID")
    startup_name: str = Field(..., description="Target startup name")
    generated_at: str = Field(..., description="Timestamp of report generation")
    generated_by: str = Field(default="TIDES Intelligence Engine", description="User or service generating the report")
    report_version: str = Field(default="1.0.0", description="SemVer version of the report")
    report_hash: str = Field(..., description="SHA-256 integrity hash of report content")
    executive_summary: str = Field(..., description="Rendered executive summary section")
    founder_analysis: str = Field(..., description="Rendered founder & team analysis section")
    product_analysis: str = Field(..., description="Rendered product & technology section")
    market_analysis: str = Field(..., description="Rendered market & customer section")
    competition_analysis: str = Field(..., description="Rendered competitor & defensibility section")
    financial_analysis: str = Field(..., description="Rendered financial runway section")
    trl_analysis: str = Field(..., description="Rendered technology readiness level section")
    ip_analysis: str = Field(..., description="Rendered intellectual property section")
    risk_analysis: str = Field(..., description="Rendered risk exposure section")
    committee_decision: str = Field(..., description="Rendered investment committee decision section")
    investment_recommendation: str = Field(..., description="Rendered investment recommendation section")
    portfolio_position: str = Field(..., description="Rendered portfolio rank and position section")
    explainability_appendix: str = Field(..., description="Rendered explainability traces section")
    evidence_appendix: str = Field(..., description="Rendered evidence references section")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata dict")
