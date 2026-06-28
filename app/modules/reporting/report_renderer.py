from abc import ABC, abstractmethod
import json
from typing import Any
from app.modules.reporting.report_models import Report, DueDiligenceReport


class ReportRenderer(ABC):
    """Abstract base class for report format renderers."""

    @abstractmethod
    def render(self, report: Any) -> Any:
        """Render the given report model into a specific target format."""
        pass


class MarkdownRenderer(ReportRenderer):
    """Compiles all sections of a Report or DueDiligenceReport into a single well-formatted Markdown document."""

    def render(self, report: Any) -> str:
        if isinstance(report, DueDiligenceReport):
            return self._render_due_diligence(report)
        elif isinstance(report, Report):
            return self._render_legacy(report)
        else:
            # Fallback/Duck typing
            if hasattr(report, "founder_assessment"):
                return self._render_due_diligence(report)
            return self._render_legacy(report)

    def _render_due_diligence(self, report: DueDiligenceReport) -> str:
        parts = [
            report.executive_summary,
            "",
            "## Investment Summary",
            f"*   **Investment Readiness**: {report.investment_summary.investment_readiness}",
            f"*   **Grant Readiness**: {report.investment_summary.grant_readiness}",
            f"*   **VC Readiness**: {report.investment_summary.vc_readiness}",
            f"*   **Technology Readiness Level (TRL)**: {report.investment_summary.trl}",
            f"*   **Portfolio Rank**: {report.investment_summary.portfolio_rank if report.investment_summary.portfolio_rank is not None else 'Not Ranked'}",
            f"*   **Recommendation**: {report.investment_summary.recommendation}",
            "",
            "## Risk Matrix",
            "| Risk Category | Severity | Confidence | Primary Evidence | Mitigations / Recommendations |",
            "| --- | --- | --- | --- | --- |",
        ]
        
        for cat in ["technical", "execution", "market", "competition", "financial", "regulatory", "ip"]:
            item = getattr(report.risk_matrix, cat)
            evidence_str = ", ".join(item.evidence) if item.evidence else "N/A"
            parts.append(f"| **{cat.capitalize()}** | {item.severity} | {item.confidence:.2f} | {evidence_str} | {item.recommendation} |")

        domains = [
            ("founder", "Founder & Team"),
            ("product", "Product & Technology"),
            ("market", "Market & Customer"),
            ("competition", "Competitor & Defensibility"),
            ("trl", "Technology Readiness Level"),
            ("financial", "Financial Runway"),
            ("ip", "Intellectual Property"),
            ("risk", "Risk Exposure"),
            ("investment", "Investment Assessment")
        ]

        for field_name, title in domains:
            sect = getattr(report, f"{field_name}_assessment")
            sect_parts = [
                "",
                f"## {title} Assessment",
                sect.summary,
                "",
                f"*   **Confidence**: {sect.confidence:.2f}",
                "",
                "### Key Observations"
            ]
            if sect.observations:
                for o in sect.observations:
                    sect_parts.append(f"*   **[{o.get('id', 'N/A')}]** {o.get('text')} *(Confidence: {o.get('confidence', 1.0):.2f})*")
            else:
                sect_parts.append("*   No observations recorded.")

            sect_parts.append("\n### Supporting Evidence")
            if sect.supporting_evidence:
                for ev in sect.supporting_evidence:
                    sect_parts.append(f"*   **[{ev.get('id', 'N/A')}]** {ev.get('excerpt')} *(Location: {ev.get('location')})*")
            else:
                sect_parts.append("*   No supporting evidence recorded.")

            sect_parts.append("\n### Key Strengths")
            if sect.strengths:
                for s in sect.strengths:
                    sect_parts.append(f"*   {s}")
            else:
                sect_parts.append("*   None recorded.")

            sect_parts.append("\n### Key Weaknesses")
            if sect.weaknesses:
                for w in sect.weaknesses:
                    sect_parts.append(f"*   {w}")
            else:
                sect_parts.append("*   None recorded.")

            sect_parts.append("\n### Recommendations")
            if sect.recommendations:
                for r in sect.recommendations:
                    sect_parts.append(f"*   {r}")
            else:
                sect_parts.append("*   None recorded.")

            sect_parts.append("\n### Open Questions")
            if sect.open_questions:
                for q in sect.open_questions:
                    sect_parts.append(f"*   {q}")
            else:
                sect_parts.append("*   None recorded.")

            parts.append("\n".join(sect_parts))

        parts.append("")
        parts.append(report.appendix)
        return "\n\n".join(parts)

    def _render_legacy(self, report: Report) -> str:
        parts = [
            f"# Due Diligence Report: {report.startup_name}",
            f"**Report ID:** `{report.report_id}`",
            f"**Startup ID:** `{report.startup_id}`",
            f"**Generated At:** {report.generated_at}",
            f"**Generated By:** {report.generated_by}",
            f"**Version:** {report.report_version}",
            f"**Integrity Hash:** `{report.report_hash}`",
            "",
            report.executive_summary,
            "",
            report.founder_analysis,
            "",
            report.product_analysis,
            "",
            report.market_analysis,
            "",
            report.competition_analysis,
            "",
            report.financial_analysis,
            "",
            report.trl_analysis,
            "",
            report.ip_analysis,
            "",
            report.risk_analysis,
            "",
            report.committee_decision,
            "",
            report.investment_recommendation,
            "",
            report.portfolio_position,
            "",
            report.explainability_appendix,
            "",
            report.evidence_appendix
        ]
        return "\n\n".join(parts)


class HTMLRenderer(ReportRenderer):
    """Converts the Report or DueDiligenceReport into a modern, responsive HTML page layout."""

    def render(self, report: Any) -> str:
        # Create a clean Markdown compilation first
        md_content = MarkdownRenderer().render(report)
        
        # Simple markdown to HTML converter
        html_lines = []
        in_list = False
        in_table = False
        
        for line in md_content.splitlines():
            line_stripped = line.strip()
            if not line_stripped:
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                if in_table:
                    html_lines.append("</tbody></table>")
                    in_table = False
                html_lines.append("<br/>")
                continue
                
            if line_stripped.startswith("# "):
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append(f"<h1>{line_stripped[2:]}</h1>")
            elif line_stripped.startswith("## "):
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append(f"<h2>{line_stripped[3:]}</h2>")
            elif line_stripped.startswith("### "):
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append(f"<h3>{line_stripped[4:]}</h3>")
            elif line_stripped.startswith("* ") or line_stripped.startswith("*   "):
                if not in_list:
                    html_lines.append("<ul>")
                    in_list = True
                content = line_stripped[4:] if line_stripped.startswith("*   ") else line_stripped[2:]
                html_lines.append(f"<li>{content}</li>")
            elif line_stripped.startswith("|"):
                if not in_table:
                    html_lines.append("<table border='1' style='border-collapse: collapse; width: 100%; margin: 10px 0;'>")
                    in_table = True
                    # Render header
                    cols = [c.strip() for c in line_stripped.split("|")[1:-1]]
                    html_lines.append("<thead><tr>" + "".join(f"<th>{c}</th>" for c in cols) + "</tr></thead><tbody>")
                else:
                    if "---" in line_stripped:
                        continue
                    cols = [c.strip() for c in line_stripped.split("|")[1:-1]]
                    html_lines.append("<tr>" + "".join(f"<td>{c}</td>" for c in cols) + "</tr>")
            else:
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                html_lines.append(f"<p>{line_stripped}</p>")
                
        if in_list:
            html_lines.append("</ul>")
        if in_table:
            html_lines.append("</tbody></table>")

        body_content = "\n".join(html_lines)
        
        # modern glassmorphism styled template
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Due Diligence Report - {report.startup_name}</title>
    <style>
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            color: #f1f5f9;
            margin: 0;
            padding: 40px 20px;
            display: flex;
            justify-content: center;
        }}
        .container {{
            max-width: 900px;
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}
        h1 {{
            color: #38bdf8;
            font-size: 2.5em;
            margin-bottom: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.15);
            padding-bottom: 10px;
        }}
        h2 {{
            color: #818cf8;
            font-size: 1.8em;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        h3 {{
            color: #fb7185;
            font-size: 1.3em;
            margin-top: 20px;
        }}
        p, li {{
            line-height: 1.6;
            color: #cbd5e1;
        }}
        ul {{
            padding-left: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: rgba(15, 23, 42, 0.4);
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        th {{
            background-color: rgba(99, 102, 241, 0.2);
            color: #818cf8;
        }}
        tr:hover {{
            background: rgba(255,255,255,0.02);
        }}
    </style>
</head>
<body>
    <div class="container">
        {body_content}
    </div>
</body>
</html>"""


class JSONRenderer(ReportRenderer):
    """Serializes the Report or DueDiligenceReport model into a structured JSON string."""

    def render(self, report: Any) -> str:
        if hasattr(report, "model_dump_json"):
            return report.model_dump_json(indent=2)
        return json.dumps(report.__dict__, indent=2, default=str)
