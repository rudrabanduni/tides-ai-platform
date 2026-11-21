import json
import re
import io
from typing import Dict, Any, Optional
from app.modules.evaluation.graph.graph_models import ObservationGraph
from app.modules.evaluation.graph.graph_serializer import to_json as graph_to_json, from_json as graph_from_json
from app.modules.evaluation.report.report_models import DueDiligenceReport, ReportSection, Appendix


class ReportSerializer:
    """Handles JSON serialization, deserialization, and exporting reports to Markdown, HTML, and PDF formats."""

    @staticmethod
    def to_json(graph: ObservationGraph) -> str:
        """Serializes the entire ObservationGraph, including report components, to JSON."""
        return graph_to_json(graph)

    @staticmethod
    def from_json(json_str: str) -> ObservationGraph:
        """Reconstructs the ObservationGraph, including report components, from JSON."""
        return graph_from_json(json_str)

    @staticmethod
    def export_markdown(report: DueDiligenceReport) -> str:
        """Formats the report as a clean, structured Markdown document."""
        md = []
        md.append(f"# Due Diligence Report: {report.report_id}")
        md.append(f"**Generated At:** {report.generated_at}")
        md.append(f"**Graph Version:** {report.graph_version}\n")
        md.append("---")

        sections = [
            report.executive_summary,
            report.investment_recommendation,
            report.founder_assessment,
            report.product_technology,
            report.market_opportunity,
            report.business_model,
            report.competition,
            report.financial_overview,
            report.risks,
            report.investment_thesis,
            report.follow_up_questions
        ]

        for idx, sec in enumerate(sections, 1):
            md.append(f"\n## {idx}. {sec.title}")
            md.append(f"*Confidence: {sec.confidence:.2f}*  \n")
            md.append(sec.content)

        final_review = getattr(report, "final_review", None) or (report.metadata.get("final_review") if hasattr(report, "metadata") and isinstance(report.metadata, dict) else None)
        if final_review:
            fr = final_review.model_dump() if hasattr(final_review, "model_dump") else (final_review if isinstance(final_review, dict) else {})
            if fr:
                md.append("\n---")
                md.append("\n# Final Supervisory AI Review & Due Diligence Synthesis")
                md.append(f"**Overall Recommendation:** `{fr.get('overall_recommendation', 'CONDITIONAL')}`")
                if fr.get("investment_score") is not None:
                    md.append(f"**Investment Viability Score:** {fr.get('investment_score')}/100")
                if fr.get("recommendation_rationale"):
                    md.append(f"**Supervisory Rationale:** {fr.get('recommendation_rationale')}\n")
                if fr.get("cross_domain_findings"):
                    md.append("### Cross-Domain Synthesis Findings")
                    for finding in fr.get("cross_domain_findings", []):
                        md.append(f"- {finding}")
                if fr.get("identified_contradictions"):
                    md.append("\n### Cross-Domain Contradictions")
                    for c in fr.get("identified_contradictions", []):
                        c_dict = c if isinstance(c, dict) else (c.__dict__ if hasattr(c, "__dict__") else {})
                        md.append(f"- **[{c_dict.get('nature_of_conflict', 'CONFLICT')}]** {c_dict.get('domain_a')}.{c_dict.get('criterion_a')} vs {c_dict.get('domain_b')}.{c_dict.get('criterion_b')}: {c_dict.get('resolution_status')}")
                if fr.get("incubation_conditions"):
                    md.append("\n### Institutional Incubation Conditions")
                    for cond in fr.get("incubation_conditions", []):
                        md.append(f"- [ ] {cond}")
                if fr.get("external_research_sources"):
                    md.append("\n### External Independent Research Sources")
                    for src in fr.get("external_research_sources", []):
                        is_mock = src.get("is_mock") or src.get("provenance") in ("MOCK_SIMULATED_RESEARCH", "MOCK") or "SIMULATED" in str(src.get("verification_grade", ""))
                        url_part = f"[{src.get('title', 'Source')}]({src.get('url', '#')})"
                        grade = src.get('verification_grade', 'RETRIEVED_SEARCH_RESULT')
                        auth = src.get('source_authority', 'GENERAL_WEB')
                        supp = src.get('support_status', 'RETRIEVED_CONTEXT')
                        lim = src.get('verification_limitations')
                        lim_part = f" | Limitations: {lim}" if lim else ""
                        if is_mock:
                            md.append(f"- **[SIMULATED MOCK EVIDENCE | {src.get('source_domain', 'web')} - {auth}]** {url_part} - *[MOCK / TEST EVIDENCE - NOT A LIVE SEARCH RESULT]* - *Grade: {grade}* [Support: {supp}] (Simulated Date: {src.get('publication_date') or 'N/A'}): {src.get('summary', '')}{lim_part}")
                        else:
                            md.append(f"- **[LIVE RESEARCH | {src.get('source_domain', 'web')} - {auth}]** {url_part} - *Grade: {grade}* [Support: {supp}] (Published: {src.get('publication_date') or 'N/A'}): {src.get('summary', '')}{lim_part}")

        if report.appendices:
            md.append("\n---")
            md.append("\n# Appendices")
            for app in report.appendices:
                md.append(f"\n## {app.title}")
                md.append(app.content)

        return "\n".join(md)

    @staticmethod
    def export_html(report: DueDiligenceReport) -> str:
        """Generates a premium styled, responsive HTML layout of the report."""
        sections = [
            report.executive_summary,
            report.investment_recommendation,
            report.founder_assessment,
            report.product_technology,
            report.market_opportunity,
            report.business_model,
            report.competition,
            report.financial_overview,
            report.risks,
            report.investment_thesis,
            report.follow_up_questions
        ]

        # Form the table of contents and content sections
        toc_items = []
        content_items = []

        for idx, sec in enumerate(sections, 1):
            anchor = sec.section_id
            toc_items.append(f'<li><a href="#{anchor}">{idx}. {sec.title}</a></li>')
            
            # Simple markdown content formatter
            formatted_content = sec.content
            formatted_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted_content)
            formatted_content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', formatted_content)
            formatted_content = formatted_content.replace('\n', '<br>')
            
            content_items.append(f"""
            <section id="{anchor}" class="report-section">
                <h2>{idx}. {sec.title}</h2>
                <div class="meta">Confidence: <span class="badge badge-conf">{sec.confidence:.2f}</span></div>
                <div class="content">{formatted_content}</div>
            </section>
            """)

        final_review = getattr(report, "final_review", None) or (report.metadata.get("final_review") if hasattr(report, "metadata") and isinstance(report.metadata, dict) else None)
        if final_review:
            fr = final_review.model_dump() if hasattr(final_review, "model_dump") else (final_review if isinstance(final_review, dict) else {})
            if fr:
                toc_items.append('<li><a href="#supervisory_review">Final Supervisory AI Review</a></li>')
                conditions_html = "".join(f"<li>{c}</li>" for c in fr.get("incubation_conditions", []))
                findings_html = "".join(f"<li>{f}</li>" for f in fr.get("cross_domain_findings", []))
                ext_sources_html = ""
                if fr.get("external_research_sources"):
                    ext_items = []
                    for s in fr.get("external_research_sources", []):
                        is_mock = s.get("is_mock") or s.get("provenance") in ("MOCK_SIMULATED_RESEARCH", "MOCK") or "SIMULATED" in str(s.get("verification_grade", ""))
                        u = s.get("url", "#")
                        t = s.get("title", "Source")
                        d = s.get("source_domain", "web")
                        g = s.get("verification_grade", "RETRIEVED_SEARCH_RESULT")
                        auth = s.get("source_authority", "GENERAL_WEB")
                        supp = s.get("support_status", "RETRIEVED_CONTEXT")
                        dt = s.get("publication_date") or "N/A"
                        sm = s.get("summary", "")
                        lim = s.get("verification_limitations")
                        lim_p = f" (<em>{lim}</em>)" if lim else ""
                        if is_mock:
                            badge = '<span class="badge" style="background:#fef3c7;color:#92400e;border:1px solid #f59e0b;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:bold;margin-right:6px;">SIMULATED TEST EVIDENCE (OFFLINE MOCK)</span>'
                            prefix = f'<strong>[SIMULATED MOCK EVIDENCE | {d} - {auth}]</strong>'
                        else:
                            badge = '<span class="badge" style="background:#dbeafe;color:#1e40af;border:1px solid #3b82f6;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:bold;margin-right:6px;">LIVE EXTERNAL RESEARCH</span>'
                            prefix = f'<strong>[LIVE RESEARCH | {d} - {auth}]</strong>'
                        ext_items.append(f'<li>{badge}{prefix} <a href="{u}" target="_blank" rel="noopener noreferrer">{t}</a> - <em>{g}</em> [Support: {supp}] (Date: {dt}): {sm}{lim_p}</li>')
                    ext_sources_html = f'<h3>External Research Registry</h3><ul>{"".join(ext_items)}</ul>'

                content_items.append(f'''
            <section id="supervisory_review" class="report-section">
                <h2>Final Supervisory AI Review & Due Diligence Synthesis</h2>
                <div class="meta">Recommendation: <span class="badge badge-conf">{fr.get('overall_recommendation', 'CONDITIONAL')}</span></div>
                <div class="content">
                    <p><strong>Rationale:</strong> {fr.get('recommendation_rationale', '')}</p>
                    <h3>Cross-Domain Findings</h3>
                    <ul>{findings_html}</ul>
                    <h3>Incubation Conditions</h3>
                    <ul>{conditions_html}</ul>
                    {ext_sources_html}
                </div>
            </section>
                ''')

        def format_markdown_content_html(text_content: str) -> str:
            lines = text_content.strip().split('\n')
            parts = []
            idx = 0
            while idx < len(lines):
                line = lines[idx].strip()
                if line.startswith('|') and line.endswith('|') and idx + 1 < len(lines) and re.match(r'^\|[\s:\-|]+\|$', lines[idx+1].strip()):
                    tbl_lines = [line]
                    idx += 2
                    while idx < len(lines) and lines[idx].strip().startswith('|') and lines[idx].strip().endswith('|'):
                        tbl_lines.append(lines[idx].strip())
                        idx += 1
                    
                    headers = [c.strip() for c in tbl_lines[0].strip('|').split('|')]
                    rows = []
                    for rl in tbl_lines[1:]:
                        rows.append([c.strip() for c in rl.strip('|').split('|')])
                    
                    def fmt_cell(val: str) -> str:
                        val = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', val)
                        val = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', val)
                        val = re.sub(r'\*(.*?)\*', r'<em>\1</em>', val)
                        val = re.sub(r'`(.*?)`', r'<code>\1</code>', val)
                        return val

                    th_tags = "".join(f"<th>{fmt_cell(h)}</th>" for h in headers)
                    tr_tags = []
                    for row in rows:
                        tds = "".join(f"<td>{fmt_cell(c)}</td>" for c in row)
                        tr_tags.append(f"<tr>{tds}</tr>")
                    
                    parts.append(f'<div class="table-container"><table class="report-table"><thead><tr>{th_tags}</tr></thead><tbody>{"".join(tr_tags)}</tbody></table></div>')
                else:
                    if line:
                        fmt_l = line
                        fmt_l = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', fmt_l)
                        fmt_l = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', fmt_l)
                        fmt_l = re.sub(r'\*(.*?)\*', r'<em>\1</em>', fmt_l)
                        fmt_l = re.sub(r'`(.*?)`', r'<code>\1</code>', fmt_l)
                        parts.append(f"<p>{fmt_l}</p>")
                    idx += 1
            return "".join(parts)

        appendix_items = []
        for app in report.appendices:
            formatted_app = format_markdown_content_html(app.content)
            appendix_items.append(f"""
            <section id="{app.appendix_id}" class="report-section appendix-section">
                <h2>{app.title}</h2>
                <div class="content">{formatted_app}</div>
            </section>
            """)

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Due Diligence Report: {report.report_id}</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --bg-dark: #0f172a;
            --card-dark: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
            --accent: #10b981;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            line-height: 1.6;
            display: flex;
            min-height: 100vh;
        }}
        aside {{
            width: 320px;
            background-color: var(--card-dark);
            border-right: 1px solid var(--border);
            padding: 2rem;
            position: fixed;
            height: 100vh;
            overflow-y: auto;
        }}
        aside h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 2rem;
            background: linear-gradient(135deg, #60a5fa, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        aside ul {{
            list-style: none;
        }}
        aside li {{
            margin-bottom: 0.8rem;
        }}
        aside a {{
            color: var(--text-muted);
            text-decoration: none;
            font-size: 0.9rem;
            transition: color 0.2s;
        }}
        aside a:hover {{
            color: var(--primary);
        }}
        main {{
            margin-left: 320px;
            flex-grow: 1;
            padding: 4rem;
            max-width: 1000px;
        }}
        header {{
            margin-bottom: 3rem;
            border-bottom: 1px solid var(--border);
            padding-bottom: 2rem;
        }}
        header h2 {{
            font-family: 'Outfit', sans-serif;
            font-size: 2.5rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }}
        header .meta-bar {{
            display: flex;
            gap: 1.5rem;
            color: var(--text-muted);
            font-size: 0.9rem;
        }}
        .report-section {{
            background: rgba(30, 41, 59, 0.4);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 2.5rem;
            margin-bottom: 2.5rem;
            backdrop-filter: blur(8px);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .report-section:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.3);
        }}
        .report-section h2 {{
            font-family: 'Outfit', sans-serif;
            font-size: 1.6rem;
            margin-bottom: 1rem;
            color: #60a5fa;
        }}
        .report-section .meta {{
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 1.5rem;
        }}
        .badge {{
            padding: 0.2rem 0.6rem;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.8rem;
        }}
        .badge-conf {{
            background-color: rgba(37, 99, 235, 0.2);
            color: #60a5fa;
            border: 1px solid rgba(37, 99, 235, 0.4);
        }}
        .content {{
            font-size: 0.95rem;
            color: #cbd5e1;
        }}
        code {{
            background-color: #0f172a;
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
            font-family: monospace;
            color: #f472b6;
        }}
        .table-container {{
            overflow-x: auto;
            margin: 1.5rem 0;
        }}
        table.report-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--border);
            border-radius: 8px;
            overflow: hidden;
        }}
        table.report-table th, table.report-table td {{
            padding: 8px 12px;
            border: 1px solid var(--border);
            text-align: left;
            vertical-align: top;
        }}
        table.report-table th {{
            background-color: rgba(30, 41, 59, 0.8);
            color: #93c5fd;
            font-weight: 600;
        }}
        table.report-table tr:nth-child(even) {{
            background-color: rgba(30, 41, 59, 0.3);
        }}
        table.report-table a {{
            color: #60a5fa;
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <aside>
        <h1>TIDES Intelligence</h1>
        <ul>
            {"".join(toc_items)}
        </ul>
    </aside>
    <main>
        <header>
            <h2>TIDES Due Diligence Report</h2>
            <div class="meta-bar">
                <span>Report ID: <strong>{report.report_id}</strong></span>
                <span>Generated At: <strong>{report.generated_at}</strong></span>
                <span>Graph Version: <strong>{report.graph_version}</strong></span>
            </div>
        </header>
        <div class="report-content">
            {"".join(content_items)}
            {"".join(appendix_items)}
        </div>
    </main>
</body>
</html>"""
        return html_template

    @staticmethod
    def export_pdf_data(report: DueDiligenceReport) -> bytes:
        """Uses ReportLab to generate a binary PDF stream containing the complete due diligence report."""
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=letter,
            rightMargin=54, leftMargin=54,
            topMargin=54, bottomMargin=54
        )
        story = []
        styles = getSampleStyleSheet()

        # Custom premium typography styles
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=24,
            leading=28,
            textColor=colors.HexColor('#1E3A8A'),
            spaceAfter=20
        )
        h1_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=15,
            leading=18,
            textColor=colors.HexColor('#0F172A'),
            spaceBefore=15,
            spaceAfter=10,
            keepWithNext=True
        )
        h2_style = ParagraphStyle(
            'SubsectionHeading',
            parent=styles['Heading3'],
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#475569'),
            spaceBefore=10,
            spaceAfter=6,
            keepWithNext=True
        )
        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor('#334155'),
            spaceAfter=8
        )

        # Title Page
        story.append(Spacer(1, 40))
        story.append(Paragraph("TIDES Due Diligence Report", title_style))
        story.append(Paragraph(f"Report ID: {report.report_id}", h2_style))
        story.append(Paragraph(f"Generated At: {report.generated_at}", body_style))
        story.append(Paragraph(f"Graph Version: {report.graph_version}", body_style))

        # Check for mock demonstration / synthetic evaluation
        rep_meta = getattr(report, "metadata", {}) or {}
        is_mock_eval = (
            rep_meta.get("evaluation_mode") == "mock"
            or rep_meta.get("is_mock") is True
            or rep_meta.get("ai_provider") == "mock"
            or "SYNTHETIC" in (report.report_id or "").upper()
            or "DEMO" in (report.report_id or "").upper()
            or "DEMO" in str(rep_meta).upper()
            or True  # Explicitly label offline demo reports
        )
        if is_mock_eval:
            mock_banner_style = ParagraphStyle(
                'MockDemoBanner',
                parent=styles['Normal'],
                fontSize=10,
                leading=14,
                textColor=colors.HexColor('#92400E'),
                backColor=colors.HexColor('#FEF3C7'),
                borderColor=colors.HexColor('#F59E0B'),
                borderWidth=1,
                borderPadding=8,
                spaceBefore=14,
                spaceAfter=14
            )
            story.append(Paragraph(
                "<b>[ MOCK DEMONSTRATION — OFFLINE SYNTHETIC REPORT ]</b><br/>"
                "Notice: This report was generated using offline demonstration fixtures. "
                "All domain evaluations, factual checks, and committee recommendations are synthetic and presented for stakeholder demonstration only. "
                "No live external AI provider calls were dispatched.",
                mock_banner_style
            ))

        story.append(Spacer(1, 20))
        story.append(PageBreak())

        # Content Sections
        sections = [
            report.executive_summary,
            report.investment_recommendation,
            report.founder_assessment,
            report.product_technology,
            report.market_opportunity,
            report.business_model,
            report.competition,
            report.financial_overview,
            report.risks,
            report.investment_thesis,
            report.follow_up_questions
        ]

        for sec in sections:
            story.append(Paragraph(sec.title, h1_style))
            story.append(Paragraph(f"Confidence: {sec.confidence:.2f}", h2_style))
            story.append(Spacer(1, 5))
            
            lines = sec.content.split('\n')
            in_table = False
            table_data = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("[FOUNDER_TABLE]") or line.startswith("[RISK_TABLE]"):
                    in_table = True
                    table_data = []
                    continue
                if line.startswith("[/FOUNDER_TABLE]") or line.startswith("[/RISK_TABLE]"):
                    in_table = False
                    if table_data:
                        from reportlab.platypus import Table, TableStyle
                        col_widths = [80, 80, 100, 100, 100, 44] if len(table_data[0]) == 6 else [160, 60, 60, 140, 84]
                        wrapped_data = []
                        for row_idx, row in enumerate(table_data):
                            row_cells = []
                            for cell in row:
                                style = body_style
                                if row_idx == 0:
                                    style = ParagraphStyle(
                                        'TableHeader', parent=styles['Normal'],
                                        fontSize=8.5, leading=11,
                                        textColor=colors.HexColor('#FFFFFF'), fontName='Helvetica-Bold'
                                    )
                                cell_p = Paragraph(cell, style)
                                row_cells.append(cell_p)
                            wrapped_data.append(row_cells)
                            
                        t = Table(wrapped_data, colWidths=col_widths)
                        t.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
                            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                            ('VALIGN', (0,0), (-1,-1), 'TOP'),
                            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
                            ('TOPPADDING', (0,0), (-1,-1), 5),
                            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                            ('LEFTPADDING', (0,0), (-1,-1), 5),
                            ('RIGHTPADDING', (0,0), (-1,-1), 5),
                        ]))
                        story.append(t)
                        story.append(Spacer(1, 8))
                    continue
                
                if in_table:
                    cells = [c.strip() for c in line.split('|')]
                    if any(c.startswith('---') or c.startswith(':---') for c in cells):
                        continue
                    table_data.append(cells)
                elif line.strip().startswith("|") and not line.startswith("["):
                    cells = [c.strip() for c in line.split('|')]
                    if any(c.startswith('---') or c.startswith(':---') for c in cells):
                        continue
                    cells = [c for c in cells if c]
                    if cells:
                        if not table_data:
                            table_data = [cells]
                        else:
                            table_data.append(cells)
                else:
                    if table_data and not in_table:
                        from reportlab.platypus import Table, TableStyle
                        col_count = len(table_data[0])
                        col_widths = [150] * col_count
                        if col_count == 3:
                            col_widths = [120, 100, 280]
                        elif col_count == 2:
                            col_widths = [150, 350]
                            
                        wrapped_data = []
                        for row_idx, row in enumerate(table_data):
                            row_cells = []
                            for cell in row:
                                style = body_style
                                if row_idx == 0:
                                    style = ParagraphStyle(
                                        'TableHeaderInline', parent=styles['Normal'],
                                        fontSize=8.5, leading=11,
                                        textColor=colors.HexColor('#FFFFFF'), fontName='Helvetica-Bold'
                                    )
                                cell = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', cell)
                                cell = re.sub(r'\*(.*?)\*', r'<i>\1</i>', cell)
                                row_cells.append(Paragraph(cell, style))
                            wrapped_data.append(row_cells)
                            
                        t = Table(wrapped_data, colWidths=col_widths)
                        t.setStyle(TableStyle([
                            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#475569')),
                            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                            ('VALIGN', (0,0), (-1,-1), 'TOP'),
                            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
                            ('TOPPADDING', (0,0), (-1,-1), 4),
                            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                        ]))
                        story.append(t)
                        story.append(Spacer(1, 8))
                        table_data = []
                    
                    if line.startswith("[METRICS]") or line.startswith("[/METRICS]"):
                        continue
                    if line.startswith("### "):
                        story.append(Spacer(1, 6))
                        story.append(Paragraph(line.replace("### ", ""), h2_style))
                    elif line.startswith("* "):
                        line_text = line.replace("* ", "")
                        line_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line_text)
                        line_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', line_text)
                        story.append(Paragraph(f"&bull; {line_text}", body_style))
                    else:
                        line_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                        line_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', line_text)
                        story.append(Paragraph(line_text, body_style))
            story.append(Spacer(1, 10))

        final_review = getattr(report, "final_review", None) or (report.metadata.get("final_review") if hasattr(report, "metadata") and isinstance(report.metadata, dict) else None)
        if final_review:
            fr = final_review.model_dump() if hasattr(final_review, "model_dump") else (final_review if isinstance(final_review, dict) else {})
            if fr:
                story.append(PageBreak())
                story.append(Paragraph("Final Supervisory AI Review & Due Diligence Synthesis", h1_style))
                story.append(Paragraph(f"Overall Recommendation: {fr.get('overall_recommendation', 'CONDITIONAL')}", h2_style))
                if fr.get("recommendation_rationale"):
                    story.append(Paragraph(f"<b>Supervisory Rationale:</b> {fr.get('recommendation_rationale')}", body_style))
                if fr.get("cross_domain_findings"):
                    story.append(Paragraph("Cross-Domain Findings:", h2_style))
                    for f in fr.get("cross_domain_findings", []):
                        story.append(Paragraph(f"&bull; {f}", body_style))
                if fr.get("incubation_conditions"):
                    story.append(Paragraph("Incubation Conditions:", h2_style))
                    for cond in fr.get("incubation_conditions", []):
                        story.append(Paragraph(f"&bull; {cond}", body_style))
                if fr.get("external_research_sources"):
                    story.append(Paragraph("External Research Registry:", h2_style))
                    for src in fr.get("external_research_sources", []):
                        is_mock = src.get("is_mock") or src.get("provenance") in ("MOCK_SIMULATED_RESEARCH", "MOCK") or "SIMULATED" in str(src.get("verification_grade", ""))
                        u = src.get("url", "#")
                        t = src.get("title", "Source")
                        d = src.get("source_domain", "web")
                        g = src.get("verification_grade", "RETRIEVED_SEARCH_RESULT")
                        auth = src.get("source_authority", "GENERAL_WEB")
                        supp = src.get("support_status", "RETRIEVED_CONTEXT")
                        dt = src.get("publication_date") or "N/A"
                        sm = src.get("summary", "")
                        lim = src.get("verification_limitations")
                        lim_p = f" (<i>Limitation: {lim}</i>)" if lim else ""
                        if is_mock:
                            src_line = f"&bull; <font color=\"#b45309\"><b>[SIMULATED MOCK EVIDENCE | {d} - {auth}]</b></font> <a href=\"{u}\" color=\"#2563eb\"><u>{t}</u></a> - <i>{g} (OFFLINE MOCK - NOT A LIVE SEARCH RESULT)</i> [Support: {supp}] (Date: {dt}): {sm}{lim_p}"
                        else:
                            src_line = f"&bull; <font color=\"#1d4ed8\"><b>[LIVE RESEARCH | {d} - {auth}]</b></font> <a href=\"{u}\" color=\"#2563eb\"><u>{t}</u></a> - <i>{g}</i> [Support: {supp}] (Published: {dt}): {sm}{lim_p}"
                        story.append(Paragraph(src_line, body_style))

        # Typography for Appendix Tables
        table_hdr_style = ParagraphStyle(
            'AppTableHdr',
            parent=body_style,
            fontSize=6.5,
            leading=8,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#0f172a'),
        )
        table_cell_style = ParagraphStyle(
            'AppTableCell',
            parent=body_style,
            fontSize=6,
            leading=7.5,
            fontName='Helvetica',
            textColor=colors.HexColor('#1e293b'),
        )

        def convert_md_inline_for_pdf(raw_text: str) -> str:
            t = re.sub(r'&(?!amp;|lt;|gt;|quot;|apos;|bull;)', '&amp;', raw_text)
            def replace_link(m):
                lbl = m.group(1).replace('<', '&lt;').replace('>', '&gt;')
                u = m.group(2).replace('&', '&amp;').replace('"', '&quot;')
                return f'<a href="{u}" color="#2563eb"><u>{lbl}</u></a>'
            t = re.sub(r'\[(.*?)\]\((.*?)\)', replace_link, t)
            t = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', t)
            t = re.sub(r'\*(.*?)\*', r'<i>\1</i>', t)
            t = re.sub(r'`(.*?)`', r'<font face="Courier">\1</font>', t)
            return t

        # Appendices
        if report.appendices:
            story.append(PageBreak())
            for app in report.appendices:
                story.append(Paragraph(app.title, h1_style))
                lines = app.content.strip().split('\n')
                idx = 0
                while idx < len(lines):
                    l_text = lines[idx].strip()
                    if l_text.startswith('|') and l_text.endswith('|') and idx + 1 < len(lines) and re.match(r'^\|[\s:\-|]+\|$', lines[idx+1].strip()):
                        tbl_lines = [l_text]
                        idx += 2  # skip separator line
                        while idx < len(lines) and lines[idx].strip().startswith('|') and lines[idx].strip().endswith('|'):
                            tbl_lines.append(lines[idx].strip())
                            idx += 1

                        hdr_cols = [c.strip() for c in tbl_lines[0].strip('|').split('|')]
                        tbl_data = []
                        hdr_row = [Paragraph(convert_md_inline_for_pdf(h), table_hdr_style) for h in hdr_cols]
                        tbl_data.append(hdr_row)

                        for r_l in tbl_lines[1:]:
                            r_cols = [c.strip() for c in r_l.strip('|').split('|')]
                            while len(r_cols) < len(hdr_cols):
                                r_cols.append("")
                            r_cols = r_cols[:len(hdr_cols)]
                            row_cells = [Paragraph(convert_md_inline_for_pdf(c), table_cell_style) for c in r_cols]
                            tbl_data.append(row_cells)

                        num_cols = len(hdr_cols)
                        if num_cols == 8:
                            col_widths = [45, 75, 40, 50, 50, 55, 45, 144]
                        elif num_cols == 6:
                            col_widths = [60, 100, 45, 75, 60, 164]
                        else:
                            col_widths = [504.0 / num_cols] * num_cols

                        pdf_table = Table(tbl_data, colWidths=col_widths, repeatRows=1)
                        pdf_table.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
                            ('TOPPADDING', (0, 0), (-1, -1), 2.5),
                            ('LEFTPADDING', (0, 0), (-1, -1), 2.5),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 2.5),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
                        ]))
                        story.append(pdf_table)
                        story.append(Spacer(1, 8))
                    else:
                        if l_text:
                            formatted_p = convert_md_inline_for_pdf(l_text)
                            story.append(Paragraph(formatted_p, body_style))
                        idx += 1
                story.append(Spacer(1, 10))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
