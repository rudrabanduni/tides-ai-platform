"""Regression: cover criteria absent from the deck are taken from the intake form (applicant-reported).

A live pilot run (2026-11-23) completed all six domains and the supervisory review but the
strict 87-criterion validator blocked the report: the deck states no geography (CM-05) or submission
date (CM-06), although both were on the submitted application form.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from app.db import session as session_module
from app.modules.ai.orchestrator.pipeline import _fill_cover_metadata_from_intake
from app.modules.applications.models import ApplicationSubmission
from app.modules.startups.models import StartupApplication


def _startup_with_submission(db, location="Roorkee, India"):
    st = StartupApplication(startup_name=f"Cover Co {uuid.uuid4().hex[:6]}", sector="MedTech", stage="Pre-Seed")
    db.add(st)
    db.flush()
    db.add(ApplicationSubmission(
        application_ref=f"TIDES-TEST-{uuid.uuid4().hex[:6].upper()}", startup_id=st.id, location=location,
        declarations={}, submitted_at=datetime(2026, 11, 23, 10, 0, tzinfo=timezone.utc),
    ))
    db.commit()
    return st


def test_missing_cover_fields_are_filled_from_the_intake_form():
    with session_module.SessionLocal() as db:
        st = _startup_with_submission(db)
        extracted = SimpleNamespace(company_name="Deck Co", sector=None, stage="Prototype", geography=None, application_date=None)
        filled = _fill_cover_metadata_from_intake(db, st, extracted)
    assert set(filled) == {"sector", "geography", "application_date"}
    assert extracted.geography == "Roorkee, India"
    assert extracted.application_date == "2026-11-23"
    assert extracted.sector == "MedTech"


def test_document_values_are_never_overwritten():
    with session_module.SessionLocal() as db:
        st = _startup_with_submission(db)
        extracted = SimpleNamespace(company_name="Deck Name", sector="HealthTech", stage="MVP", geography="Bhubaneswar", application_date="2026-10-01")
        filled = _fill_cover_metadata_from_intake(db, st, extracted)
    assert filled == []
    assert (extracted.company_name, extracted.sector, extracted.geography) == ("Deck Name", "HealthTech", "Bhubaneswar")


def test_no_submission_means_no_change():
    with session_module.SessionLocal() as db:
        st = StartupApplication(startup_name="Legacy Co", sector="SaaS", stage="Seed")
        db.add(st)
        db.commit()
        extracted = SimpleNamespace(company_name=None, sector=None, stage=None, geography=None, application_date=None)
        assert _fill_cover_metadata_from_intake(db, st, extracted) == []
    assert extracted.geography is None
