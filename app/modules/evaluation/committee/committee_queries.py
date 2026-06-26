from typing import List, Dict, Any, Optional
import threading
from app.modules.evaluation.committee.committee_models import (
    InvestmentCommitteeDecision, Recommendation, Priority,
    CommitteeReport, CommitteeFinding, CommitteeConcern, CommitteeRecommendation
)

# Thread-safe global store for generated committee reports
_report_registry: Dict[str, CommitteeReport] = {}
_registry_lock = threading.RLock()


def register_report(report: CommitteeReport) -> None:
    """Store a report in the global registry."""
    with _registry_lock:
        _report_registry[report.decision.decision_id] = report


def clear_report_registry() -> None:
    """Clear all stored reports (test helper)."""
    with _registry_lock:
        _report_registry.clear()



def get_ready_for_incubation(decisions: List[InvestmentCommitteeDecision]) -> List[InvestmentCommitteeDecision]:
    """Filters decisions ready for incubation (INCUBATE or INCUBATE_AFTER_DD)."""
    return [d for d in decisions if d.recommendation in (Recommendation.INCUBATE, Recommendation.INCUBATE_AFTER_DD)]


def get_high_priority(decisions: List[InvestmentCommitteeDecision]) -> List[InvestmentCommitteeDecision]:
    """Filters decisions with critical or high investment priority."""
    return [d for d in decisions if d.investment_priority in (Priority.CRITICAL, Priority.HIGH)]


def get_pending_dd(decisions: List[InvestmentCommitteeDecision]) -> List[InvestmentCommitteeDecision]:
    """Filters decisions containing blocking due diligence requirements."""
    return [d for d in decisions if any(item.blocking for item in d.required_due_diligence)]


def get_deferred(decisions: List[InvestmentCommitteeDecision]) -> List[InvestmentCommitteeDecision]:
    """Filters decisions with DEFER recommendation."""
    return [d for d in decisions if d.recommendation == Recommendation.DEFER]


def get_rejected(decisions: List[InvestmentCommitteeDecision]) -> List[InvestmentCommitteeDecision]:
    """Filters decisions with REJECT recommendation."""
    return [d for d in decisions if d.recommendation == Recommendation.REJECT]


def get_by_startup(decisions: List[InvestmentCommitteeDecision], startup_id: str) -> Optional[InvestmentCommitteeDecision]:
    """Retrieves decision for a specific startup by ID."""
    for d in decisions:
        if d.startup_id == startup_id:
            return d
    return None


def statistics(decisions: List[InvestmentCommitteeDecision]) -> Dict[str, Any]:
    """Generates aggregate statistics across a collection of committee decisions."""
    total = len(decisions)
    if total == 0:
        return {
            "total_decisions": 0,
            "ready_for_incubation": 0,
            "pending_due_diligence": 0,
            "average_confidence": 0.0,
            "recommendation_distribution": {},
            "priority_distribution": {}
        }
    
    ready = len(get_ready_for_incubation(decisions))
    pending_dd = len(get_pending_dd(decisions))
    avg_conf = sum(d.decision_confidence for d in decisions) / total
    
    rec_dist = {}
    prio_dist = {}
    for d in decisions:
        rec_dist[d.recommendation.value] = rec_dist.get(d.recommendation.value, 0) + 1
        prio_dist[d.investment_priority.value] = prio_dist.get(d.investment_priority.value, 0) + 1
        
    return {
        "total_decisions": total,
        "ready_for_incubation": ready,
        "pending_due_diligence": pending_dd,
        "average_confidence": round(avg_conf, 4),
        "recommendation_distribution": rec_dist,
        "priority_distribution": prio_dist
    }


def committee_dashboard(decisions: List[InvestmentCommitteeDecision]) -> Dict[str, Any]:
    """Formats decision summaries and top priority startups for dashboard consumption."""
    stats = statistics(decisions)
    top_items = [
        {
            "decision_id": d.decision_id,
            "startup_id": d.startup_id,
            "startup_name": d.startup_name,
            "recommendation": d.recommendation.value,
            "priority": d.investment_priority.value,
            "portfolio_rank": d.portfolio_rank,
            "confidence": d.decision_confidence
        }
        for d in sorted(decisions, key=lambda x: x.portfolio_rank)[:5]
    ]
    return {
        "summary": stats,
        "top_startups": top_items
    }


def generate_report(graph: Any, workflow_reference: str, metadata: Optional[Dict[str, Any]] = None) -> CommitteeReport:
    """Generates a new committee report and registers it."""
    from app.modules.evaluation.committee.committee_engine import generate_committee_report
    report = generate_committee_report(graph, workflow_reference, metadata)
    return report


def get_report(report_id: str) -> Optional[CommitteeReport]:
    """Retrieve a committee report by ID from the global registry (accepts decision_id or REP-COMM- prefix)."""
    with _registry_lock:
        if report_id in _report_registry:
            return _report_registry[report_id]
        
        for key, report in _report_registry.items():
            if report.decision.startup_id in report_id or key in report_id or report_id in key:
                return report
        return None


def list_reports() -> List[CommitteeReport]:
    """List all registered committee reports."""
    with _registry_lock:
        return list(_report_registry.values())


def list_reports_by_startup(startup_id: str) -> List[CommitteeReport]:
    """List all reports matching a startup ID."""
    with _registry_lock:
        return [r for r in _report_registry.values() if r.decision.startup_id == startup_id]


def list_reports_by_decision(decision_id: str) -> List[CommitteeReport]:
    """List all reports matching a decision ID."""
    with _registry_lock:
        return [r for r in _report_registry.values() if r.decision.decision_id == decision_id]


def get_committee_findings(report_id: str) -> List[CommitteeFinding]:
    """Get findings for a report."""
    report = get_report(report_id)
    return report.findings if report else []


def get_committee_concerns(report_id: str) -> List[CommitteeConcern]:
    """Get concerns for a report."""
    report = get_report(report_id)
    return report.concerns if report else []


def get_committee_recommendations(report_id: str) -> Optional[CommitteeRecommendation]:
    """Get recommendation for a report."""
    report = get_report(report_id)
    return report.recommendations if report else None


def get_traceability(report_id: str) -> Dict[str, Any]:
    """Get traceability metadata for a report."""
    report = get_report(report_id)
    return report.traceability if report else {}


def export_report(report_id: str, format_str: str) -> Any:
    """Export report to a specific format (json, markdown, html)."""
    report = get_report(report_id)
    if not report:
        return None
        
    from app.modules.evaluation.committee.committee_serializer import CommitteeSerializer
    fmt = format_str.lower()
    if fmt == "json":
        return CommitteeSerializer.to_json(report)
    elif fmt == "markdown" or fmt == "md":
        return CommitteeSerializer.to_markdown(report)
    elif fmt == "html":
        return CommitteeSerializer.to_html(report)
    elif fmt == "pdf":
        return report.model_dump()
    return None

