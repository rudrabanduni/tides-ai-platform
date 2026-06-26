from typing import Dict, List
import json
from app.modules.evaluation.graph.graph_models import ObservationGraph, NodeType
from app.modules.reporting.report_models import Report
from app.modules.reporting.report_builder import ReportBuilder


class ReportValidationError(ValueError):
    """Exception raised when a report fails validation."""
    pass


class ReportValidator:
    """Validates Report completeness, referential integrity, and serialization correctness."""

    @staticmethod
    def validate_report(report: Report, graph: ObservationGraph) -> Dict[str, List[str]]:
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Required sections exist
        required_fields = [
            "executive_summary",
            "founder_analysis",
            "product_analysis",
            "market_analysis",
            "competition_analysis",
            "financial_analysis",
            "trl_analysis",
            "ip_analysis",
            "risk_analysis",
            "committee_decision",
            "investment_recommendation",
            "portfolio_position",
            "explainability_appendix",
            "evidence_appendix"
        ]
        
        for field in required_fields:
            val = getattr(report, field, "")
            if not val or not isinstance(val, str):
                errors.append(f"Missing Section: Section '{field}' is empty or not a string")
            elif "has not been compiled" in val.lower():
                warnings.append(f"Incomplete Section: Section '{field}' contains compilation stubs")

        # 2. Executive summary exists
        if "has not been compiled" in report.executive_summary.lower():
            errors.append("Missing Executive Summary: Executive Assessment is missing or not compiled")

        # 3. Committee section exists
        if "has not been compiled" in report.committee_decision.lower():
            errors.append("Missing Committee Decision: Committee Decision is missing or not compiled")

        # 4. Report hash is valid
        report_dict = report.model_dump() if hasattr(report, "model_dump") else report.__dict__.copy()
        recomputed = ReportBuilder._compute_hash(report_dict)
        if report.report_hash != recomputed:
            errors.append(f"Invalid Report Hash: Report hash '{report.report_hash}' does not match recomputed hash '{recomputed}'")

        # 5. Metadata is complete
        meta = report.metadata
        required_meta = ["graph_hash", "graph_version", "active_risks_count", "total_evidence_referenced"]
        for key in required_meta:
            if key not in meta:
                errors.append(f"Incomplete Metadata: Missing metadata key '{key}'")

        # Determine suppressed/active observations
        suppressed_obs = set()
        for res in graph.resolutions.values():
            if res.preferred_observation_id:
                conflict_id = res.conflict_id
                obs_ids = []
                conflict_node = graph.conflicts.get(conflict_id) or graph.correlations.get(conflict_id)
                if conflict_node:
                    if getattr(conflict_node, "node_type", None) == NodeType.CONFLICT:
                        conflict_edges = graph.out_edges.get(conflict_id, [])
                        claim_ids = [e.target_id for e in conflict_edges 
                                     if e.target_type == NodeType.CLAIM and e.relationship == "CONFLICTS_WITH"]
                        for cid in claim_ids:
                            for edge in graph.in_edges.get(cid, []):
                                if edge.source_type == NodeType.OBSERVATION and edge.relationship == "SUPPORTED_BY":
                                    obs_ids.append(edge.source_id)
                    elif getattr(conflict_node, "node_type", None) == NodeType.CORRELATION:
                        corr_edges = graph.out_edges.get(conflict_id, [])
                        obs_ids = [e.target_id for e in corr_edges 
                                   if e.target_type == NodeType.OBSERVATION and e.relationship == "RELATED_TO"]
                for oid in obs_ids:
                    if oid != res.preferred_observation_id:
                        suppressed_obs.add(oid)

        for corr_id, corr in graph.correlations.items():
            if hasattr(corr, "correlation_type") and corr.correlation_type == "DUPLICATES":
                if corr_id not in graph.resolutions_by_conflict:
                    corr_edges = graph.out_edges.get(corr_id, [])
                    obs_ids = [e.target_id for e in corr_edges 
                               if e.target_type == NodeType.OBSERVATION and e.relationship == "RELATED_TO"]
                    if len(obs_ids) >= 2:
                        for oid in obs_ids[1:]:
                            suppressed_obs.add(oid)

        active_obs = [o for o in graph.observations.values() if o.observation_id not in suppressed_obs]

        # 6. Every observation has traceability
        for o in active_obs:
            out_edges = graph.out_edges.get(o.observation_id, [])
            claim_ids = [e.target_id for e in out_edges if e.target_type == NodeType.CLAIM]
            evidence_ids = [e.target_id for e in out_edges if e.target_type == NodeType.EVIDENCE]
            if not claim_ids:
                errors.append(f"Traceability Error: Observation '{o.observation_id}' is not linked to any claim")
            else:
                for cid in claim_ids:
                    if cid not in graph.claims:
                        errors.append(f"Broken Traceability Reference: Observation '{o.observation_id}' references non-existent claim '{cid}'")
            if not evidence_ids:
                errors.append(f"Traceability Error: Observation '{o.observation_id}' is not linked to any evidence")
            else:
                for eid in evidence_ids:
                    if eid not in graph.evidence:
                        errors.append(f"Broken Traceability Reference: Observation '{o.observation_id}' references non-existent evidence '{eid}'")

        # 7. Evidence appendix is complete
        for o in active_obs:
            out_edges = graph.out_edges.get(o.observation_id, [])
            evidence_ids = [e.target_id for e in out_edges if e.target_type == NodeType.EVIDENCE]
            for eid in evidence_ids:
                if eid not in report.evidence_appendix:
                    errors.append(f"Incomplete Evidence Appendix: Evidence '{eid}' is linked in observation but missing from evidence appendix")

        # 8. No orphan references (check references exist in graph)
        for o in active_obs:
            # We check if observation_id is mentioned in any of the analysis/appendix sections
            in_sections = False
            for field in required_fields:
                if o.observation_id in getattr(report, field, ""):
                    in_sections = True
                    break
            if not in_sections:
                warnings.append(f"Orphan observation trace: Observation '{o.observation_id}' is active but not rendered in report sections")

        # 9. Serialization round-trips correctly
        try:
            serialized = report.model_dump_json() if hasattr(report, "model_dump_json") else json.dumps(report_dict, default=str)
            deserialized_dict = json.loads(serialized)
            rebuilt = Report(**deserialized_dict)
            rebuilt_dict = rebuilt.model_dump() if hasattr(rebuilt, "model_dump") else rebuilt.__dict__.copy()
            # Compare key fields to ignore minor dict/list ordering differences
            for k in required_fields + ["report_id", "startup_id", "startup_name", "generated_at", "report_version", "report_hash"]:
                if rebuilt_dict.get(k) != report_dict.get(k):
                    errors.append(f"Serialization Error: Section '{k}' mismatch after round-trip serialization")
        except Exception as e:
            errors.append(f"Serialization Exception: {str(e)}")

        return {"errors": errors, "warnings": warnings}

    @staticmethod
    def validate_and_raise(report: Report, graph: ObservationGraph) -> None:
        result = ReportValidator.validate_report(report, graph)
        if result["errors"]:
            raise ReportValidationError(f"Report validation failed: {'; '.join(result['errors'])}")
