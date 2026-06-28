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

        appendix_items = []
        for app in report.appendices:
            formatted_app = app.content
            formatted_app = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted_app)
            formatted_app = re.sub(r'\*(.*?)\*', r'<em>\1</em>', formatted_app)
            formatted_app = re.sub(r'`(.*?)`', r'<code>\1</code>', formatted_app)
            formatted_app = formatted_app.replace('\n', '<br>')
            
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
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
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
                elif "|" in line and not line.startswith("["):
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

        # Appendices
        if report.appendices:
            story.append(PageBreak())
            for app in report.appendices:
                story.append(Paragraph(app.title, h1_style))
                for p_text in app.content.split('\n'):
                    p_text = p_text.strip()
                    if p_text:
                        p_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', p_text)
                        p_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', p_text)
                        p_text = re.sub(r'`(.*?)`', r'<font face="Courier">\1</font>', p_text)
                        story.append(Paragraph(p_text, body_style))
                story.append(Spacer(1, 10))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
