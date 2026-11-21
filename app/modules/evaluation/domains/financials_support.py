"""financials_support.py - Domain 6: Financials & Incubation Support Specialist Expert Agent.

Owns LaunchIndex Slides 15–18 and Canonical Criteria FI-01 through FI-21.
Reuses capabilities from FinancialExpert.
Evaluates 3-year forecasts against stated assumptions (without fabricating assumptions), monthly burn rate,
optional external funding, 6-quarter operational roadmaps, and TIDES IIT Roorkee physical infrastructure needs.
"""

from typing import Any, Optional, List
from app.modules.evaluation.domains.base import CanonicalDomainExpert
from app.modules.evaluation.domain_schemas import VerificationStatus


class FinancialsSupportExpert(CanonicalDomainExpert):
    """Domain 6: Financials & Incubation Support Specialist."""

    def get_domain_key(self) -> str:
        return "financials_support"

    def get_fallback_prompt_key(self) -> str:
        return "financial"

    def refine_verification_status(
        self,
        criterion_id: str,
        value: Optional[str],
        default_status: VerificationStatus,
        all_claims: List[Any]
    ) -> VerificationStatus:
        """Enforces optional funding and projection integrity rules."""
        if criterion_id == "FI-08":  # External Funding Raised (Explicitly Optional)
            if self._is_missing_placeholder(value):
                return (
                    VerificationStatus.NOT_APPLICABLE
                    if default_status == VerificationStatus.VERIFIED_DOCUMENTED
                    else default_status
                )
            cleaned = str(value).strip().lower()
            if cleaned in ("0", "0.0", "₹0", "nil", "bootstrapped", "none (bootstrapped)", "0 inr") or "bootstrapped" in cleaned:
                # Explicitly documented bootstrapped/zero status must not fail as contradicted
                return (
                    VerificationStatus.VERIFIED_DOCUMENTED
                    if default_status == VerificationStatus.VERIFIED_DOCUMENTED
                    else VerificationStatus.SELF_REPORTED_ONLY
                )

        if criterion_id in ("FI-01", "FI-02", "FI-03", "FI-04"):  # 3-Year Projections
            if value and not self._is_missing_placeholder(value) and any(c.isdigit() for c in str(value)):
                # Forecast is provided, but inherently forward-looking
                return VerificationStatus.PLAUSIBLE_ESTIMATE

        if criterion_id in ("FI-20", "FI-21", "CM-01", "CM-02", "CM-03", "CM-04", "CM-05", "CM-06"):
            # Completeness and administrative verification fields
            if self._is_missing_placeholder(value):
                return VerificationStatus.MISSING_INFORMATION
            return default_status

        return default_status
