"""commercialisation.py - Domain 4: Business Model & Commercialisation Specialist Expert Agent.

Owns LaunchIndex Slides 11–12 and Canonical Criteria BC-01 through BC-13.
Builds on existing commercial and financial capabilities.
Strictly distinguishes paying customers from free trial users, and signed commercial contracts from non-binding MOUs.
"""

from typing import Any, Optional, List
from app.modules.evaluation.domains.base import CanonicalDomainExpert
from app.modules.evaluation.domain_schemas import VerificationStatus


class CommercialisationExpert(CanonicalDomainExpert):
    """Domain 4: Business Model & Commercialisation Specialist."""

    def get_domain_key(self) -> str:
        return "commercialisation"

    def get_fallback_prompt_key(self) -> str:
        return "financial"

    def refine_verification_status(
        self,
        criterion_id: str,
        value: Optional[str],
        default_status: VerificationStatus,
        all_claims: List[Any]
    ) -> VerificationStatus:
        """Enforces commercial factuality:

        1. Free users must never be equated to paying clients.
        2. Non-binding MOUs/LOIs must never be presented as confirmed commercial contracts.
        """
        if criterion_id == "BC-08":  # Users and paying customers
            paying_claim = next((c for c in all_claims if getattr(getattr(c, "field", None), "field_key", "").lower().startswith("bc_08_paying_customers")), None)
            if paying_claim is None:
                if self._is_missing_placeholder(value):
                    return VerificationStatus.MISSING_INFORMATION
                return default_status

            raw_paying = (
                paying_claim.value_string
                if paying_claim.value_string is not None
                else (str(paying_claim.value_number) if paying_claim.value_number is not None else None)
            )
            if raw_paying is None or not str(raw_paying).strip():
                return (
                    VerificationStatus.MISSING_INFORMATION
                    if default_status == VerificationStatus.VERIFIED_DOCUMENTED
                    else default_status
                )

            cleaned_paying = str(raw_paying).strip().lower()
            if cleaned_paying in ("0", "0.0", "none", "nil", "zero", "pre-revenue") or "pre-revenue" in cleaned_paying:
                # Explicitly documented zero paying customers / pre-revenue status must not be penalized
                return (
                    VerificationStatus.VERIFIED_DOCUMENTED
                    if default_status == VerificationStatus.VERIFIED_DOCUMENTED
                    else VerificationStatus.SELF_REPORTED_ONLY
                )
            return default_status

        if criterion_id == "BC-10":  # Pilot agreements & LOIs
            pilot_claim = next((c for c in all_claims if getattr(getattr(c, "field", None), "field_key", "").lower().startswith("bc_10_pilot_agreements")), None)
            if pilot_claim and pilot_claim.value_json:
                pilots = pilot_claim.value_json if isinstance(pilot_claim.value_json, list) else [pilot_claim.value_json]
                has_signed = any(isinstance(p, dict) and p.get("is_signed") is True for p in pilots)
                if has_signed:
                    return VerificationStatus.VERIFIED_DOCUMENTED
                else:
                    # Only LOIs or unsigned MOUs
                    return VerificationStatus.PLAUSIBLE_ESTIMATE

        return default_status
