import threading
from typing import Dict, Optional, Any

from app.modules.reporting.report_models import Report

# Thread-safe global store for generated reports
_report_registry: Dict[str, Report] = {}
_registry_lock = threading.RLock()


def register_report(report: Report) -> None:
    """Store a report in the global registry."""
    with _registry_lock:
        _report_registry[report.report_id] = report


def get_report(report_id: str) -> Optional[Report]:
    """Retrieve a report by ID from the global registry."""
    with _registry_lock:
        return _report_registry.get(report_id)


def get_latest_report(startup_id: str) -> Optional[Report]:
    """Retrieve the latest report generated for a specific startup ID."""
    with _registry_lock:
        latest: Optional[Report] = None
        for r in _report_registry.values():
            if r.startup_id == startup_id:
                if latest is None or r.generated_at > latest.generated_at:
                    latest = r
        return latest


def get_report_sections(report: Report) -> Dict[str, str]:
    """Return a dictionary of all section names mapped to their rendered text content."""
    return {
        "executive_summary": report.executive_summary,
        "founder_analysis": report.founder_analysis,
        "product_analysis": report.product_analysis,
        "market_analysis": report.market_analysis,
        "competition_analysis": report.competition_analysis,
        "financial_analysis": report.financial_analysis,
        "trl_analysis": report.trl_analysis,
        "ip_analysis": report.ip_analysis,
        "risk_analysis": report.risk_analysis,
        "committee_decision": report.committee_decision,
        "investment_recommendation": report.investment_recommendation,
        "portfolio_position": report.portfolio_position,
        "explainability_appendix": report.explainability_appendix,
        "evidence_appendix": report.evidence_appendix,
    }


def get_report_metadata(report: Report) -> Dict[str, Any]:
    """Retrieve metadata map from the Report."""
    return report.metadata


def clear_report_registry() -> None:
    """Clear all stored reports (test helper)."""
    with _registry_lock:
        _report_registry.clear()
