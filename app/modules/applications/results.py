"""Read model for a finished evaluation run.

Everything here is derived from persisted artifacts (the evaluation graph written by the
pipeline under uploads/graphs/{evaluation_id}.json and the startup's claims/evidence rows).
Nothing is generated on the fly by a model and nothing is fabricated: missing artifacts are
reported as missing.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.applications.models import ApplicationSubmission, EvaluationRun
from app.modules.evaluation.domains.registry import (
    CANONICAL_DOMAINS,
    CRITERIA_DIRECTORY,
    get_criteria_for_domain,
    get_criterion_metadata,
)
from app.modules.evaluation.scoring import compute_weighted_score
from app.modules.evaluation.evidence_classes import (
    APPLICANT_REPORTED,
    DOCUMENTARY_EVIDENCE,
    MISSING,
    evidence_class_for,
    evidence_class_label,
)

COVER_CRITERIA = ("CM-01", "CM-02", "CM-03", "CM-04", "CM-05", "CM-06")
_SAFE_ID = re.compile(r"^[A-Za-z0-9-]{8,64}$")

DOMAIN_TITLES = {
    "problem_solution": "Problem & Solution",
    "market_opportunity": "Market Opportunity",
    "founder_team": "Founder & Team",
    "commercialisation": "Business Model & Commercialisation",
    "innovation_impact": "Innovation & Impact",
    "financials_support": "Financials & Incubation Support",
}


def graph_path_for(evaluation_id: str) -> Path | None:
    if not _SAFE_ID.match(str(evaluation_id or "")):
        return None
    base = (Path(get_settings().upload_dir) / "graphs").resolve()
    path = (base / f"{evaluation_id}.json").resolve()
    if base not in path.parents:
        return None
    return path


def load_graph_dict(evaluation_id: str) -> dict[str, Any] | None:
    path = graph_path_for(evaluation_id)
    if path is None or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_graph_object(evaluation_id: str):
    path = graph_path_for(evaluation_id)
    if path is None or not path.exists():
        return None
    from app.modules.evaluation.graph.graph_serializer import from_json

    return from_json(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- cover criteria
_COVER_FIELD_PREFIX = {cm: cm.lower().replace("-", "_") for cm in COVER_CRITERIA}


def _claim_value(claim: Any) -> str | None:
    for attr in ("value_string", "value_number", "value_boolean", "value_json", "value_date"):
        val = getattr(claim, attr, None)
        if val is not None and str(val).strip():
            return str(val).strip()
    return None


def build_cover_assessment(db: Session, startup_id: UUID, submission: ApplicationSubmission | None) -> list[dict[str, Any]]:
    """Deterministic CM-01..CM-06 intake-completeness assessment (no model call).

    Documentary evidence when an extracted claim carries a document snippet; applicant-reported
    when only the intake form supplies it; missing otherwise.
    """
    from app.modules.intelligence.models import StartupClaim, StartupEvidence, StartupIntelligenceProfile
    from app.modules.startups.models import StartupApplication

    startup = db.get(StartupApplication, startup_id)
    profile = db.query(StartupIntelligenceProfile).filter(StartupIntelligenceProfile.startup_id == startup_id).first()
    claims = list(db.query(StartupClaim).filter(StartupClaim.profile_id == profile.id).all()) if profile else []
    evidence_by_claim: dict[str, list[Any]] = {}
    if claims:
        for ev in db.query(StartupEvidence).filter(StartupEvidence.claim_id.in_([c.id for c in claims])).all():
            evidence_by_claim.setdefault(str(ev.claim_id), []).append(ev)

    form_values = {
        "CM-01": getattr(startup, "startup_name", None),
        "CM-02": getattr(startup, "solution_summary", None),
        "CM-03": getattr(startup, "sector", None),
        "CM-04": getattr(startup, "stage", None),
        "CM-05": getattr(submission, "location", None) if submission else None,
        "CM-06": (submission.submitted_at.date().isoformat() if submission and submission.submitted_at else None),
    }
    out: list[dict[str, Any]] = []
    for cm in COVER_CRITERIA:
        meta = get_criterion_metadata(cm)
        prefix = _COVER_FIELD_PREFIX[cm]
        claim = next(
            (c for c in claims if str(getattr(getattr(c, "field", None), "field_key", "") or "").lower().startswith(prefix)),
            None,
        )
        extracted = _claim_value(claim) if claim else None
        evs = evidence_by_claim.get(str(claim.id), []) if claim else []
        documented = [e for e in evs if (e.evidence_snippet or "").strip()]
        if extracted and documented:
            cls = DOCUMENTARY_EVIDENCE
            status = "VERIFIED_DOCUMENTED"
        elif extracted or form_values.get(cm):
            cls = APPLICANT_REPORTED
            status = "SELF_REPORTED_ONLY"
        else:
            cls = MISSING
            status = "MISSING_INFORMATION"
        out.append({
            "criterion_id": cm,
            "criterion_name": meta.get("name", cm),
            "value": extracted or form_values.get(cm),
            "source": (
                "document" if (extracted and documented)
                else ("intake form" if form_values.get(cm) else ("applicant statement" if extracted else None))
            ),
            "verification_status": status,
            "evidence_class": cls,
            "evidence_class_label": evidence_class_label(cls),
            "evidence_ids": [str(e.id) for e in documented][:3],
            "score": None,
        })
    return out


# --------------------------------------------------------------------------- red flags (TAES)
def _number(text: Any) -> float | None:
    m = re.search(r"-?\d+(?:\.\d+)?", str(text or "").replace(",", ""))
    return float(m.group(0)) if m else None


def build_red_flags(db: Session, startup_id: UUID) -> list[dict[str, Any]]:
    """Deterministic TAES red-flag checks on the startup's own extracted claims.

    Flags are for committee attention only; none is an automatic rejection.
    """
    from app.modules.intelligence.models import StartupClaim, StartupIntelligenceProfile

    profile = db.query(StartupIntelligenceProfile).filter(StartupIntelligenceProfile.startup_id == startup_id).first()
    if not profile:
        return []
    values: dict[str, Any] = {}
    for c in db.query(StartupClaim).filter(StartupClaim.profile_id == profile.id).all():
        key = str(getattr(getattr(c, "field", None), "field_key", "") or "")
        val = c.value_json if c.value_json is not None else _claim_value(c)
        if key and val is not None:
            values.setdefault(key, val)

    flags: list[dict[str, Any]] = []
    trl = _number(values.get("ps_09_current_trl"))
    revenue_raw = values.get("bc_09_current_revenue")
    revenue_text = str(revenue_raw or "").lower()
    pre_revenue = revenue_raw is not None and (
        _number(revenue_raw) == 0 or any(t in revenue_text for t in ("pre-revenue", "pre revenue", "nil", "none", "no revenue"))
    )
    if trl is not None and trl >= 8 and pre_revenue:
        flags.append({
            "id": "TRL_GAMING",
            "rule": "Pre-revenue startup claiming TRL 8-9",
            "finding": f"Claimed TRL {trl:g} with current revenue reported as '{revenue_raw}'.",
            "action": "Committee to investigate the TRL claim (not an automatic rejection).",
            "criteria": ["PS-09", "BC-09"],
        })

    founders = values.get("ft_01_founder_details")
    if isinstance(founders, list) and founders:
        equities = [_number(f.get("equity_percentage")) for f in founders if isinstance(f, dict)]
        if equities and all(e is not None for e in equities):
            total = sum(equities)
            if total < 50:
                flags.append({
                    "id": "FOUNDER_EQUITY_BELOW_50",
                    "rule": "Combined founder equity below 50%",
                    "finding": f"Founders together hold {total:g}% equity.",
                    "action": "Review dilution and governance (not an automatic rejection).",
                    "criteria": ["FT-01", "FT-06"],
                })
    return flags


# --------------------------------------------------------------------------- domains
def build_domains(graph: dict[str, Any]) -> list[dict[str, Any]]:
    reports = graph.get("domain_reports") or {}
    domains: list[dict[str, Any]] = []
    for dkey in CANONICAL_DOMAINS:
        rep = reports.get(dkey)
        owned = get_criteria_for_domain(dkey)
        if not isinstance(rep, dict):
            domains.append({
                "key": dkey, "title": DOMAIN_TITLES.get(dkey, dkey), "status": "MISSING",
                "criteria_total": len(owned), "criteria_assessed": 0, "criteria": [],
            })
            continue
        evals = rep.get("criteria_evaluations") or {}
        failed = "incomplete" in str(rep.get("summary", "")).lower() or float(rep.get("composite_domain_confidence") or 0) == 0.0
        criteria = []
        for cid in owned:
            ce = evals.get(cid)
            if not isinstance(ce, dict):
                continue
            cls = evidence_class_for(ce.get("verification_status"), ce.get("external_research_sources"))
            criteria.append({
                "criterion_id": cid,
                "criterion_name": ce.get("criterion_name") or get_criterion_metadata(cid).get("name", cid),
                "score": ce.get("score"),
                "verification_status": ce.get("verification_status"),
                "evidence_class": cls,
                "evidence_class_label": evidence_class_label(cls),
                "evidence_ids": list(ce.get("evidence_ids") or []),
                "rationale": ce.get("assessment_narrative"),
                "missing_information": ce.get("confidence_limitations") if cls in (MISSING, APPLICANT_REPORTED) else None,
                "applicant_response": ce.get("extracted_startup_response"),
                "source_locations": list(ce.get("source_locations") or []),
                "confidence": ce.get("confidence_score"),
            })
        scored = [c["score"] for c in criteria if isinstance(c.get("score"), (int, float))]
        domains.append({
            "key": dkey,
            "title": DOMAIN_TITLES.get(dkey, rep.get("domain_title") or dkey),
            "status": "FAILED" if failed else "COMPLETED",
            "criteria_total": len(owned),
            "criteria_assessed": len(criteria),
            "average_score": round(sum(scored) / len(scored), 2) if scored else None,
            "confidence": rep.get("composite_domain_confidence"),
            "summary": rep.get("summary"),
            "executive_conclusion": rep.get("executive_conclusion"),
            "strengths": list(rep.get("strengths") or []),
            "weaknesses": list(rep.get("weaknesses") or []),
            "contradictions": list(rep.get("contradictions") or []),
            "missing_information": list(rep.get("missing_information") or []),
            "risks": [
                {k: r.get(k) for k in ("id", "category", "severity", "description", "mitigation")}
                for r in (rep.get("risks") or []) if isinstance(r, dict)
            ],
            "questions": [q.get("question") for q in (rep.get("questions") or []) if isinstance(q, dict)],
            "model_used": rep.get("model_used"),
            "cost_usd": rep.get("cost_usd"),
            "criteria": criteria,
        })
    return domains


def build_coverage(domains: list[dict[str, Any]], cover: list[dict[str, Any]]) -> dict[str, Any]:
    domain_ids: list[str] = [c["criterion_id"] for d in domains for c in d["criteria"]]
    expected_domain = [cid for dkey in CANONICAL_DOMAINS for cid in get_criteria_for_domain(dkey)]
    duplicates = sorted({c for c in domain_ids if domain_ids.count(c) > 1})
    unknown = sorted(set(domain_ids) - set(CRITERIA_DIRECTORY))
    missing = [c for c in expected_domain if c not in domain_ids]
    cover_ids = [c["criterion_id"] for c in cover]
    by_class: dict[str, int] = {}
    for c in [*(c for d in domains for c in d["criteria"]), *cover]:
        by_class[c["evidence_class"]] = by_class.get(c["evidence_class"], 0) + 1
    complete = (
        not missing and not duplicates and not unknown
        and sorted(cover_ids) == sorted(COVER_CRITERIA)
        and all(d["status"] == "COMPLETED" for d in domains)
    )
    return {
        "domain_criteria_expected": len(expected_domain),
        "domain_criteria_present": len(set(domain_ids) & set(expected_domain)),
        "cover_criteria_expected": len(COVER_CRITERIA),
        "cover_criteria_present": len(set(cover_ids)),
        "total_expected": len(CRITERIA_DIRECTORY),
        "total_present": len(set(domain_ids) & set(expected_domain)) + len(set(cover_ids)),
        "missing": missing,
        "duplicates": duplicates,
        "unknown": unknown,
        "domains_completed": sum(1 for d in domains if d["status"] == "COMPLETED"),
        "evidence_classes": by_class,
        "complete": complete,
    }


# --------------------------------------------------------------------------- supervisory
def build_supervisory(graph: dict[str, Any], domains: list[dict[str, Any]]) -> dict[str, Any]:
    """Institutional synthesis: model-authored supervisory fields + deterministic, cited
    roll-ups of the six domain assessments."""
    final = graph.get("final_review") or {}
    sup = graph.get("supervisory_review") or {}
    if not isinstance(final, dict):
        final = {}
    if not final and not sup:
        return {"status": "NOT_RUN"}

    def _cite(domain: dict[str, Any], crit: dict[str, Any], text: str) -> dict[str, Any]:
        return {
            "text": text,
            "domain": domain["key"],
            "criterion_id": crit["criterion_id"],
            "evidence_ids": crit["evidence_ids"][:3],
        }

    strengths, weaknesses, missing = [], [], []
    for d in domains:
        for c in d["criteria"]:
            score = c.get("score")
            if c["evidence_class"] == DOCUMENTARY_EVIDENCE and isinstance(score, (int, float)) and score >= 7.0:
                strengths.append(_cite(d, c, f"{c['criterion_name']} ({score}/10, documentary evidence)"))
            elif isinstance(score, (int, float)) and score < 5.0:
                weaknesses.append(_cite(d, c, f"{c['criterion_name']} scored {score}/10 ({c['evidence_class_label']})"))
            if c["evidence_class"] == MISSING:
                missing.append(_cite(d, c, f"{c['criterion_name']}: not provided"))
    strengths.sort(key=lambda x: x["criterion_id"])

    def _domain_risks(keys: tuple[str, ...]) -> list[dict[str, Any]]:
        out = []
        for d in domains:
            if d["key"] in keys:
                for r in d.get("risks", []):
                    out.append({**r, "domain": d["key"]})
        return out[:8]

    team = next((d for d in domains if d["key"] == "founder_team"), None)
    team_obs = []
    if team:
        for c in team["criteria"][:13]:
            if c["evidence_class"] in (DOCUMENTARY_EVIDENCE, APPLICANT_REPORTED):
                team_obs.append(_cite(team, c, f"{c['criterion_name']}: {c['evidence_class_label']}"))

    contradictions = []
    for item in final.get("identified_contradictions") or []:
        contradictions.append(item if isinstance(item, dict) else {"description": str(item)})
    for d in domains:
        for text in d.get("contradictions", []):
            contradictions.append({"description": text, "domain": d["key"]})

    support = []
    fin = next((d for d in domains if d["key"] == "financials_support"), None)
    if fin:
        for c in fin["criteria"]:
            if c["criterion_id"] in ("FI-10", "FI-11", "FI-12", "FI-13", "FI-14", "FI-15") and c.get("applicant_response"):
                support.append(_cite(fin, c, f"{c['criterion_name']}: {str(c['applicant_response'])[:160]}"))

    founder_clarifications = [m["text"] for m in missing[:6]] + [
        f"Provide supporting documents for {c['criterion_id']} ({c['criterion_name']})"
        for d in domains for c in d["criteria"] if c["evidence_class"] == APPLICANT_REPORTED
    ][:6]

    return {
        "status": "COMPLETED" if final else "PARTIAL",
        "overall_diligence_position": final.get("executive_summary") or sup.get("recommendation_rationale"),
        "committee_recommendation": final.get("overall_recommendation") or sup.get("overall_recommendation"),
        "recommendation_rationale": final.get("recommendation_rationale") or sup.get("recommendation_rationale"),
        "confidence": final.get("confidence_score") or sup.get("confidence_score"),
        "major_strengths": strengths[:8],
        "material_weaknesses": weaknesses[:8],
        "contradictions": contradictions[:8],
        "missing_evidence": missing[:10],
        "financial_and_technical_risks": _domain_risks(("financials_support", "problem_solution", "innovation_impact")),
        "market_risks": _domain_risks(("market_opportunity", "commercialisation")),
        "team_capability_observations": team_obs[:8],
        "priority_diligence_questions": list(final.get("unresolved_questions") or [])[:8]
        or [q for d in domains for q in d.get("questions", [])][:8],
        "required_founder_clarifications": founder_clarifications[:8],
        "recommended_incubation_support": support[:6],
        "conditional_requirements": list(final.get("incubation_conditions") or [])[:6],
        "cross_domain_findings": list(final.get("cross_domain_findings") or [])[:8],
        "domains_cited": [d["key"] for d in domains if d["status"] == "COMPLETED"],
    }


# --------------------------------------------------------------------------- validation
def validate_run_report(run: EvaluationRun) -> dict[str, Any]:
    graph = load_graph_object(run.id)
    if graph is None or not getattr(graph, "report", None):
        return {"valid": False, "errors": ["No persisted due-diligence report for this evaluation."], "warnings": []}
    from app.modules.evaluation.report.report_validator import ReportValidator

    res = ReportValidator.validate_canonical_87_report(graph)
    return {
        "valid": bool(res.get("valid")),
        "errors": [e.get("message") if isinstance(e, dict) else str(e) for e in res.get("errors", [])][:25],
        "warnings": [w.get("message") if isinstance(w, dict) else str(w) for w in res.get("warnings", [])][:25],
    }


def build_run_summary(db: Session, run: EvaluationRun) -> dict[str, Any]:
    graph = load_graph_dict(run.id)
    if graph is None:
        return {"coverage": {"complete": False}, "validation": {"valid": False, "errors": ["Evaluation graph not found."]}}
    sub = db.query(ApplicationSubmission).filter(ApplicationSubmission.startup_id == run.startup_id).first()
    domains = build_domains(graph)
    cover = build_cover_assessment(db, run.startup_id, sub)
    coverage = build_coverage(domains, cover)
    supervisory = build_supervisory(graph, domains)
    validation = validate_run_report(run)
    claims = graph.get("claims") or {}
    evidence = graph.get("evidence") or {}
    weighted = compute_weighted_score(domains)
    return {
        "coverage": coverage,
        "validation": validation,
        "weighted_score": {k: weighted[k] for k in ("standard_version", "standard_status", "overall_score_pct", "overall_score_10", "recommendation")},
        "red_flags": [f["id"] for f in build_red_flags(db, run.startup_id)],
        "supervisory_status": supervisory.get("status"),
        "committee_recommendation": supervisory.get("committee_recommendation"),
        "domain_status": {d["key"]: d["status"] for d in domains},
        "claims_count": len(claims) if hasattr(claims, "__len__") else None,
        "evidence_count": len(evidence) if hasattr(evidence, "__len__") else None,
    }


def build_run_results(db: Session, run: EvaluationRun) -> dict[str, Any]:
    graph = load_graph_dict(run.id)
    sub = db.query(ApplicationSubmission).filter(ApplicationSubmission.startup_id == run.startup_id).first()
    if graph is None:
        return {"available": False, "evaluation_id": run.id, "status": run.status}
    domains = build_domains(graph)
    cover = build_cover_assessment(db, run.startup_id, sub)
    report = graph.get("report") or {}
    return {
        "available": True,
        "evaluation_id": run.id,
        "startup_id": str(run.startup_id),
        "startup_name": graph.get("startup_name"),
        "status": run.status,
        "mode": run.mode,
        "report_id": report.get("report_id") if isinstance(report, dict) else None,
        "domains": domains,
        "cover_criteria": cover,
        "coverage": build_coverage(domains, cover),
        "weighted_score": compute_weighted_score(domains),
        "red_flags": build_red_flags(db, run.startup_id),
        "supervisory": build_supervisory(graph, domains),
        "validation": (run.summary or {}).get("validation") or validate_run_report(run),
    }


def evidence_records(db: Session, startup_id: UUID, evidence_ids: list[str]) -> list[dict[str, Any]]:
    """Evidence lookup strictly scoped to one startup (cross-startup isolation)."""
    from app.modules.documents.models import Document
    from app.modules.intelligence.models import StartupClaim, StartupEvidence, StartupIntelligenceProfile

    ids: list[UUID] = []
    for raw in evidence_ids[:100]:
        try:
            ids.append(UUID(str(raw)))
        except ValueError:
            continue
    if not ids:
        return []
    rows = (
        db.query(StartupEvidence, StartupClaim)
        .join(StartupClaim, StartupClaim.id == StartupEvidence.claim_id)
        .join(StartupIntelligenceProfile, StartupIntelligenceProfile.id == StartupClaim.profile_id)
        .filter(StartupIntelligenceProfile.startup_id == startup_id, StartupEvidence.id.in_(ids))
        .all()
    )
    doc_names = {}
    doc_ids = [ev.source_document_id for ev, _ in rows if ev.source_document_id]
    if doc_ids:
        for d in db.query(Document).filter(Document.id.in_(doc_ids), Document.startup_id == startup_id).all():
            doc_names[d.id] = d.original_filename
    out = []
    for ev, claim in rows:
        out.append({
            "evidence_id": str(ev.id),
            "document": doc_names.get(ev.source_document_id),
            "page_number": ev.page_number,
            "section_name": ev.section_name,
            "snippet": ev.evidence_snippet,
            "confidence": ev.confidence_score,
            "claim_field": getattr(getattr(claim, "field", None), "field_key", None),
            "claim_value": _claim_value(claim),
        })
    return out
