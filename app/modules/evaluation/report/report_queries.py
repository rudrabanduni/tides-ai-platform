from typing import List, Optional, Any, Dict
from app.modules.evaluation.graph.graph_models import ObservationGraph
from app.modules.evaluation.report.report_models import (
    DueDiligenceReport, ReportSection, Appendix
)


def get_report(graph: ObservationGraph) -> Optional[DueDiligenceReport]:
    """Retrieves the DueDiligenceReport from the graph in O(1) time."""
    return graph.report


def get_summary(graph: ObservationGraph) -> Optional[ReportSection]:
    """Retrieves the executive summary ReportSection from the graph's report in O(1) time."""
    report = graph.report
    return report.executive_summary if report else None


def get_section(graph: ObservationGraph, section_id: str) -> Optional[ReportSection]:
    """Retrieves a specific ReportSection by its ID in O(1) time."""
    report = graph.report
    if not report:
        return None
    # Lookup by section attribute name
    if hasattr(report, section_id):
        val = getattr(report, section_id)
        if isinstance(val, ReportSection):
            return val
    return None


def get_appendices(graph: ObservationGraph) -> List[Appendix]:
    """Retrieves all Appendices in the report in O(1) time."""
    report = graph.report
    return report.appendices if report else []


def trace_report_section(graph: ObservationGraph, section_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves the complete pedigree provenance trace mapping for a specific section in O(1) time."""
    report = graph.report
    if report and section_id in report.traceability:
        return report.traceability[section_id]
    return None
