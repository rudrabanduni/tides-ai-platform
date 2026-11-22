"""End-to-end application workflow through the public API (offline MockAIGateway).

SUBMIT APPLICATION -> UPLOAD + VALIDATE DOCUMENTS -> START EVALUATION -> REAL PIPELINE (extraction,
claims, evidence, six domains, supervisory review, report validation) -> RESULTS -> EVIDENCE -> PDF.

No external provider is called: AI_PROVIDER=mock and no API key is present.
"""

from __future__ import annotations

import io
import uuid
from pathlib import Path

import pypdf
import pytest
from fastapi.testclient import TestClient

from app.core.config import PROJECT_ROOT, get_settings

DECK = PROJECT_ROOT / "demo_fixtures" / "cleanpower_systems_pitch_deck.pdf"
DISCLOSURE = "MOCK DEMONSTRATION — OFFLINE SYNTHETIC RESULTS — NOT A REAL AI EVALUATION"


def _application_payload(name: str = "CleanPower Systems Pvt Ltd") -> dict:
    return {
        "company_name": name,
        "sector": "CleanTech",
        "industry": "Stationary energy / backup power",
        "stage": "Seed",
        "location": "Roorkee, Uttarakhand, India",
        "website": "https://cleanpower.example",
        "contact_name": "Dr. Arjun Sharma",
        "contact_email": "founders@cleanpower.example",
        "contact_phone": "+91 00000 00000",
        "founders": [
            {"name": "Dr. Arjun Sharma", "role_in_startup": "Co-Founder & CEO", "email": "arjun@cleanpower.example"},
            {"name": "Priya Mehta", "role_in_startup": "Co-Founder & CTO"},
        ],
        "problem_statement": "Grid outages force telecom towers and edge data centres onto diesel generators.",
        "proposed_solution": "Containerised 10 kW PEM fuel-cell units with remote monitoring.",
        "product_technology": "Low-platinum PEM stack with in-house power electronics.",
        "target_market": "Telecom tower and edge data-centre operators in North India.",
        "business_model": "Power-as-a-service contracts plus hardware sales.",
        "traction": "Three pilot sites; one letter of intent.",
        "revenue_information": "Pre-revenue.",
        "financial_information": "INR 25 lakh grant; INR 6 lakh monthly operating cost.",
        "funding_requirement": "INR 2 crore seed round.",
        "incubation_support_requirement": "Hydrogen-safe test bay; certification mentorship.",
        "declarations": {
            "information_accurate": True,
            "consent_to_evaluation": True,
            "documents_owned_or_authorised": True,
            "synthetic_demo_data": True,
        },
    }


@pytest.fixture()
def api(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.setenv("AI_ENABLED", "false")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")
    monkeypatch.setenv("EVALUATION_RUNNER_MODE", "inline")
    get_settings.cache_clear()
    from app.api.main import create_app
    from app.db import session as session_module
    from app.modules.users.service import UserService

    with session_module.SessionLocal() as db:
        from app.core.enums import RoleName
        from app.modules.users.schemas import UserCreate

        email = f"analyst-{uuid.uuid4().hex[:6]}@tides.ai"
        UserService(db).ensure_default_roles()
        UserService(db).create_user(
            UserCreate(name="Workflow Analyst", email=email, password="Workflow-Test-Pass-91!", role=RoleName.ANALYST),
            actor_id=None,
        )
    client = TestClient(create_app())
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "Workflow-Test-Pass-91!"})
    assert res.status_code == 200, res.text
    client.headers.update({"Authorization": f"Bearer {res.json()['access_token']}"})
    return client


def _upload(client: TestClient, app_id: str, name: str, data: bytes, ctype: str = "application/pdf"):
    return client.post(
        f"/api/v1/applications/{app_id}/documents",
        data={"document_type": "pitch_deck"},
        files={"file": (name, data, ctype)},
    )


def test_full_application_to_validated_pdf_workflow(api: TestClient) -> None:
    # 1. Validation: declarations are mandatory
    bad = _application_payload()
    bad["declarations"]["consent_to_evaluation"] = False
    assert api.post("/api/v1/applications", json=bad).status_code == 422

    # 2. Submission is persisted once, retries are idempotent
    key = f"idem-{uuid.uuid4().hex}"
    first = api.post("/api/v1/applications", json=_application_payload(), headers={"Idempotency-Key": key})
    assert first.status_code == 201, first.text
    app_data = first.json()
    assert app_data["application_ref"].startswith("TIDES-")
    assert app_data["is_synthetic"] is True
    assert len(app_data["founders"]) == 2
    again = api.post("/api/v1/applications", json=_application_payload(), headers={"Idempotency-Key": key})
    assert again.status_code == 200 and again.json()["id"] == app_data["id"]
    app_id = app_data["id"]

    # 3. Evaluation cannot start without documents
    no_docs = api.post(f"/api/v1/applications/{app_id}/evaluations")
    assert no_docs.status_code in (400, 422)

    # 4. Upload validation: executable disguised as PDF, corrupt PDF, empty file, path traversal name
    assert _upload(api, app_id, "deck.pdf", b"MZ\x90\x00 fake executable").status_code in (400, 422)
    assert _upload(api, app_id, "deck.pdf", b"%PDF-1.4 not really a pdf").status_code in (400, 422)
    assert _upload(api, app_id, "deck.pdf", b"").status_code in (400, 422)
    assert _upload(api, app_id, "malware.exe", b"MZ\x90").status_code in (400, 422)
    ok = _upload(api, app_id, "..\\..\\evil:stream.pdf", DECK.read_bytes())
    assert ok.status_code == 201, ok.text
    assert ok.json()["original_filename"] == "evil_stream.pdf"
    stored = list((Path(get_settings().upload_dir)).rglob("*.pdf"))
    assert all(":" not in p.name and ".." not in p.name for p in stored)

    # 5. Start evaluation (inline runner executes the real pipeline with MockAIGateway)
    started = api.post(f"/api/v1/applications/{app_id}/evaluations")
    assert started.status_code == 202, started.text
    run = started.json()
    assert run["mode"] == "MOCK_DEMONSTRATION"
    assert run["disclosure"] == DISCLOSURE

    progress = api.get(f"/api/v1/evaluation-runs/{run['id']}").json()
    assert progress["status"] == "COMPLETED", progress.get("error_message")
    assert progress["progress_pct"] == 100
    stage_status = {s["key"]: s["status"] for s in progress["stages"]}
    assert all(v == "SUCCESS" for v in stage_status.values()), stage_status
    assert sum(1 for k in stage_status if k.startswith("extraction:")) == 10
    assert sum(1 for k in stage_status if k.startswith("domain:")) == 6
    assert progress["cost_usd"] == 0.0

    # Retrying the start request does not create a duplicate run
    again_run = api.post(f"/api/v1/applications/{app_id}/evaluations")
    assert again_run.status_code == 200 and again_run.json()["id"] == run["id"]

    # 6. Results: six domains, 81 + 6 = 87 criteria, supervisory review, validation
    results = api.get(f"/api/v1/evaluation-runs/{run['id']}/results").json()
    assert results["disclosure"] == DISCLOSURE
    assert [d["status"] for d in results["domains"]] == ["COMPLETED"] * 6
    assert sum(len(d["criteria"]) for d in results["domains"]) == 81
    assert len(results["cover_criteria"]) == 6
    cov = results["coverage"]
    assert cov["complete"] is True
    assert cov["total_present"] == cov["total_expected"] == 87
    assert cov["duplicates"] == [] and cov["unknown"] == [] and cov["missing"] == []
    assert results["validation"]["valid"] is True, results["validation"]
    ws = results["weighted_score"]
    assert ws["overall_score_10"] is not None and 0 <= ws["overall_score_10"] <= 10
    assert ws["standard_status"] == "TAES_V1_DEFAULT"
    assert isinstance(results["red_flags"], list)
    assert len(ws["sections"]) == 6 and ws["standard_version"]
    sup = results["supervisory"]
    assert sup["status"] == "COMPLETED"
    assert sup["committee_recommendation"]
    assert len(sup["domains_cited"]) == 6

    # Evidence classes are honest: documentary evidence only with real cited evidence
    all_criteria = [c for d in results["domains"] for c in d["criteria"]]
    documentary = [c for c in all_criteria if c["evidence_class"] == "DOCUMENTARY_EVIDENCE"]
    assert documentary, "the synthetic deck must yield documented criteria"
    assert all(c["evidence_ids"] for c in documentary)
    assert not any(c["evidence_class"] == "INDEPENDENTLY_VERIFIED" for c in all_criteria)
    assert all(str(c["rationale"]).startswith("MOCK:") or "Applicant-reported" in str(c["rationale"]) for c in all_criteria)

    # 7. Evidence inspection returns the real passage from the deck
    ev_ids = documentary[0]["evidence_ids"]
    evidence = api.get(f"/api/v1/evaluation-runs/{run['id']}/evidence", params={"ids": ",".join(ev_ids)}).json()
    assert evidence and all(e["snippet"] for e in evidence)
    deck_text = "\n".join(p.extract_text() for p in pypdf.PdfReader(str(DECK)).pages)
    flat_deck = " ".join(deck_text.split())
    assert all(" ".join(e["snippet"].split(" / ")[0].split()) in flat_deck for e in evidence)
    assert evidence[0]["document"] == "evil_stream.pdf"

    # 8. PDF report: real PDF, paginated, all sections, disclosure on every page
    pdf = api.get(f"/api/v1/evaluation-runs/{run['id']}/report.pdf")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content[:5] == b"%PDF-"
    reader = pypdf.PdfReader(io.BytesIO(pdf.content))
    assert len(reader.pages) >= 10
    texts = [p.extract_text() for p in reader.pages]
    full = "\n".join(texts)
    for title in ("2. Executive Summary", "10. Criterion-Level Assessments", "15. Risk Register",
                  "19. Supervisory Synthesis", "20. Final Recommendation and Conditions", "Appendix A. Methodology"):
        assert title in full, title
    assert run["id"] in full
    assert app_data["startup_id"] in full
    assert all("MOCK DEMONSTRATION" in t for t in texts), "disclosure must appear on every page"
    assert f"Page 1 of {len(reader.pages)}" in texts[0]
    for cid in ("CM-01", "CM-06", "PS-01", "FI-21"):
        assert cid in full
    # PDF is persisted once and served identically afterwards
    assert api.get(f"/api/v1/evaluation-runs/{run['id']}/report.pdf").content == pdf.content

    # 9. Dashboard reads real records
    dash = api.get("/api/v1/applications-dashboard").json()
    assert dash["total_applications"] >= 1 and dash["completed_evaluations"] >= 1


def test_cross_startup_evidence_isolation_and_incomplete_reports(api: TestClient) -> None:
    a = api.post("/api/v1/applications", json=_application_payload("Isolation Alpha Pvt Ltd")).json()
    b = api.post("/api/v1/applications", json=_application_payload("Isolation Beta Pvt Ltd")).json()
    assert _upload(api, a["id"], "a.pdf", DECK.read_bytes()).status_code == 201
    assert _upload(api, b["id"], "b.pdf", DECK.read_bytes()).status_code == 201
    run_a = api.post(f"/api/v1/applications/{a['id']}/evaluations").json()
    run_b = api.post(f"/api/v1/applications/{b['id']}/evaluations").json()
    res_a = api.get(f"/api/v1/evaluation-runs/{run_a['id']}/results").json()
    ids_a = [e for d in res_a["domains"] for c in d["criteria"] for e in c["evidence_ids"]]
    assert ids_a
    # Evidence of startup A is never returned through startup B's evaluation
    leaked = api.get(f"/api/v1/evaluation-runs/{run_b['id']}/evidence", params={"ids": ",".join(ids_a[:20])}).json()
    assert leaked == []

    # A run that is not COMPLETED never yields a "final" PDF
    from app.db import session as session_module
    from app.modules.applications.models import EvaluationRun

    with session_module.SessionLocal() as db:
        r = db.get(EvaluationRun, run_b["id"])
        r.status = "BLOCKED"
        db.commit()
    assert api.get(f"/api/v1/evaluation-runs/{run_b['id']}/report.pdf").status_code == 409


def test_live_provider_runs_are_refused_from_the_web_app(api: TestClient, monkeypatch) -> None:
    app_data = api.post("/api/v1/applications", json=_application_payload("Live Guard Pvt Ltd")).json()
    assert _upload(api, app_data["id"], "deck.pdf", DECK.read_bytes()).status_code == 201
    monkeypatch.setenv("AI_PROVIDER", "anthropic")
    monkeypatch.setenv("AI_ENABLED", "true")
    get_settings.cache_clear()
    with pytest.MonkeyPatch.context() as mp:
        import litellm

        def _forbidden(*a, **k):  # pragma: no cover - must never be reached
            raise AssertionError("live provider call attempted")

        mp.setattr(litellm, "completion", _forbidden)
        res = api.post(f"/api/v1/applications/{app_data['id']}/evaluations")
    assert res.status_code in (400, 422)
    assert "ALLOW_UI_LIVE_EVALUATIONS" in res.text


def test_rerun_assesses_only_its_own_fresh_extraction(api: TestClient) -> None:
    """Regression (live pilot re-run, 2026-11-23): a second evaluation of the same startup fed the
    specialists the claims of the earlier run as well (72 -> 151 claims). Each run must assess only the
    claims extracted in that run; older claims stay stored for audit but are not re-assessed."""
    app_data = api.post("/api/v1/applications", json=_application_payload("Rerun Scope Pvt Ltd")).json()
    assert _upload(api, app_data["id"], "deck.pdf", DECK.read_bytes()).status_code == 201
    first = api.post(f"/api/v1/applications/{app_data['id']}/evaluations").json()
    second = api.post(f"/api/v1/applications/{app_data['id']}/evaluations", params={"rerun": True}).json()
    assert second["id"] != first["id"]
    run1 = api.get(f"/api/v1/evaluation-runs/{first['id']}").json()
    run2 = api.get(f"/api/v1/evaluation-runs/{second['id']}").json()
    assert run1["status"] == run2["status"] == "COMPLETED"
    assert run2["summary"]["claims_count"] == run1["summary"]["claims_count"]
