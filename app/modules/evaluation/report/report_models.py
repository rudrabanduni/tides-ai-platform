from typing import List, Dict, Any
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
    executive_summary: ReportSection
    investment_summary: ReportSection
    founder_analysis: ReportSection
    product_analysis: ReportSection
    trl_analysis: ReportSection
    market_analysis: ReportSection
    competition_analysis: ReportSection
    financial_analysis: ReportSection
    ip_analysis: ReportSection
    risk_analysis: ReportSection
    observations: ReportSection
    risks: ReportSection
    conflicts: ReportSection
    resolutions: ReportSection
    missing_information: ReportSection
    follow_up_questions: ReportSection
    appendices: List[Appendix] = Field(default_factory=list)
    traceability: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
