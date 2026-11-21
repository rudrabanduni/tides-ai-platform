"""founder_team.py - Domain 3: Founder & Team Capability Specialist Expert Agent.

Owns LaunchIndex Slides 8–10 and Canonical Criteria FT-01 through FT-13.
Reuses capabilities from FounderExpert.
Supports multi-founder parity, verified credentials vs self-reported claims, skill gaps, hiring roadmap, and advisors.
"""

from typing import Any, Optional, List
from app.modules.evaluation.domains.base import CanonicalDomainExpert
from app.modules.evaluation.domain_schemas import VerificationStatus


class FounderTeamExpert(CanonicalDomainExpert):
    """Domain 3: Founder & Team Capability Specialist."""

    def get_domain_key(self) -> str:
        return "founder_team"

    def get_fallback_prompt_key(self) -> str:
        return "founder"

    def refine_verification_status(
        self,
        criterion_id: str,
        value: Optional[str],
        default_status: VerificationStatus,
        all_claims: List[Any]
    ) -> VerificationStatus:
        """Enforces credential rule: Profile URL presence does NOT constitute verified credentials."""
        if criterion_id == "FT-02":  # LinkedIn Profile
            if value and "linkedin.com" in str(value).lower():
                return VerificationStatus.VERIFIED_DOCUMENTED
            return VerificationStatus.MISSING_INFORMATION

        if criterion_id in ("FT-03", "FT-04", "FT-05"):  # Education, Experience, Prior Ventures
            if self._is_missing_placeholder(value):
                return (
                    VerificationStatus.NOT_APPLICABLE
                    if default_status == VerificationStatus.NOT_APPLICABLE
                    else VerificationStatus.MISSING_INFORMATION
                )
            # If founder merely states a degree/experience without third-party proof, classify as SELF_REPORTED_ONLY
            if default_status == VerificationStatus.VERIFIED_DOCUMENTED:
                # Disclosed in deck with evidence snippet
                return VerificationStatus.VERIFIED_DOCUMENTED
            return VerificationStatus.SELF_REPORTED_ONLY

        return default_status
