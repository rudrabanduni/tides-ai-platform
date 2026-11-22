"""Weighted scoring from the TIDES scoring standard (section weightage, missing policy, thresholds)."""

from __future__ import annotations

import copy

import pytest

from app.modules.evaluation.scoring import (
    CANONICAL_SECTIONS,
    ScoringStandardError,
    compute_weighted_score,
    load_standard,
    validate_standard,
)


def _domains(scores_by_section: dict[str, list]) -> list[dict]:
    out = []
    for key in CANONICAL_SECTIONS:
        crits = []
        for i, sc in enumerate(scores_by_section.get(key, [])):
            crits.append({
                "criterion_id": f"{key[:2].upper()}-{i + 1:02d}",
                "score": sc,
                "evidence_class": "MISSING" if sc is None else "DOCUMENTARY_EVIDENCE",
            })
        out.append({"key": key, "title": key, "criteria": crits})
    return out


def _standard(**overrides) -> dict:
    std = {
        "version": "test-1",
        "status": "APPROVED",
        "score_scale_max": 10,
        "section_weights": {k: 0 for k in CANONICAL_SECTIONS},
        "criterion_weights": {},
        "missing_policy": "exclude",
        "decision_thresholds": [],
        "knockout_rules": [],
    }
    std.update(overrides)
    return std


def test_shipped_standard_is_taes_v1_default_mapping():
    std = load_standard()
    assert std["status"] == "TAES_V1_DEFAULT"
    assert std["score_scale_max"] == 10
    assert std["decision_thresholds"] == []  # TAES defines no cut-offs; committee decides
    assert std["missing_policy"] == "zero_required"
    # TAES pillars (Founder 18, Product 16, Technology 14, Market 14, Business Model 12, Financial 10,
    # IP 8) mapped to six sections and the 8% Risk pillar redistributed proportionally (/0.92).
    pillars = std["taes_pillar_weights"]
    assert sum(pillars.values()) == 100
    expected = {
        "problem_solution": (pillars["product"] + pillars["technology"]) / 0.92,
        "founder_team": pillars["founder"] / 0.92,
        "market_opportunity": pillars["market"] / 0.92,
        "commercialisation": pillars["business_model"] / 0.92,
        "financials_support": pillars["financial"] / 0.92,
        "innovation_impact": pillars["ip"] / 0.92,
    }
    for key, value in expected.items():
        assert abs(std["section_weights"][key] - value) < 0.001, key
    assert abs(sum(std["section_weights"].values()) - 100) < 0.01


def test_zero_required_penalises_missing_mandatory_but_not_optional_or_conditional():
    weights = {k: 0 for k in CANONICAL_SECTIONS}
    weights["financials_support"] = 100
    std = _standard(section_weights=weights, missing_policy="zero_required")
    domains = [{
        "key": "financials_support", "title": "Financials",
        "criteria": [
            {"criterion_id": "FI-01", "score": 8, "evidence_class": "DOCUMENTARY_EVIDENCE"},
            {"criterion_id": "FI-05", "score": None, "evidence_class": "MISSING"},   # required -> 0
            {"criterion_id": "FI-08", "score": None, "evidence_class": "MISSING"},   # optional/conditional -> excluded
            {"criterion_id": "FI-15", "score": None, "evidence_class": "MISSING"},   # optional -> excluded
        ],
    }]
    result = compute_weighted_score(domains, std)
    # (8 + 0) / (2 * 10) = 40%
    assert result["overall_score_pct"] == 40.0
    assert result["overall_score_10"] == 4.0
    sec = next(s for s in result["sections"] if s["key"] == "financials_support")
    assert sec["criteria_scored"] == 2 and sec["criteria_not_scored"] == 2


def test_weights_must_cover_all_sections_and_sum_to_100():
    with pytest.raises(ScoringStandardError, match="add up to 100"):
        validate_standard(_standard(section_weights={k: 10 for k in CANONICAL_SECTIONS}))
    partial = {k: 20 for k in CANONICAL_SECTIONS[:5]}
    with pytest.raises(ScoringStandardError, match="cover all six"):
        validate_standard(_standard(section_weights=partial))
    with pytest.raises(ScoringStandardError, match="Unknown sections"):
        validate_standard(_standard(section_weights={**{k: 0 for k in CANONICAL_SECTIONS}, "marketing": 100}))


def test_section_weightage_drives_the_overall_score():
    weights = {k: 0 for k in CANONICAL_SECTIONS}
    weights.update({"founder_team": 60, "market_opportunity": 40})
    std = _standard(section_weights=weights)
    result = compute_weighted_score(_domains({"founder_team": [10, 10], "market_opportunity": [5, 5]}), std)
    # 0.6 * 100% + 0.4 * 50% = 80%
    assert result["overall_score_pct"] == 80.0
    founder = next(s for s in result["sections"] if s["key"] == "founder_team")
    assert founder["score_pct"] == 100.0 and founder["weighted_contribution"] == 60.0


def test_missing_policy_exclude_vs_zero():
    weights = {k: 0 for k in CANONICAL_SECTIONS}
    weights["problem_solution"] = 100
    domains = _domains({"problem_solution": [8, None]})
    excl = compute_weighted_score(domains, _standard(section_weights=weights, missing_policy="exclude"))
    zero = compute_weighted_score(domains, _standard(section_weights=copy.deepcopy(weights), missing_policy="zero"))
    assert excl["overall_score_pct"] == 80.0
    assert excl["sections"][0]["criteria_not_scored"] == 1
    assert zero["overall_score_pct"] == 40.0


def test_criterion_weights_within_a_section():
    weights = {k: 0 for k in CANONICAL_SECTIONS}
    weights["problem_solution"] = 100
    std = _standard(section_weights=weights, criterion_weights={"problem_solution": {"PR-01": 3, "PR-02": 1}})
    result = compute_weighted_score(_domains({"problem_solution": [10, 2]}), std)
    # (3*10 + 1*2) / (4*10) = 80%
    assert result["overall_score_pct"] == 80.0


def test_decision_thresholds_pick_the_highest_band_reached():
    weights = {k: 100 / 6 for k in CANONICAL_SECTIONS}
    weights["financials_support"] = 100 - sum(v for k, v in weights.items() if k != "financials_support")
    std = _standard(section_weights=weights, decision_thresholds=[
        {"min": 75, "label": "Incubate"}, {"min": 55, "label": "Conditional"}, {"min": 0, "label": "Reject"},
    ])
    high = compute_weighted_score(_domains({k: [8] for k in CANONICAL_SECTIONS}), std)
    mid = compute_weighted_score(_domains({k: [6] for k in CANONICAL_SECTIONS}), std)
    low = compute_weighted_score(_domains({k: [3] for k in CANONICAL_SECTIONS}), std)
    assert (high["recommendation"], mid["recommendation"], low["recommendation"]) == ("Incubate", "Conditional", "Reject")


def test_no_scores_gives_no_overall_score():
    result = compute_weighted_score(_domains({}), load_standard())
    assert result["overall_score_pct"] is None
    assert result["recommendation"] is None


def test_red_flags_trl_gaming_and_founder_equity():
    import uuid as _uuid

    from app.db import session as session_module
    from app.modules.applications.results import build_red_flags
    from app.modules.intelligence.models import KnowledgeFieldRegistry, StartupClaim, StartupIntelligenceProfile
    from app.modules.startups.models import StartupApplication

    with session_module.SessionLocal() as db:
        startup = StartupApplication(startup_name=f"Flag Co {_uuid.uuid4().hex[:6]}", sector="DeepTech", stage="Seed")
        db.add(startup); db.flush()
        profile = StartupIntelligenceProfile(startup_id=startup.id)
        db.add(profile); db.flush()

        def field(key, vtype):
            f = db.query(KnowledgeFieldRegistry).filter_by(field_key=key).first()
            if not f:
                f = KnowledgeFieldRegistry(field_key=key, field_name=key, value_type=vtype, is_active=True)
                db.add(f); db.flush()
            return f

        def claim(key, vtype, **value):
            db.add(StartupClaim(profile_id=profile.id, field_id=field(key, vtype).id, confidence_score=0.9,
                                validation_status="PENDING", is_preferred=True, **value))

        claim("ps_09_current_trl", "number", value_number=8.0)
        claim("bc_09_current_revenue", "string", value_string="INR 0")
        claim("ft_01_founder_details", "json", value_json=[
            {"name": "A", "equity_percentage": "20%"}, {"name": "B", "equity_percentage": "15%"},
        ])
        db.commit()
        flags = {f["id"]: f for f in build_red_flags(db, startup.id)}
    assert set(flags) == {"TRL_GAMING", "FOUNDER_EQUITY_BELOW_50"}
    assert "35" in flags["FOUNDER_EQUITY_BELOW_50"]["finding"]
    assert "not an automatic rejection" in flags["TRL_GAMING"]["action"]
