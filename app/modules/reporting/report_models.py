from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ReportSection(BaseModel):
    summary: str
    observations: List[Dict[str, Any]] = Field(default_factory=list)
    supporting_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)


class RiskMatrixItem(BaseModel):
    severity: str = "LOW"  # "HIGH", "MEDIUM", "LOW"
    confidence: float = 0.0
    evidence: List[str] = Field(default_factory=list)
    recommendation: str = ""


class RiskMatrix(BaseModel):
    technical: RiskMatrixItem
    execution: RiskMatrixItem
    market: RiskMatrixItem
    competition: RiskMatrixItem
    financial: RiskMatrixItem
    regulatory: RiskMatrixItem
    ip: RiskMatrixItem


class InvestmentSummarySection(BaseModel):
    investment_readiness: str
    grant_readiness: str
    vc_readiness: str
    trl: int
    portfolio_rank: Optional[int] = None
    recommendation: str


class DueDiligenceReport(BaseModel):
    report_id: str
    startup_id: str
    startup_name: str
    generated_at: str
    generated_by: str
    graph_hash: str
    profile_version: str
    overall_score: float
    overall_confidence: float

    executive_summary: str

    founder_assessment: ReportSection
    product_assessment: ReportSection
    market_assessment: ReportSection
    competition_assessment: ReportSection
    trl_assessment: ReportSection
    financial_assessment: ReportSection
    ip_assessment: ReportSection
    risk_assessment: ReportSection
    investment_assessment: ReportSection

    portfolio_position: str

    key_strengths: List[str] = Field(default_factory=list)
    key_weaknesses: List[str] = Field(default_factory=list)
    major_risks: List[str] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    committee_questions: List[str] = Field(default_factory=list)

    risk_matrix: RiskMatrix
    investment_summary: InvestmentSummarySection

    appendix: str
    traceability: Dict[str, Any] = Field(default_factory=dict)
    report_hash: str = ""


# Keep legacy Report model for backward compatibility
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
