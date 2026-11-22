"""Institutional due-diligence PDF for a completed evaluation run.

Built with ReportLab from persisted artifacts only (evaluation graph + application records).
The PDF is written once to uploads/reports/{evaluation_id}.pdf and served from there; its
SHA-256 is recorded on the evaluation run.
"""

from __future__ import annotations

import hashlib
import io
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.applications.models import ApplicationSubmission, EvaluationRun
from app.modules.applications.results import build_run_results, evidence_records, load_graph_dict
from app.modules.applications.runner import MOCK_DISCLOSURE
from app.modules.evaluation.evidence_classes import EVIDENCE_CLASS_LABELS

CONFIDENTIALITY = (
    "CONFIDENTIAL — Prepared for the Technology Incubation and Entrepreneurship Development Society (TIEDS), "
    "IIT Roorkee incubation committee. Contains applicant business information. Do not distribute outside "
    "the evaluation committee."
)

SECTION_TITLES = [
    "1. Cover", "2. Executive Summary", "3. Company Overview", "4. Problem and Solution",
    "5. Market Opportunity", "6. Founder and Team", "7. Business Model and Commercialisation",
    "8. Innovation, IP and Impact", "9. Financials and Incubation Support", "10. Criterion-Level Assessments",
    "11. Evidence Quality", "12. Key Strengths", "13. Key Concerns", "14. Contradictions", "15. Risk Register",
    "16. Missing Information", "17. Priority Diligence Questions", "18. Incubation Support Recommendations",
    "19. Supervisory Synthesis", "20. Final Recommendation and Conditions",
]

_DOMAIN_SECTIONS = [
    ("4. Problem and Solution", "problem_solution", ("product_technology", "product_analysis", "trl_analysis")),
    ("5. Market Opportunity", "market_opportunity", ("market_opportunity", "market_analysis", "competition")),
    ("6. Founder and Team", "founder_team", ("founder_assessment", "founder_analysis")),
    ("7. Business Model and Commercialisation", "commercialisation", ("business_model",)),
    ("8. Innovation, IP and Impact", "innovation_impact", ("ip_analysis",)),
    ("9. Financials and Incubation Support", "financials_support", ("financial_overview", "financial_analysis")),
]


def _t(value: Any, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", str(value if value is not None else "")).strip()
    text = re.sub(r"[*#`]+", "", text)  # strip markdown emphasis from engine text
    if limit and len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return escape(text)


def _section_text(report: dict[str, Any], keys: tuple[str, ...]) -> list[str]:
    out = []
    for k in keys:
        sec = report.get(k)
        content = sec.get("content") if isinstance(sec, dict) else None
        if content and str(content).strip():
            for para in re.split(r"\n\s*\n", str(content)):
                if para.strip():
                    out.append(para.strip())
    return out[:6]


def _pdf_dir() -> Path:
    d = (Path(get_settings().upload_dir) / "reports").resolve()
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_or_build_run_pdf(db: Session, run: EvaluationRun) -> tuple[bytes, str]:
    safe = re.sub(r"[^A-Za-z0-9-]", "", run.id)
    path = _pdf_dir() / f"{safe}.pdf"
    if path.exists():
        data = path.read_bytes()
    else:
        data = build_run_pdf(db, run)
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(data)
        tmp.replace(path)
        summary = dict(run.summary or {})
        summary["pdf"] = {
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        run.summary = summary
        db.commit()
    from app.modules.startups.models import StartupApplication

    st = db.get(StartupApplication, run.startup_id)
    name = re.sub(r"[^A-Za-z0-9]+", "_", (st.startup_name if st else "Startup")).strip("_")[:60] or "Startup"
    prefix = "MOCK_DEMO_" if run.mode == "MOCK_DEMONSTRATION" else ""
    return data, f"{prefix}TIDES_Due_Diligence_{name}_{safe[:8]}.pdf"


def build_run_pdf(db: Session, run: EvaluationRun) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.platypus import (
        KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
    )

    from app.modules.startups.models import StartupApplication

    results = build_run_results(db, run)
    graph = load_graph_dict(run.id) or {}
    report = graph.get("report") or {}
    st = db.get(StartupApplication, run.startup_id)
    sub = db.query(ApplicationSubmission).filter(ApplicationSubmission.startup_id == run.startup_id).first()
    is_mock = run.mode == "MOCK_DEMONSTRATION"
    generated = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")

    NAVY = colors.HexColor("#14284B")
    INK = colors.HexColor("#1F2937")
    MUTED = colors.HexColor("#6B7280")
    RULE = colors.HexColor("#D1D5DB")
    AMBER = colors.HexColor("#B45309")

    base = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=base["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13.5, textColor=INK, spaceAfter=5)
    small = ParagraphStyle("small", parent=body, fontSize=7.8, leading=10)
    h1 = ParagraphStyle("h1", parent=base["Heading1"], fontName="Helvetica-Bold", fontSize=15, leading=19, textColor=NAVY, spaceBefore=4, spaceAfter=8)
    h2 = ParagraphStyle("h2", parent=base["Heading2"], fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=NAVY, spaceBefore=8, spaceAfter=4)
    bullet = ParagraphStyle("bullet", parent=body, leftIndent=10, bulletIndent=0)
    cover_title = ParagraphStyle("ct", parent=h1, fontSize=24, leading=30, alignment=TA_CENTER, spaceAfter=6)
    cover_sub = ParagraphStyle("cs", parent=body, fontSize=11, leading=15, alignment=TA_CENTER, textColor=MUTED)
    banner = ParagraphStyle("banner", parent=body, fontName="Helvetica-Bold", fontSize=10, leading=13, alignment=TA_CENTER, textColor=colors.white)

    def table(rows: list[list[Any]], widths: list[float], header: bool = True, font: float = 7.6) -> Table:
        cell = ParagraphStyle("cell", parent=small, fontSize=font, leading=font + 2.2)
        head = ParagraphStyle("head", parent=cell, fontName="Helvetica-Bold", textColor=colors.white)
        data = []
        for i, row in enumerate(rows):
            data.append([Paragraph(str(c), head if (header and i == 0) else cell) for c in row])
        t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
        style = [
            ("GRID", (0, 0), (-1, -1), 0.4, RULE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]
        if header:
            style.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
        t.setStyle(TableStyle(style))
        return t

    def bullets(items: list[str], empty: str) -> list[Any]:
        if not items:
            return [Paragraph(_t(empty), body)]
        return [Paragraph(_t(i, 600), bullet, bulletText="•") for i in items]

    def cited(items: list[dict[str, Any]]) -> list[str]:
        out = []
        for it in items:
            refs = ", ".join(str(e)[:8] for e in it.get("evidence_ids") or [])
            tag = f" [{it.get('criterion_id')}; {it.get('domain')}" + (f"; evidence {refs}" if refs else "") + "]"
            out.append(f"{it.get('text')}{tag}")
        return out

    story: list[Any] = []
    domains = {d["key"]: d for d in results.get("domains", [])}
    sup = results.get("supervisory") or {}
    coverage = results.get("coverage") or {}
    cover_criteria = results.get("cover_criteria") or []

    # 1. Cover -------------------------------------------------------------------------
    story.append(Spacer(1, 30 * mm))
    if is_mock:
        b = Table([[Paragraph(escape(MOCK_DISCLOSURE), banner)]], colWidths=[170 * mm])
        b.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), AMBER), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
        story += [b, Spacer(1, 10 * mm)]
    story.append(Paragraph("Startup Incubation Due-Diligence Report", cover_title))
    story.append(Paragraph(_t(st.startup_name if st else results.get("startup_name")), ParagraphStyle("cn", parent=cover_title, fontSize=18, leading=24, textColor=INK)))
    story.append(Paragraph("TIDES-AI · LaunchIndex 87-criterion evaluation", cover_sub))
    story.append(Spacer(1, 14 * mm))
    meta_rows = [
        ["Field", "Value"],
        ["Application reference", _t(sub.application_ref if sub else "—")],
        ["Evaluation ID", _t(run.id)],
        ["Startup ID", _t(run.startup_id)],
        ["Report ID", _t(results.get("report_id") or "—")],
        ["Sector / Stage", _t(f"{st.sector or '—'} / {st.stage or '—'}" if st else "—")],
        ["Evaluation mode", "Offline synthetic demonstration (MockAIGateway)" if is_mock else "Live provider evaluation"],
        ["Evaluation completed", _t(run.finished_at.strftime("%d %b %Y %H:%M UTC") if run.finished_at else "—")],
        ["Report generated", _t(generated)],
        ["Criteria accounted for", _t(f"{coverage.get('total_present', 0)} / {coverage.get('total_expected', 87)}")],
    ]
    story.append(table(meta_rows, [55 * mm, 115 * mm], font=8.5))
    story.append(Spacer(1, 12 * mm))
    story.append(Paragraph(_t(CONFIDENTIALITY), small))
    story.append(PageBreak())

    # 2. Executive summary ---------------------------------------------------------------
    story.append(Paragraph("2. Executive Summary", h1))
    if is_mock:
        story.append(Paragraph(f"<b>{escape(MOCK_DISCLOSURE)}</b>. All assessments below are deterministic synthetic outputs produced to demonstrate the workflow; they are not an evaluation of any real company.", body))
    story += [Paragraph(_t(p, 1500), body) for p in _section_text(report, ("executive_summary",))[:3]]
    ws = results.get("weighted_score") or {}
    if ws:
        score10 = ws.get("overall_score_10")
        story.append(Paragraph(
            f"<b>Weighted score:</b> {_t(score10) if score10 is not None else 'not available'}"
            f"{' / 10' if score10 is not None else ''} under scoring standard {_t(ws.get('standard_version'))} "
            f"({_t(ws.get('standard_status'))}; approved by {_t(ws.get('approved_by') or 'not recorded')}; "
            f"effective {_t(ws.get('effective_date') or 'not recorded')}).",
            body))
        story.append(Paragraph(_t(ws.get("decision_note") or ws.get("recommendation_basis")), small))
        if str(ws.get("standard_status") or "").upper() == "PROVISIONAL":
            story.append(Paragraph("The scoring weights are provisional (equal weights); treat the weighted score as indicative only.", small))
        rows_w = [["Section", "Weight", "Section score", "Contribution", "Criteria scored"]]
        for sec in ws.get("sections", []):
            rows_w.append([_t(sec["title"]), f"{sec['weight_pct']:.1f}%",
                           f"{sec['score_10']} / 10" if sec.get("score_10") is not None else "—",
                           f"{sec['weighted_contribution']}" if sec["weighted_contribution"] is not None else "—",
                           f"{sec['criteria_scored']} (not scored: {sec['criteria_not_scored']})"])
        story.append(table(rows_w, [55 * mm, 20 * mm, 28 * mm, 25 * mm, 42 * mm], font=8))
    story.append(Paragraph(f"<b>Supervisory position:</b> {_t(sup.get('overall_diligence_position') or 'Not available')}", body))
    story.append(Paragraph(f"<b>Committee recommendation:</b> {_t(sup.get('committee_recommendation') or 'Not available')}", body))
    cls_counts = coverage.get("evidence_classes") or {}
    story.append(Paragraph(
        "<b>Coverage:</b> " + _t(
            f"{coverage.get('domain_criteria_present', 0)}/81 domain criteria and "
            f"{coverage.get('cover_criteria_present', 0)}/6 cover criteria assessed across "
            f"{coverage.get('domains_completed', 0)}/6 specialist domains. Evidence classes: "
            + ", ".join(f"{EVIDENCE_CLASS_LABELS.get(k, k)} {v}" for k, v in sorted(cls_counts.items()))
        ), body))

    # 3. Company overview -----------------------------------------------------------------
    story.append(Paragraph("3. Company Overview", h1))
    ov = [["Item", "Applicant-reported information"]]
    for label, val in (
        ("Company", st.startup_name if st else None), ("Sector", st.sector if st else None),
        ("Industry", sub.industry if sub else None), ("Stage", st.stage if st else None),
        ("Location", sub.location if sub else None), ("Website", sub.website if sub else None),
        ("Problem statement", st.problem_statement if st else None), ("Proposed solution", st.solution_summary if st else None),
        ("Target market", st.target_market if st else None), ("Business model", st.business_model if st else None),
        ("Traction", st.traction_summary if st else None), ("Funding requirement", sub.funding_requirement if sub else None),
        ("Incubation support requested", sub.incubation_support_requirement if sub else None),
    ):
        ov.append([label, _t(val or "Not provided", 700)])
    story.append(table(ov, [45 * mm, 125 * mm], font=8))
    story.append(Paragraph("Founder and contact personal details are held in the application record and omitted from this report.", small))

    # 4-9. Domain sections ------------------------------------------------------------------
    for title, dkey, report_keys in _DOMAIN_SECTIONS:
        d = domains.get(dkey) or {}
        story.append(PageBreak())
        story.append(Paragraph(title, h1))
        story.append(Paragraph(_t(
            f"Status: {d.get('status', 'MISSING')} · Criteria assessed: {d.get('criteria_assessed', 0)}/{d.get('criteria_total', 0)} · "
            f"Average score: {d.get('average_score') if d.get('average_score') is not None else '—'} · Confidence: {d.get('confidence') if d.get('confidence') is not None else '—'}"
        ), small))
        for p in [d.get("summary"), d.get("executive_conclusion")]:
            if p:
                story.append(Paragraph(_t(p, 900), body))
        for p in _section_text(report, report_keys)[:3]:
            story.append(Paragraph(_t(p, 1400), body))
        rows = [["ID", "Criterion", "Score", "Evidence class"]]
        for c in d.get("criteria", []):
            rows.append([c["criterion_id"], _t(c["criterion_name"], 90), _t(c.get("score") if c.get("score") is not None else "—"), _t(c["evidence_class_label"])])
        story.append(table(rows, [16 * mm, 104 * mm, 16 * mm, 34 * mm]))

    # 10. Criterion-level assessments --------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("10. Criterion-Level Assessments", h1))
    story.append(Paragraph("All 87 canonical criteria: six cover/intake criteria (CM-01..CM-06) followed by the 81 domain criteria in registry order. Evidence references are shortened IDs; full IDs are listed in the Evidence Appendix.", small))
    rows = [["ID", "Criterion", "Score", "Evidence class", "Evidence", "Rationale / missing information"]]
    for c in cover_criteria:
        rows.append([c["criterion_id"], _t(c["criterion_name"], 60), "—", _t(c["evidence_class_label"]),
                     _t(", ".join(e[:8] for e in c.get("evidence_ids") or []) or "—"),
                     _t(f"Value ({c.get('source') or 'none'}): {c.get('value') or 'not provided'}", 160)])
    for d in results.get("domains", []):
        for c in d.get("criteria", []):
            note = c.get("rationale") or ""
            if c.get("missing_information"):
                note = f"{note} Missing: {c['missing_information']}"
            rows.append([c["criterion_id"], _t(c["criterion_name"], 60), _t(c.get("score") if c.get("score") is not None else "—"),
                         _t(c["evidence_class_label"]), _t(", ".join(e[:8] for e in c.get("evidence_ids") or []) or "—"), _t(note, 220)])
    story.append(table(rows, [14 * mm, 40 * mm, 11 * mm, 24 * mm, 21 * mm, 60 * mm], font=6.8))

    # 11. Evidence quality ------------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("11. Evidence Quality", h1))
    story.append(Paragraph(
        "Each criterion carries exactly one evidence class. <b>Applicant-reported</b>: stated by the applicant without a supporting document. "
        "<b>Documentary evidence</b>: supported by a cited passage in a submitted document. <b>Independently verified</b>: corroborated by a recorded "
        "third-party source (none in offline mode). <b>Not verified</b>: an estimate, unsupported assumption or contradiction. <b>Missing</b>: not provided. "
        "Missing evidence is reported as a diligence gap and is not by itself treated as a weakness of the venture.", body))
    q = [["Evidence class", "Criteria"]] + [[_t(EVIDENCE_CLASS_LABELS.get(k, k)), str(v)] for k, v in sorted(cls_counts.items())]
    story.append(table(q, [80 * mm, 30 * mm], font=8.5))

    # 12-18 ---------------------------------------------------------------------------------
    story.append(Paragraph("12. Key Strengths", h1))
    story += bullets(cited(sup.get("major_strengths") or []), "No strengths met the documentary-evidence threshold (score >= 7 with cited evidence).")
    story.append(Paragraph("13. Key Concerns", h1))
    story += bullets(cited(sup.get("material_weaknesses") or []) + [w for d in results.get("domains", []) for w in d.get("weaknesses", [])][:6], "No material concerns recorded.")
    flags = results.get("red_flags") or []
    story.append(Paragraph("TAES red-flag checks", h2))
    story += bullets([f"{f['rule']}: {f['finding']} {f['action']} [{', '.join(f.get('criteria', []))}]" for f in flags],
                     "No TAES red flags triggered (TRL claim vs revenue; combined founder equity).")
    story.append(Paragraph("14. Contradictions", h1))
    story += bullets([f"{c.get('description') or c.get('text') or c}" + (f" [{c.get('domain')}]" if isinstance(c, dict) and c.get("domain") else "") for c in sup.get("contradictions") or []], "No contradictions were identified between submitted documents and applicant statements.")
    story.append(PageBreak())
    story.append(Paragraph("15. Risk Register", h1))
    risk_rows = [["ID", "Domain", "Severity", "Risk", "Mitigation"]]
    for d in results.get("domains", []):
        for r in d.get("risks", [])[:4]:
            risk_rows.append([_t(r.get("id"), 30), _t(d["title"], 30), _t(r.get("severity")), _t(r.get("description"), 220), _t(r.get("mitigation"), 140)])
    if len(risk_rows) == 1:
        risk_rows.append(["—", "—", "—", "No risks recorded", "—"])
    story.append(table(risk_rows, [30 * mm, 28 * mm, 15 * mm, 60 * mm, 37 * mm], font=7))
    story.append(Paragraph("16. Missing Information", h1))
    story += bullets(cited(sup.get("missing_evidence") or []), "All canonical criteria contain applicant information.")
    story.append(Paragraph("17. Priority Diligence Questions", h1))
    story += bullets(list(sup.get("priority_diligence_questions") or []), "No priority questions recorded.")
    story.append(Paragraph("Required founder clarifications", h2))
    story += bullets(list(sup.get("required_founder_clarifications") or []), "None.")
    story.append(Paragraph("18. Incubation Support Recommendations", h1))
    story += bullets(cited(sup.get("recommended_incubation_support") or []), "The applicant did not specify incubation support needs (FI-10..FI-15).")

    # 19-20 ----------------------------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("19. Supervisory Synthesis", h1))
    story.append(Paragraph(_t(sup.get("overall_diligence_position") or "Supervisory review output not available."), body))
    story.append(Paragraph(f"<b>Rationale:</b> {_t(sup.get('recommendation_rationale') or '—')}", body))
    story.append(Paragraph("Team capability observations", h2))
    story += bullets(cited(sup.get("team_capability_observations") or []), "No team observations recorded.")
    story.append(Paragraph("Financial and technical risks", h2))
    story += bullets([f"{r.get('description')} [{r.get('domain')}]" for r in sup.get("financial_and_technical_risks") or []], "None recorded.")
    story.append(Paragraph("Market risks", h2))
    story += bullets([f"{r.get('description')} [{r.get('domain')}]" for r in sup.get("market_risks") or []], "None recorded.")
    story.append(Paragraph(_t("Domains cited: " + ", ".join(sup.get("domains_cited") or [])), small))
    story.append(Paragraph("20. Final Recommendation and Conditions", h1))
    story.append(KeepTogether([
        Paragraph(f"<b>Committee recommendation:</b> {_t(sup.get('committee_recommendation') or 'Not available')}", body),
        Paragraph(
            f"<b>Weighted score:</b> {_t(ws.get('overall_score_10'))} / 10 · standard {_t(ws.get('standard_version'))} · "
            f"{_t(ws.get('recommendation') or ws.get('recommendation_basis'))}", body) if ws else Spacer(1, 1),
        Paragraph("<b>Conditional incubation requirements:</b>", body),
        *bullets(list(sup.get("conditional_requirements") or []), "No conditions recorded."),
    ]))
    story.append(Paragraph("This recommendation supports, and does not replace, the decision of the TIEDS incubation committee. It makes no claim of regulatory compliance, patent grant, ethics approval or customer traction beyond the evidence classes stated above.", small))

    # Appendices -----------------------------------------------------------------------------
    story.append(PageBreak())
    story.append(Paragraph("Appendix A. Methodology", h1))
    story.append(Paragraph(
        "Supporting documents are parsed and passed through ten staged extraction passes that produce claims with document evidence. "
        "Six domain specialists (Problem &amp; Solution; Market Opportunity; Founder &amp; Team; Business Model &amp; Commercialisation; Innovation &amp; Impact; "
        "Financials &amp; Incubation Support) assess the 81 LaunchIndex domain criteria in bounded batches of at most three criteria, citing only evidence shown to them; "
        "cited evidence is validated against the startup's evidence records. Cover criteria CM-01..CM-06 are assessed deterministically from extracted and intake data. "
        "A supervisory reviewer runs only when all six domains completed without missing, duplicate or unknown criteria. The report is accepted only after strict "
        "87-criterion validation.", body))
    if is_mock:
        story.append(Paragraph(f"<b>{escape(MOCK_DISCLOSURE)}.</b> In this run every model response came from the offline MockAIGateway: no external AI provider was called and no cost was incurred. The workflow, persistence, validation and report generation are the production code paths.", body))
    story.append(Paragraph("Appendix B. Evidence References", h1))
    all_ids = sorted({e for d in results.get("domains", []) for c in d.get("criteria", []) for e in c.get("evidence_ids") or []}
                     | {e for c in cover_criteria for e in c.get("evidence_ids") or []})
    recs = evidence_records(db, run.startup_id, all_ids) if all_ids else []
    ev_rows = [["Evidence ID", "Document", "Page / section", "Passage"]]
    for r in recs[:120]:
        ev_rows.append([_t(r["evidence_id"]), _t(r.get("document") or "—", 40), _t(f"p.{r.get('page_number') or '—'} {r.get('section_name') or ''}", 40), _t(r.get("snippet") or "—", 260)])
    if len(ev_rows) == 1:
        ev_rows.append(["—", "—", "—", "No document evidence was cited."])
    story.append(table(ev_rows, [42 * mm, 34 * mm, 24 * mm, 70 * mm], font=6.6))

    # Canvas with "Page X of Y", running header/footer ---------------------------------------
    header_text = f"TIDES-AI Due-Diligence · {st.startup_name if st else ''} · Evaluation {run.id[:8]}"

    class NumberedCanvas(rl_canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved = []

        def showPage(self):
            self._saved.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._saved)
            for state in self._saved:
                self.__dict__.update(state)
                self._decorate(total)
                super().showPage()
            super().save()

        def _decorate(self, total: int):
            w, h = A4
            self.setFont("Helvetica", 7.5)
            self.setFillColor(MUTED)
            self.drawString(18 * mm, h - 11 * mm, header_text[:110])
            self.drawRightString(w - 18 * mm, 10 * mm, f"Page {self._pageNumber} of {total}")
            self.drawString(18 * mm, 10 * mm, f"Confidential · Generated {generated}")
            if is_mock:
                self.setFillColor(AMBER)
                self.setFont("Helvetica-Bold", 7.5)
                self.drawCentredString(w / 2, h - 16 * mm, MOCK_DISCLOSURE)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=22 * mm, bottomMargin=18 * mm,
        title=f"TIDES-AI Due-Diligence Report - {st.startup_name if st else ''}",
        author="TIDES-AI", subject=("MOCK DEMONSTRATION " if is_mock else "") + "Startup incubation due diligence",
    )
    doc.build(story, canvasmaker=NumberedCanvas)
    return buf.getvalue()
