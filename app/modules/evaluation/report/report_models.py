from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.modules.evaluation.graph.graph_models import GraphNode, NodeType


class ReportSection(BaseModel):
    section_id: str
    title: str
    content: str
    supporting_nodes: List[str] = Field(default_factory=list)
    confidence: float


class Appendix(BaseModel):
    appendix_id: str
    title: str
    content: str


class DueDiligenceReport(GraphNode):
    report_id: str
    generated_at: str
    graph_version: str = "1.0.0"

    # 11 Structured Report Sections:
    executive_summary: ReportSection
    investment_recommendation: ReportSection
    founder_assessment: ReportSection
    product_technology: ReportSection
    market_opportunity: ReportSection
    business_model: ReportSection
    competition: ReportSection
    financial_overview: ReportSection
    risks: ReportSection
    investment_thesis: ReportSection
    follow_up_questions: ReportSection

    # Backward-compatible fields:
    investment_summary: Optional[ReportSection] = None
    founder_analysis: Optional[ReportSection] = None
    product_analysis: Optional[ReportSection] = None
    trl_analysis: Optional[ReportSection] = None
    market_analysis: Optional[ReportSection] = None
    competition_analysis: Optional[ReportSection] = None
    financial_analysis: Optional[ReportSection] = None
    ip_analysis: Optional[ReportSection] = None
    risk_analysis: Optional[ReportSection] = None
    observations: Optional[ReportSection] = None
    conflicts: Optional[ReportSection] = None
    resolutions: Optional[ReportSection] = None
    missing_information: Optional[ReportSection] = None

    appendices: List[Appendix] = Field(default_factory=list)
    traceability: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
