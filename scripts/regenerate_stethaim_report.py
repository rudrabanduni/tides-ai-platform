"""
Regenerate STETHAIM Due Diligence Report Locally (Zero Live API Calls)

Fixes:
1. Eliminates cross-startup energy/battery contamination in executive summary and investment recommendation.
2. Aligns supervisory review recommendation to CONDITIONAL to match its non-contradictory rationale.
3. Surfaces multi-body governance reconciliation across Supervisory (CONDITIONAL), Investment (WATCH), and Committee (SEEK_MORE_INFORMATION).
4. Generates a fresh Report ID and validates with ReportValidator.
5. Preserves REPORT-BBD93B93.json and historical metadata/cost telemetry untouched.
"""
import os
import sys
import json
import hashlib
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app.modules.evaluation.graph.graph_serializer import from_json, to_json
from app.modules.evaluation.report.report_engine import DueDiligenceReportEngine
from app.modules.evaluation.report.report_validator import ReportValidator


def get_file_hash(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    graph_path = REPO_ROOT / "uploads" / "graphs" / "a246f3a5-b797-43fc-9dc3-3e603e3b37b9.json"
    older_artifact_path = REPO_ROOT / "uploads" / "graphs" / "REPORT-BBD93B93.json"
    metadata_path = REPO_ROOT / "uploads" / "graphs" / "a246f3a5-b797-43fc-9dc3-3e603e3b37b9.metadata.json"

    if not graph_path.exists():
        print(f"Error: Target graph not found at {graph_path}", file=sys.stderr)
        sys.exit(1)

    # 1. Record pre-hashes to guarantee artifact preservation
    older_hash_pre = get_file_hash(older_artifact_path) if older_artifact_path.exists() else None
    meta_hash_pre = get_file_hash(metadata_path) if metadata_path.exists() else None

    # 2. Load target STETHAIM graph
    print(f"Loading target graph from {graph_path}...")
    with open(graph_path, "r", encoding="utf-8") as f:
        graph_data = json.load(f)

    old_report_id = graph_data.get("report", {}).get("report_id") if graph_data.get("report") else None
    print(f"Original Report ID: {old_report_id}")

    graph = from_json(json.dumps(graph_data))

    # 3. Resolve supervisory recommendation inconsistency:
    # Rationale states: "A full DEFER is not warranted because no contradictions were found,
    # so milestone-gated conditions are the proportionate response." -> Align to CONDITIONAL
    if isinstance(graph.supervisory_review, dict):
        graph.supervisory_review["overall_recommendation"] = "CONDITIONAL"
    elif graph.supervisory_review:
        graph.supervisory_review.overall_recommendation = "CONDITIONAL"

    # Align stale final_review recommendation to CONDITIONAL
    if isinstance(getattr(graph, "final_review", None), dict):
        graph.final_review["overall_recommendation"] = "CONDITIONAL"
    elif getattr(graph, "final_review", None):
        graph.final_review.overall_recommendation = "CONDITIONAL"

    # 4. Generate clean report locally (zero LLM / external calls)
    print("Regenerating clean due diligence report locally...")
    graph = DueDiligenceReportEngine.generate(graph)

    new_report_id = graph.report.report_id
    print(f"Regenerated Report ID: {new_report_id}")
    assert new_report_id != old_report_id, f"Report ID should be freshly generated (got {new_report_id})"
    assert new_report_id != "REPORT-BBD93B93", "Report ID must not overwrite or match older artifact REPORT-BBD93B93"

    # 5. Run full report validation including cross-contamination check
    print("Running ReportValidator on regenerated graph...")
    errors = ReportValidator.validate(graph)
    if errors:
        print("Validation FAILED with errors:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)
    print("ReportValidator: 0 errors detected. Full integrity confirmed.")

    # 6. Save updated graph
    serialized = to_json(graph)
    with open(graph_path, "w", encoding="utf-8") as f:
        f.write(serialized)
    print(f"Saved updated graph to {graph_path}")

    # 7. Verify older artifact and metadata preservation
    if older_artifact_path.exists():
        older_hash_post = get_file_hash(older_artifact_path)
        assert older_hash_pre == older_hash_post, "REPORT-BBD93B93.json was modified!"
        print("Older artifact REPORT-BBD93B93.json verified intact.")

    if metadata_path.exists():
        meta_hash_post = get_file_hash(metadata_path)
        assert meta_hash_pre == meta_hash_post, "Metadata telemetry file was modified!"
        print("Historical metadata & cost observability verified intact.")

    print("\n=== REGENERATED EXECUTIVE SUMMARY ===")
    print(graph.report.executive_summary.content)

    print("\n=== REGENERATED INVESTMENT RECOMMENDATION ===")
    print(graph.report.investment_recommendation.content[:1500])

    print("\nSTETHAIM report regeneration completed successfully.")


if __name__ == "__main__":
    main()
