import json
from datetime import datetime
from typing import Any, List
from app.modules.workflow.workflow_models import Workflow, WorkflowHistoryEntry


class WorkflowSerializer:
    """Handles deterministic serialization and export formatting for Workflow entities."""

    @staticmethod
    def to_json(workflow: Workflow, history: List[WorkflowHistoryEntry]) -> str:
        """Serialize workflow and history into a deterministic JSON string."""
        def default_serializer(obj: Any) -> Any:
            if isinstance(obj, datetime):
                if obj.tzinfo is not None:
                    from datetime import timezone
                    obj = obj.astimezone(timezone.utc).replace(tzinfo=None)
                return obj.isoformat() + "Z"
            return str(obj)

        data = {
            "workflow": workflow.model_dump(),
            "history": [entry.model_dump() for entry in history]
        }
        return json.dumps(data, sort_keys=True, indent=2, default=default_serializer)

    @staticmethod
    def from_json(json_str: str) -> tuple[Workflow, List[WorkflowHistoryEntry]]:
        """Deserialize json string back to Workflow and history list."""
        data = json.loads(json_str)
        workflow_data = data["workflow"]
        history_data = data.get("history", [])

        # Parse datetimes
        for key in ["created_at", "updated_at"]:
            if workflow_data.get(key):
                if isinstance(workflow_data[key], str):
                    # Strip Z suffix if present to parse with fromisoformat
                    val = workflow_data[key].replace("Z", "+00:00")
                    workflow_data[key] = datetime.fromisoformat(val)

        history_entries = []
        for h in history_data:
            if h.get("timestamp") and isinstance(h["timestamp"], str):
                val = h["timestamp"].replace("Z", "+00:00")
                h["timestamp"] = datetime.fromisoformat(val)
            history_entries.append(WorkflowHistoryEntry(**h))

        return Workflow(**workflow_data), history_entries

    @staticmethod
    def export_markdown(workflow: Workflow, history: List[WorkflowHistoryEntry]) -> str:
        """Export workflow status and history to markdown format."""
        lines = [
            f"# Startup Workflow Lifecycle: {workflow.startup_name}",
            f"*   **Workflow ID:** `{workflow.workflow_id}`",
            f"*   **Startup ID:** `{workflow.startup_id}`",
            f"*   **Current State:** `{workflow.current_state}`",
            f"*   **Previous State:** `{workflow.previous_state or 'N/A'}`",
            f"*   **Version:** `{workflow.workflow_version}`",
            f"*   **Hash:** `{workflow.workflow_hash}`",
            f"*   **Created At:** {workflow.created_at.isoformat()}Z",
            f"*   **Updated At:** {workflow.updated_at.isoformat()}Z",
            "",
            "## Workflow History"
        ]

        if not history:
            lines.append("No transition history recorded.")
        else:
            for idx, entry in enumerate(history, 1):
                lines.extend([
                    f"### {idx}. Transition: {entry.previous_state or 'Initial'} → {entry.new_state}",
                    f"*   **Actor:** {entry.actor} ({entry.role})",
                    f"*   **Timestamp:** {entry.timestamp.isoformat()}Z",
                    f"*   **Reason/Justification:** {entry.reason}",
                    f"*   **Audit Ref:** `{entry.audit_reference}`",
                    ""
                ])

        return "\n".join(lines)

    @staticmethod
    def export_html(workflow: Workflow, history: List[WorkflowHistoryEntry]) -> str:
        """Export workflow status and history to structured HTML with premium styling."""
        history_rows = ""
        for idx, entry in enumerate(history, 1):
            history_rows += f"""
            <tr class="history-row">
                <td class="history-cell">{idx}</td>
                <td class="history-cell"><span class="badge badge-prev">{entry.previous_state or 'None'}</span> &rarr; <span class="badge badge-new">{entry.new_state}</span></td>
                <td class="history-cell"><strong>{entry.actor}</strong> ({entry.role})</td>
                <td class="history-cell">{entry.timestamp.isoformat()}Z</td>
                <td class="history-cell">{entry.reason}</td>
            </tr>
            """

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Workflow - {workflow.startup_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #333;
            background-color: #f7f9fa;
            margin: 0;
            padding: 40px;
        }}
        .card {{
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            max-width: 1000px;
            margin: 0 auto;
            padding: 30px;
        }}
        h1 {{
            color: #1a73e8;
            margin-top: 0;
            font-size: 24px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 30px;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
        }}
        .grid-item {{
            font-size: 14px;
        }}
        .grid-label {{
            color: #666;
            font-weight: 600;
            margin-bottom: 4px;
        }}
        .grid-value {{
            font-family: monospace;
            background: #eef1f2;
            padding: 2px 6px;
            border-radius: 4px;
        }}
        .badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        .badge-prev {{
            background-color: #e8eaed;
            color: #5f6368;
        }}
        .badge-new {{
            background-color: #e6f4ea;
            color: #137333;
        }}
        .badge-current {{
            background-color: #e8f0fe;
            color: #1a73e8;
            font-size: 14px;
            padding: 6px 12px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            text-align: left;
            padding: 12px;
            border-bottom: 2px solid #ddd;
            color: #555;
            font-size: 14px;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Workflow Lifecycle: {workflow.startup_name}</h1>
        <div class="grid">
            <div class="grid-item">
                <div class="grid-label">Workflow ID</div>
                <div class="grid-value">{workflow.workflow_id}</div>
            </div>
            <div class="grid-item">
                <div class="grid-label">Current State</div>
                <div><span class="badge badge-current">{workflow.current_state}</span></div>
            </div>
            <div class="grid-item">
                <div class="grid-label">Startup ID</div>
                <div class="grid-value">{workflow.startup_id}</div>
            </div>
            <div class="grid-item">
                <div class="grid-label">Updated At</div>
                <div>{workflow.updated_at.isoformat()}Z</div>
            </div>
        </div>

        <h2>Workflow History Trail</h2>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Transition States</th>
                    <th>Actor (Role)</th>
                    <th>Timestamp</th>
                    <th>Justification</th>
                </tr>
            </thead>
            <tbody>
                {history_rows or "<tr><td colspan='5'>No transitions logged yet.</td></tr>"}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        return html
