MARKDOWN_TEMPLATE = """# Incubation Committee Report: {startup_name}
*   **Report ID:** `{decision_id}`
*   **Startup ID:** `{startup_id}`
*   **Workflow Ref:** `{workflow_reference}`
*   **Generated At:** {created_at}
*   **Overall Confidence:** {overall_confidence:.2f}

## Executive Summary & Recommendation
*   **Verdict Recommendation:** **{recommendation}** *(Priority: {priority})*
*   **Justification:** {justification}
*   **Overall Reasoning details:** {overall_reasoning}

## Findings & Corroborations
{findings_content}

## Risks & Concerns
{concerns_content}

## Consensus & Conflict Auditing
*   **Consensus Agreement Level:** {agreement_level:.2f}
*   **Corroborated Findings Count:** {corroborated_count}
*   **Contradictions Count:** {contradictions_count}
*   **Unresolved Conflicts Count:** {unresolved_conflicts_count}

### Cross-Domain Dependencies
{dependencies_content}

### Required Follow-ups
{followups_content}

### Required Documents
{documents_content}
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Committee Report - {startup_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #333;
            background-color: #f4f6f8;
            margin: 0;
            padding: 40px;
        }}
        .report-container {{
            background: #fff;
            max-width: 900px;
            margin: 0 auto;
            border-radius: 8px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.06);
            padding: 40px;
        }}
        h1 {{
            color: #1a73e8;
            margin-top: 0;
            border-bottom: 2px solid #e8eaed;
            padding-bottom: 12px;
            font-size: 26px;
        }}
        h2 {{
            color: #202124;
            border-bottom: 1px solid #e8eaed;
            padding-bottom: 8px;
            margin-top: 30px;
            font-size: 18px;
        }}
        .meta-list {{
            background: #f8f9fa;
            border-radius: 6px;
            padding: 16px 20px;
            font-size: 14px;
            list-style: none;
            margin: 0 0 24px 0;
        }}
        .meta-list li {{
            margin-bottom: 8px;
        }}
        .meta-list li:last-child {{
            margin-bottom: 0;
        }}
        .badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        .badge-priority {{
            background-color: #fce8e6;
            color: #c5221f;
        }}
        .badge-recommendation {{
            background-color: #e8f0fe;
            color: #1a73e8;
            font-size: 15px;
            padding: 6px 12px;
        }}
        .list-item {{
            margin-bottom: 12px;
            font-size: 14px;
            line-height: 1.5;
        }}
        .trace-label {{
            font-family: monospace;
            background-color: #f1f3f4;
            padding: 2px 6px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <h1>Incubation Committee Decision Report</h1>
        <ul class="meta-list">
            <li><strong>Startup Name:</strong> {startup_name}</li>
            <li><strong>Report ID:</strong> <span class="trace-label">{decision_id}</span></li>
            <li><strong>Startup ID:</strong> <span class="trace-label">{startup_id}</span></li>
            <li><strong>Workflow Reference:</strong> <span class="trace-label">{workflow_reference}</span></li>
            <li><strong>Overall Confidence:</strong> {overall_confidence:.2f}</li>
        </ul>

        <h2>1. Recommendation Verdict</h2>
        <p><span class="badge badge-recommendation">{recommendation}</span> &nbsp; <span class="badge badge-priority">Priority: {priority}</span></p>
        <p><strong>Justification:</strong> {justification}</p>
        <p><strong>Reasoning:</strong> {overall_reasoning}</p>

        <h2>2. Aggregated Findings</h2>
        {findings_html}

        <h2>3. Risks & Gaps</h2>
        {concerns_html}

        <h2>4. Consensus Auditing</h2>
        <ul class="meta-list" style="background-color: #fdf7e2;">
            <li><strong>Agreement Level:</strong> {agreement_level:.2f}</li>
            <li><strong>Corroborated Findings:</strong> {corroborated_count}</li>
            <li><strong>Contradictions:</strong> {contradictions_count}</li>
            <li><strong>Unresolved Conflicts:</strong> {unresolved_conflicts_count}</li>
        </ul>

        <h2>5. Follow-up & Documentation Actions</h2>
        <p><strong>Required Documents:</strong></p>
        <ul>
            {documents_html}
        </ul>
        <p><strong>Required Follow-up Questions:</strong></p>
        <ul>
            {followups_html}
        </ul>
    </div>
</body>
</html>
"""
