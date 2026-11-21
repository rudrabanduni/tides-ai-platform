"""Institutional evidence classes shown in every report and UI view.

Maps the model-facing VerificationStatus grades onto the five classes the incubation committee
reads, so applicant self-reporting is never presented as verified evidence.
"""

from __future__ import annotations

from typing import Any

APPLICANT_REPORTED = "APPLICANT_REPORTED"
DOCUMENTARY_EVIDENCE = "DOCUMENTARY_EVIDENCE"
INDEPENDENTLY_VERIFIED = "INDEPENDENTLY_VERIFIED"
NOT_VERIFIED = "NOT_VERIFIED"
MISSING = "MISSING"
NOT_APPLICABLE = "NOT_APPLICABLE"

EVIDENCE_CLASS_LABELS = {
    APPLICANT_REPORTED: "Applicant-reported",
    DOCUMENTARY_EVIDENCE: "Documentary evidence",
    INDEPENDENTLY_VERIFIED: "Independently verified",
    NOT_VERIFIED: "Not verified",
    MISSING: "Missing",
    NOT_APPLICABLE: "Not applicable",
}

_STATUS_TO_CLASS = {
    "VERIFIED_DOCUMENTED": DOCUMENTARY_EVIDENCE,
    "SELF_REPORTED_ONLY": APPLICANT_REPORTED,
    "PLAUSIBLE_ESTIMATE": NOT_VERIFIED,
    "UNSUPPORTED_ASSUMPTION": NOT_VERIFIED,
    "CONTRADICTED": NOT_VERIFIED,
    "MISSING_INFORMATION": MISSING,
    "NOT_APPLICABLE": NOT_APPLICABLE,
}


def _has_independent_source(external_sources: Any) -> bool:
    """Independent verification requires a recorded third-party source that is not synthetic."""
    for src in external_sources or []:
        if not isinstance(src, dict):
            continue
        provenance = str(src.get("provenance") or src.get("source_type") or "").lower()
        if "mock" in provenance or "synthetic" in provenance:
            continue
        if src.get("url") and src.get("verified") is True:
            return True
    return False


def evidence_class_for(verification_status: Any, external_sources: Any = None) -> str:
    raw = getattr(verification_status, "value", verification_status)
    cls = _STATUS_TO_CLASS.get(str(raw or "").upper(), NOT_VERIFIED)
    if cls == DOCUMENTARY_EVIDENCE and _has_independent_source(external_sources):
        return INDEPENDENTLY_VERIFIED
    return cls


def evidence_class_label(cls: str) -> str:
    return EVIDENCE_CLASS_LABELS.get(cls, cls)
