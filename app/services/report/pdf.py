"""PDF report generator for startup assessment results."""
from __future__ import annotations

import io
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.modules.startup_profiles.schemas import AIAssessmentRecordRead


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------

_TIDES_BLUE = colors.HexColor("#1B4F72")
_TIDES_LIGHT = colors.HexColor("#D6EAF8")
_ACCENT_GREEN = colors.HexColor("#1E8449")
_ACCENT_RED = colors.HexColor("#922B21")
_ACCENT_AMBER = colors.HexColor("#B7950B")
_GREY = colors.HexColor("#5D6D7E")
_LIGHT_GREY = colors.HexColor("#F2F3F4")


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------

def _build_styles() -> dict:
    base = getSampleStyleSheet()

    def style(name, **kwargs):
        return ParagraphStyle(name=name, **kwargs)

    return {
        "cover_title": style(
            "CoverTitle",
            fontSize=26,
            textColor=_TIDES_BLUE,
            alignment=TA_CENTER,
            spaceAfter=6,
            fontName="Helvetica-Bold",
        ),
        "cover_sub": style(
            "CoverSub",
            fontSize=13,
            textColor=_GREY,
            alignment=TA_CENTER,
            spaceAfter=4,
            fontName="Helvetica",
        ),
        "section_heading": style(
            "SectionHeading",
            fontSize=14,
            textColor=_TIDES_BLUE,
            spaceBefore=14,
            spaceAfter=4,
            fontName="Helvetica-Bold",
        ),
        "body": style(
            "Body",
            fontSize=10,
            textColor=colors.black,
            leading=15,
            spaceAfter=4,
            alignment=TA_LEFT,
            fontName="Helvetica",
        ),
        "bullet": style(
            "Bullet",
            fontSize=10,
            textColor=colors.black,
            leading=14,
            spaceAfter=2,
            leftIndent=16,
            bulletIndent=8,
            fontName="Helvetica",
        ),
        "footer": style(
            "Footer",
            fontSize=8,
            textColor=_GREY,
            alignment=TA_CENTER,
            fontName="Helvetica-Oblique",
        ),
    }


# ---------------------------------------------------------------------------
# Score bar helper
# ---------------------------------------------------------------------------

def _score_color(score: int, max_score: int = 10) -> colors.Color:
    ratio = score / max_score if max_score else 0
    if ratio >= 0.7:
        return _ACCENT_GREEN
    if ratio >= 0.4:
        return _ACCENT_AMBER
    return _ACCENT_RED


def _score_table(label: str, score: int, max_score: int = 10) -> Table:
    """Return a two-column table: label | score badge."""
    badge_color = _score_color(score, max_score)
    score_text = f"<font color='white'><b>{score}/{max_score}</b></font>"
    label_para = Paragraph(label, ParagraphStyle(
        "ScoreLabel", fontSize=10, fontName="Helvetica", textColor=colors.black, leading=14,
    ))
    score_para = Paragraph(score_text, ParagraphStyle(
        "ScoreBadge", fontSize=10, fontName="Helvetica-Bold",
        alignment=TA_CENTER, textColor=colors.white, leading=14,
    ))
    tbl = Table([[label_para, score_para]], colWidths=[12 * cm, 3 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (1, 0), (1, 0), badge_color),
        ("BACKGROUND", (0, 0), (0, 0), _LIGHT_GREY),
        ("ROUNDEDCORNERS", [4]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, 0), 8),
        ("RIGHTPADDING", (1, 0), (1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return tbl


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_assessment_pdf(
    startup_name: str,
    record: AIAssessmentRecordRead,
) -> bytes:
    """Generate a PDF assessment report and return raw bytes.

    Args:
        startup_name: Human-readable startup name for the cover page.
        record: The persisted assessment record to render.

    Returns:
        PDF file content as ``bytes``.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Assessment Report – {startup_name}",
        author="TIDES IIT Roorkee",
    )

    styles = _build_styles()
    story = []

    # ---- Cover ----
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("TIDES IIT Roorkee", styles["cover_sub"]))
    story.append(Paragraph("Startup Assessment Report", styles["cover_title"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(startup_name, styles["cover_sub"]))
    generated_on = datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")
    story.append(Paragraph(f"Generated: {generated_on}", styles["cover_sub"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=_TIDES_BLUE))
    story.append(Spacer(1, 0.6 * cm))

    # ---- Executive Summary ----
    story.append(Paragraph("Executive Summary", styles["section_heading"]))
    story.append(Paragraph(record.executive_summary, styles["body"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_TIDES_LIGHT))

    # ---- Scores ----
    story.append(Paragraph("Evaluation Scores", styles["section_heading"]))
    story.append(_score_table("Innovation", record.innovation_score))
    story.append(Spacer(1, 0.15 * cm))
    story.append(_score_table("Market Potential", record.market_score))
    story.append(Spacer(1, 0.15 * cm))
    story.append(_score_table("Execution Readiness", record.execution_score))
    story.append(Spacer(1, 0.3 * cm))
    story.append(_score_table("Overall Score", record.overall_score, max_score=30))
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_TIDES_LIGHT))

    # ---- Strengths ----
    story.append(Paragraph("Strengths", styles["section_heading"]))
    for item in record.strengths:
        story.append(Paragraph(f"• {item}", styles["bullet"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_TIDES_LIGHT))

    # ---- Weaknesses ----
    story.append(Paragraph("Weaknesses", styles["section_heading"]))
    for item in record.weaknesses:
        story.append(Paragraph(f"• {item}", styles["bullet"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_TIDES_LIGHT))

    # ---- Recommendations ----
    story.append(Paragraph("Recommendations", styles["section_heading"]))
    for item in record.recommendations:
        story.append(Paragraph(f"• {item}", styles["bullet"]))
    story.append(Spacer(1, 0.6 * cm))

    # ---- Footer note ----
    story.append(HRFlowable(width="100%", thickness=1, color=_TIDES_BLUE))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "This report was generated by the TIDES AI Startup Evaluation Platform. "
        "Scores reflect AI-assisted analysis and should be reviewed by an evaluator.",
        styles["footer"],
    ))

    doc.build(story)
    return buffer.getvalue()
