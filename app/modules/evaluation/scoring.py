"""scoring.py - Weighted final score from the TIDES scoring standard.

The standard (`scoring_standard.json`) is the single place that holds TIDES' "golden rules":
section weightage, optional per-criterion weights, missing-information policy, decision thresholds
and knockout rules. It is versioned and stamped onto every result and PDF.

Computation (deterministic, no model call):
  criterion score  : 0..score_scale_max as given by the domain specialist (None = not scored)
  section score    : weighted mean of its scored criteria, as a percentage of the scale
                     (criterion weights default to equal)
  missing policy   : "exclude"       -> unscored criteria are left out of the mean and reported
                     "zero"          -> every criterion with MISSING information counts as 0
                     "zero_required" -> MISSING required (non-conditional) criteria count as 0;
                                        optional, conditional and not-applicable ones are excluded
  overall score    : sum(section_weight x section score) / sum(weights of sections with a score)
  recommendation   : first threshold whose `min` the overall score reaches (highest first);
                     knockout rules can cap the recommendation.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

STANDARD_PATH = Path(__file__).with_name("scoring_standard.json")
CANONICAL_SECTIONS = (
    "problem_solution",
    "market_opportunity",
    "founder_team",
    "commercialisation",
    "innovation_impact",
    "financials_support",
)


class ScoringStandardError(ValueError):
    pass


def validate_standard(std: dict[str, Any]) -> dict[str, Any]:
    weights = std.get("section_weights") or {}
    unknown = set(weights) - set(CANONICAL_SECTIONS)
    if unknown:
        raise ScoringStandardError(f"Unknown sections in section_weights: {sorted(unknown)}")
    missing = [s for s in CANONICAL_SECTIONS if s not in weights]
    if missing:
        raise ScoringStandardError(f"section_weights must cover all six sections; missing {missing}")
    total = sum(float(v) for v in weights.values())
    if abs(total - 100.0) > 0.1:
        raise ScoringStandardError(f"section_weights must add up to 100 (got {total:.2f})")
    if any(float(v) < 0 for v in weights.values()):
        raise ScoringStandardError("section weights cannot be negative")
    if std.get("missing_policy", "exclude") not in ("exclude", "zero", "zero_required"):
        raise ScoringStandardError("missing_policy must be 'exclude', 'zero' or 'zero_required'")
    thresholds = std.get("decision_thresholds") or []
    for t in thresholds:
        if "min" not in t or "label" not in t:
            raise ScoringStandardError("each decision threshold needs 'min' and 'label'")
    if float(std.get("score_scale_max", 10)) <= 0:
        raise ScoringStandardError("score_scale_max must be positive")
    return std


@lru_cache(maxsize=1)
def load_standard() -> dict[str, Any]:
    return validate_standard(json.loads(STANDARD_PATH.read_text(encoding="utf-8")))


def _criterion_weight(std: dict[str, Any], section: str, criterion_id: str) -> float:
    per = (std.get("criterion_weights") or {}).get(section) or {}
    if not per:
        return 1.0
    return float(per.get(criterion_id, 0.0))


def _is_required(criterion_id: str) -> bool:
    from app.modules.evaluation.domains.registry import get_criterion_metadata

    meta = get_criterion_metadata(criterion_id) or {}
    if not isinstance(meta, dict) or not meta:
        return True
    return bool(meta.get("is_required", True)) and not bool(meta.get("is_conditional", False))


def compute_weighted_score(domains: list[dict[str, Any]], std: dict[str, Any] | None = None) -> dict[str, Any]:
    """`domains` is the list produced by applications.results.build_domains()."""
    std = std or load_standard()
    scale = float(std.get("score_scale_max", 10))
    policy = std.get("missing_policy", "exclude")
    weights = {k: float(v) for k, v in (std.get("section_weights") or {}).items()}

    sections = []
    weighted_sum = 0.0
    weight_used = 0.0
    for d in domains:
        key = d["key"]
        num = den = 0.0
        scored = excluded = 0
        for c in d.get("criteria", []):
            w = _criterion_weight(std, key, c["criterion_id"])
            if w <= 0:
                continue
            score = c.get("score")
            if isinstance(score, (int, float)):
                num += w * max(0.0, min(scale, float(score)))
                den += w
                scored += 1
            elif c.get("evidence_class") == "MISSING" and (
                policy == "zero" or (policy == "zero_required" and _is_required(c["criterion_id"]))
            ):
                den += w  # contributes 0 to the numerator
                scored += 1
            else:
                excluded += 1
        pct = round(100.0 * num / (den * scale), 1) if den > 0 else None
        if pct is not None:
            weighted_sum += weights.get(key, 0.0) * pct
            weight_used += weights.get(key, 0.0)
        sections.append({
            "key": key,
            "title": d.get("title", key),
            "weight_pct": weights.get(key, 0.0),
            "score_pct": pct,
            "criteria_scored": scored,
            "criteria_not_scored": excluded,
            "weighted_contribution": round(weights.get(key, 0.0) * pct / 100.0, 2) if pct is not None else None,
        })

    overall = round(weighted_sum / weight_used, 1) if weight_used > 0 else None
    for sec in sections:
        sec["score_10"] = round(sec["score_pct"] * scale / 100.0, 1) if sec["score_pct"] is not None else None
    recommendation = None
    for t in sorted(std.get("decision_thresholds") or [], key=lambda t: float(t["min"]), reverse=True):
        if overall is not None and overall >= float(t["min"]):
            recommendation = t["label"]
            break
    return {
        "standard_version": std.get("version"),
        "standard_status": std.get("status"),
        "standard_source": std.get("source"),
        "missing_policy": policy,
        "overall_score_pct": overall,
        "overall_score_10": round(overall * scale / 100.0, 1) if overall is not None else None,
        "score_scale_max": scale,
        "approved_by": std.get("approved_by"),
        "effective_date": std.get("effective_date"),
        "missing_policy_note": std.get("missing_policy_note"),
        "decision_note": std.get("decision_note"),
        "weight_coverage_pct": round(weight_used, 2),
        "recommendation": recommendation,
        "recommendation_basis": (
            "TIDES decision thresholds" if recommendation
            else ("No score cut-offs: decision by committee with the supervisory review" if not std.get("decision_thresholds") else "Below the lowest threshold")
        ),
        "knockout_rules": list(std.get("knockout_rules") or []),
        "sections": sections,
    }
