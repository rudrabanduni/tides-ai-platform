from datetime import datetime, timezone
from uuid import uuid4

import app.db.base  # noqa: F401

from app.core.enums import DocumentProcessingStatus, DocumentType, StartupStatus
from app.modules.company_profiles.models import CompanyProfile
from app.modules.documents.models import Document
from app.modules.founders.models import Founder
from app.modules.startup_profiles.context import StartupProfileContextBuilder
from app.modules.startup_profiles.models import StartupProfile
from app.modules.startups.models import StartupApplication


def _utcnow() -> datetime:
    return datetime(2026, 6, 9, 12, 0, tzinfo=timezone.utc)


def _startup(**overrides: object) -> StartupApplication:
    values = {
        "id": uuid4(),
        "startup_name": "BatteryX",
        "sector": "CleanTech",
        "stage": "MVP",
        "current_status": StartupStatus.SUBMITTED,
        "problem_statement": "Grid storage is expensive",
        "solution_summary": "Affordable battery analytics",
        "business_model": None,
        "target_market": "Industrial energy users",
        "traction_summary": None,
        "funding_status": None,
        "submitted_at": _utcnow(),
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
    }
    values.update(overrides)
    return StartupApplication(**values)


def _founder(startup_id, **overrides: object) -> Founder:
    values = {
        "id": uuid4(),
        "startup_id": startup_id,
        "name": "Asha Rao",
        "email": "asha@example.com",
        "phone": None,
        "education": None,
        "experience_summary": None,
        "linkedin_url": None,
        "role_in_startup": "CEO",
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
    }
    values.update(overrides)
    return Founder(**values)


def _profile(startup_id, **overrides: object) -> StartupProfile:
    values = {
        "id": uuid4(),
        "startup_id": startup_id,
        "problem_statement": "Grid storage is expensive",
        "solution_summary": "Affordable battery analytics",
        "target_market": "Industrial energy users",
        "business_model": None,
        "technology_summary": None,
        "traction_summary": None,
        "funding_summary": None,
        "ip_summary": None,
        "generated_at": _utcnow(),
        "updated_at": _utcnow(),
    }
    values.update(overrides)
    return StartupProfile(**values)


def _company_profile(startup_id, **overrides: object) -> CompanyProfile:
    values = {
        "id": uuid4(),
        "startup_id": startup_id,
        "website": "https://batteryx.example",
        "incorporation_status": "Private Limited",
        "registration_number": None,
        "location": "Roorkee",
        "team_size": 4,
        "revenue_status": None,
        "ip_status": None,
        "market_category": "Energy",
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
    }
    values.update(overrides)
    return CompanyProfile(**values)


def _document(startup_id, **overrides: object) -> Document:
    values = {
        "id": uuid4(),
        "startup_id": startup_id,
        "document_type": DocumentType.PITCH_DECK,
        "original_filename": "deck.pdf",
        "stored_filename": "stored-deck.pdf",
        "file_path": "uploads/secret/path/deck.pdf",
        "content_type": "application/pdf",
        "file_size": 1024,
        "parsed_text": "Pitch deck summary",
        "processing_status": DocumentProcessingStatus.PARSED,
        "uploaded_by": None,
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
    }
    values.update(overrides)
    return Document(**values)


def test_builds_full_context_with_all_sections() -> None:
    startup = _startup()
    founder = _founder(startup.id)
    profile = _profile(startup.id)
    company_profile = _company_profile(startup.id)
    document = _document(startup.id)

    context = StartupProfileContextBuilder().build(
        startup=startup,
        founders=[founder],
        profile=profile,
        company_profile=company_profile,
        documents=[document],
    )
    payload = context.to_prompt_dict()

    assert payload["startup"]["startup_name"] == "BatteryX"
    assert payload["startup"]["current_status"] == "Submitted"
    assert len(payload["founders"]) == 1
    assert payload["founders"][0]["email"] == "asha@example.com"
    assert payload["company_profile"]["website"] == "https://batteryx.example"
    assert len(payload["documents"]) == 1
    assert payload["documents"][0]["parsed_text"] == "Pitch deck summary"
    assert payload["current_profile"]["target_market"] == "Industrial energy users"


def test_handles_missing_optional_sections_gracefully() -> None:
    startup = _startup()

    context = StartupProfileContextBuilder().build(startup=startup)
    payload = context.to_prompt_dict()

    assert payload["startup"]["startup_name"] == "BatteryX"
    assert payload["founders"] == []
    assert payload["company_profile"] is None
    assert payload["documents"] == []
    assert payload["current_profile"] is None


def test_document_parsed_text_only_included_when_status_is_parsed() -> None:
    startup = _startup()
    uploaded_document = _document(
        startup.id,
        parsed_text="Should not leak",
        processing_status=DocumentProcessingStatus.UPLOADED,
    )
    parsed_document = _document(startup.id)

    context = StartupProfileContextBuilder().build(
        startup=startup,
        documents=[uploaded_document, parsed_document],
    )
    payload = context.to_prompt_dict()

    assert payload["documents"][0]["parsed_text"] is None
    assert payload["documents"][1]["parsed_text"] == "Pitch deck summary"


def test_documents_exclude_internal_storage_paths() -> None:
    startup = _startup()
    document = _document(startup.id)

    payload = StartupProfileContextBuilder().build(startup=startup, documents=[document]).to_prompt_dict()

    document_payload = payload["documents"][0]
    assert "file_path" not in document_payload
    assert "stored_filename" not in document_payload
    assert document_payload["original_filename"] == "deck.pdf"


def test_nullable_fields_remain_null_in_populated_sections() -> None:
    startup = _startup(business_model=None, traction_summary=None)
    founder = _founder(startup.id, phone=None, education=None)

    payload = StartupProfileContextBuilder().build(
        startup=startup,
        founders=[founder],
        profile=_profile(startup.id, business_model=None),
    ).to_prompt_dict()

    assert payload["startup"]["business_model"] is None
    assert payload["founders"][0]["phone"] is None
    assert payload["current_profile"]["business_model"] is None
