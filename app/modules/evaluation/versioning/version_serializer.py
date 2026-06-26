import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from app.modules.evaluation.versioning.version_models import StartupVersion, VersionSnapshot, DeltaReport


class VersionSerializer:
    """Handles JSON, Markdown, HTML, and PDF-ready serialization/export for Startup Versions and Deltas."""

    @staticmethod
    def to_json(obj: Any) -> str:
        """Serializes any versioning object to a JSON string with deterministic key sorting."""
        if hasattr(obj, "model_dump_json"):
            return obj.model_dump_json()
        elif hasattr(obj, "model_dump"):
            return json.dumps(obj.model_dump(), default=str, sort_keys=True)
        return json.dumps(obj, default=str, sort_keys=True)

    @staticmethod
    def from_json(json_str: str, target_class: Any) -> Any:
        """Deserializes a JSON string into a target Pydantic model class."""
        if hasattr(target_class, "model_validate_json"):
            return target_class.model_validate_json(json_str)
        data = json.loads(json_str)
        return target_class(**data)

    @staticmethod
    def to_markdown(version: StartupVersion, snapshot: VersionSnapshot) -> str:
        """Compiles the startup version snapshot into a structured markdown report."""
        md = f"# Startup Evaluation Version Report: {version.startup_name}\n\n"
        md += f"> [!NOTE]\n"
        md += f"> This is an immutable snapshot of the evaluation graph state for version **{version.version_number}**.\n\n"

        md += "## Version Details\n"
        md += f"- **Version ID**: `{version.version_id}`\n"
        md += f"- **Startup ID**: `{version.startup_id}`\n"
        md += f"- **Startup Name**: {version.startup_name}\n"
        md += f"- **Version Number**: {version.version_number}\n"
        md += f"- **Created At**: {version.created_at.isoformat() if isinstance(version.created_at, datetime) else version.created_at}\n"
        md += f"- **Created By**: {version.created_by}\n"
        md += f"- **Graph Hash**: `{version.graph_hash}`\n"
        md += f"- **Workflow Reference ID**: `{version.workflow_id}`\n"
        md += f"- **Committee Report Reference ID**: `{version.committee_report_id}`\n"
        md += f"- **Investment Assessment ID**: `{version.investment_report_id}`\n"
        md += f"- **Portfolio Snapshot ID**: `{version.portfolio_snapshot_id}`\n\n"

        md += "## Snapshot Summary\n"
        obs_count = len(snapshot.observation_graph.get("observations", {}))
        claims_count = len(snapshot.claims)
        ev_count = len(snapshot.evidence)
        risks_count = len(snapshot.risks)
        qst_count = len(snapshot.questions)
        conf_count = len(snapshot.conflicts)

        md += "| Component | Count | Stored Status |\n"
        md += "| :--- | :--- | :--- |\n"
        md += f"| **Observations** | {obs_count} | Captured |\n"
        md += f"| **Claims** | {claims_count} | Captured |\n"
        md += f"| **Evidence References** | {ev_count} | Captured |\n"
        md += f"| **Identified Risks** | {risks_count} | Captured |\n"
        md += f"| **Due Diligence Questions** | {qst_count} | Captured |\n"
        md += f"| **Factual Conflicts** | {conf_count} | Captured |\n\n"

        if snapshot.committee_report:
            dec = snapshot.committee_report.get("decision", {})
            md += "### Incubation Committee Decision Snapshot\n"
            md += f"- **Incubation Verdict**: `{snapshot.committee_report.get('recommendations', {}).get('recommendation', 'N/A')}`\n"
            md += f"- **Overall Verdict Confidence**: `{dec.get('overall_confidence', 'N/A')}`\n"
            md += f"- **Executive Summary**: {dec.get('overall_reasoning', 'N/A')}\n\n"

        if snapshot.workflow_state:
            md += "### Lifecycle Workflow Snapshot\n"
            md += f"- **Current State**: `{snapshot.workflow_state.get('current_state', 'N/A')}`\n"
            md += f"- **Last Modified By**: `{snapshot.workflow_state.get('last_modified_by', 'N/A')}`\n"
            md += f"- **Updated At**: {snapshot.workflow_state.get('updated_at', 'N/A')}\n"

        return md

    @staticmethod
    def to_html(version: StartupVersion, snapshot: VersionSnapshot) -> str:
        """Renders the version snapshot details into a styled HTML page."""
        md_html = VersionSerializer.to_markdown(version, snapshot)
        # Standard conversion template with styles
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Version Report - {version.startup_name}</title>
    <style>
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            line-height: 1.6;
            color: #1a202c;
            background-color: #f7fafc;
            padding: 40px 20px;
            max-width: 900px;
            margin: 0 auto;
        }}
        .card {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
            border: 1px solid #e2e8f0;
        }}
        h1 {{
            color: #1a365d;
            font-size: 2.25rem;
            margin-top: 0;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 12px;
        }}
        h2 {{
            color: #2b6cb0;
            margin-top: 30px;
            font-size: 1.5rem;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background-color: #ebf8ff;
            color: #2b6cb0;
        }}
        code {{
            background-color: #edf2f7;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9em;
        }}
        .badge {{
            background-color: #3182ce;
            color: white;
            padding: 4px 8px;
            border-radius: 9999px;
            font-size: 0.85em;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Version Report: {version.startup_name}</h1>
        <p><strong>Version Number:</strong> {version.version_number} &nbsp;|&nbsp; <strong>Date:</strong> {version.created_at.isoformat() if isinstance(version.created_at, datetime) else version.created_at}</p>
        <hr/>
        <h2>Version Metadata</h2>
        <ul>
            <li><strong>Version ID:</strong> <code>{version.version_id}</code></li>
            <li><strong>Graph Hash Reference:</strong> <code>{version.graph_hash}</code></li>
            <li><strong>Created By Actor:</strong> <code>{version.created_by}</code></li>
            <li><strong>Workflow Reference:</strong> <code>{version.workflow_id}</code></li>
            <li><strong>Committee Report Reference:</strong> <code>{version.committee_report_id}</code></li>
            <li><strong>Investment Assessment Reference:</strong> <code>{version.investment_report_id}</code></li>
            <li><strong>Portfolio Snapshot Reference:</strong> <code>{version.portfolio_snapshot_id}</code></li>
        </ul>
        
        <h2>Snapshot statistics</h2>
        <table>
            <thead>
                <tr>
                    <th>Component</th>
                    <th>Count</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Observations</td>
                    <td>{len(snapshot.observation_graph.get("observations", {}))}</td>
                    <td><span class="badge">Stored</span></td>
                </tr>
                <tr>
                    <td>Claims</td>
                    <td>{len(snapshot.claims)}</td>
                    <td><span class="badge">Stored</span></td>
                </tr>
                <tr>
                    <td>Evidence Snippets</td>
                    <td>{len(snapshot.evidence)}</td>
                    <td><span class="badge">Stored</span></td>
                </tr>
                <tr>
                    <td>Active Risks</td>
                    <td>{len(snapshot.risks)}</td>
                    <td><span class="badge">Stored</span></td>
                </tr>
                <tr>
                    <td>Due Diligence Questions</td>
                    <td>{len(snapshot.questions)}</td>
                    <td><span class="badge">Stored</span></td>
                </tr>
                <tr>
                    <td>Factual Conflicts</td>
                    <td>{len(snapshot.conflicts)}</td>
                    <td><span class="badge">Stored</span></td>
                </tr>
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        return html

    @staticmethod
    def delta_to_markdown(report: DeltaReport) -> str:
        """Formats the delta report comparison results into a structured markdown document."""
        md = f"# Version Delta Intelligence Report: V{report.from_version} &rarr; V{report.to_version}\n\n"
        md += f"- **Delta Report ID**: `{report.delta_id}`\n"
        md += f"- **From Version**: V{report.from_version}\n"
        md += f"- **To Version**: V{report.to_version}\n"
        md += f"- **Overall Change Confidence**: `{report.overall_change_confidence:.4f}`\n"
        md += f"- **Generated At**: {report.generated_at.isoformat() if isinstance(report.generated_at, datetime) else report.generated_at}\n\n"

        md += "## Executive Summary of Changes\n"
        md += f"{report.summary}\n\n"

        md += "## Summary of Changed Fields\n"
        if report.changed_fields:
            for f in report.changed_fields:
                md += f"- `{f}`\n"
            md += "\n"
        else:
            md += "*No changes detected.*\n\n"

        def format_items(items: List[Any], name: str):
            nonlocal md
            md += f"### {name} Items ({len(items)})\n"
            if not items:
                md += "*None.*\n\n"
                return
            md += "| Category | Field | Previous Value | Current Value | Confidence | Reasoning |\n"
            md += "| :--- | :--- | :--- | :--- | :--- | :--- |\n"
            for item in items:
                prev = str(item.previous_value) if item.previous_value is not None else "-"
                curr = str(item.current_value) if item.current_value is not None else "-"
                md += f"| {item.category} | {item.field} | {prev} | {curr} | {item.confidence:.2f} | {item.reasoning} |\n"
            md += "\n"

        format_items(report.added_items, "Added")
        format_items(report.removed_items, "Removed")
        format_items(report.modified_items, "Modified")

        return md

    @staticmethod
    def delta_to_html(report: DeltaReport) -> str:
        """Renders the Delta Report changes into a styled, responsive HTML comparison layout."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Delta Report - V{report.from_version} to V{report.to_version}</title>
    <style>
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            line-height: 1.6;
            color: #2d3748;
            background-color: #f7fafc;
            padding: 40px 20px;
            max-width: 1000px;
            margin: 0 auto;
        }}
        .card {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
            border: 1px solid #e2e8f0;
        }}
        h1 {{
            color: #1a365d;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 12px;
            margin-top: 0;
        }}
        h2 {{
            color: #2b6cb0;
            margin-top: 30px;
        }}
        .summary {{
            background-color: #ebf8ff;
            border-left: 4px solid #3182ce;
            padding: 15px;
            border-radius: 0 8px 8px 0;
            margin: 20px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.95rem;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        th {{
            background-color: #edf2f7;
            color: #4a5568;
        }}
        .badge-add {{ background-color: #c6f6d5; color: #22543d; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }}
        .badge-rem {{ background-color: #fed7d7; color: #742a2a; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }}
        .badge-mod {{ background-color: #feebc8; color: #744210; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Delta Comparison Report</h1>
        <p><strong>Delta ID:</strong> <code>{report.delta_id}</code> &nbsp;|&nbsp; <strong>Comparing:</strong> V{report.from_version} &rarr; V{report.to_version} &nbsp;|&nbsp; <strong>Overall Confidence:</strong> {report.overall_change_confidence:.4f}</p>
        
        <div class="summary">
            <h3>Executive Summary</h3>
            <p>{report.summary}</p>
        </div>

        <h2>Detected Changes Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Type</th>
                    <th>Category</th>
                    <th>Field / Item</th>
                    <th>Previous Value</th>
                    <th>Current Value</th>
                    <th>Confidence</th>
                    <th>Reasoning</th>
                </tr>
            </thead>
            <tbody>
        """
        
        def write_rows(items, badge_class, label):
            nonlocal html
            for item in items:
                prev = str(item.previous_value) if item.previous_value is not None else "-"
                curr = str(item.current_value) if item.current_value is not None else "-"
                html += f"""
                <tr>
                    <td><span class="{badge_class}">{label}</span></td>
                    <td>{item.category}</td>
                    <td>{item.field}</td>
                    <td>{prev}</td>
                    <td>{curr}</td>
                    <td>{item.confidence:.2f}</td>
                    <td>{item.reasoning}</td>
                </tr>"""

        write_rows(report.added_items, "badge-add", "ADDED")
        write_rows(report.removed_items, "badge-rem", "REMOVED")
        write_rows(report.modified_items, "badge-mod", "MODIFIED")
        
        if not report.added_items and not report.removed_items and not report.modified_items:
            html += """<tr><td colspan="7" style="text-align: center; color: #a0aec0;">No changes detected between these two versions.</td></tr>"""

        html += """
            </tbody>
        </table>
    </div>
</body>
</html>"""
        return html

    @staticmethod
    def export_version(version: StartupVersion, snapshot: VersionSnapshot, format: str) -> Any:
        """Exposes the public endpoint for exporting version snaps in JSON, MD, HTML, or PDF-ready formats."""
        if format.lower() == "json":
            return VersionSerializer.to_json({"version": version, "snapshot": snapshot})
        elif format.lower() == "markdown":
            return VersionSerializer.to_markdown(version, snapshot)
        elif format.lower() == "html":
            return VersionSerializer.to_html(version, snapshot)
        elif format.lower() == "pdf":
            # PDF-ready dictionary structured format
            return {
                "version": version.model_dump(),
                "snapshot": snapshot.model_dump()
            }
        raise ValueError(f"Unsupported format '{format}'. Supported: JSON, Markdown, HTML, PDF")
