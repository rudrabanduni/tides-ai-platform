"""Regression: extraction schemas must accept explicit "unknown" (null) values from the model.

The first live pilot run (2026-11-23) failed at the Innovation/IP stage because the
deck says "Patent filed" without a jurisdiction; the model correctly returned null, and the schema
rejected it (it also defaulted unknown jurisdictions to "India", inventing a fact).
"""

from app.modules.ai.orchestrator.startup_profile_extraction import (
    ApplicantDeclarationEntry,
    CompetitorEntry,
    FounderEntry,
    InnovationIpPatentsExtraction,
    PatentEntry,
    PilotAgreementEntry,
)


def test_innovation_stage_accepts_patent_with_unknown_jurisdiction_and_status():
    payload = {"patent_details": [{"title": "Synthetic sensor assembly", "jurisdiction": None, "status": None}]}
    parsed = InnovationIpPatentsExtraction.model_validate(payload)
    entry = parsed.patent_details[0]
    assert entry.jurisdiction is None and entry.status is None


def test_unknown_values_are_not_replaced_by_invented_facts():
    assert PatentEntry(title="x").jurisdiction is None
    assert PatentEntry(title="x").status is None
    assert CompetitorEntry(name="c").country is None


def test_nullable_fields_with_conservative_defaults():
    assert PilotAgreementEntry(partner_name="p", is_signed=None, agreement_type=None).is_signed is None
    assert PilotAgreementEntry(partner_name="p").is_signed is False  # unknown pilot is never treated as signed
    assert FounderEntry(name="f", role=None).role is None
    assert ApplicantDeclarationEntry(is_signed=None).is_signed is None
