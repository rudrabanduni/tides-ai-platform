"""market_opportunity.py - Domain 2: Market Opportunity Specialist Expert Agent.

Owns LaunchIndex Slides 6–7 and Canonical Criteria MO-01 through MO-10.
Reuses capabilities from MarketExpert and CompetitionExpert.
Evaluates TAM/SAM/SOM, growth drivers, geographic focus, and dynamic competitor matrix (supporting >=4 competitors).
Distinguishes founder figures, verified analyst facts, reasoned estimates, and unsupported claims.
Integrates cost-metered external research (e.g. Tavily, industry reports) with strict provenance tracking.
"""

import logging
from typing import Any, Optional, List

from app.core.config import get_settings
from app.modules.evaluation.domains.base import CanonicalDomainExpert
from app.modules.evaluation.domain_schemas import DomainAssessmentReport, VerificationStatus
from app.services.ai.exceptions import AIBudgetExhaustedError
from app.services.ai.research import ExternalResearchService, ResearchEvidenceItem

logger = logging.getLogger(__name__)


class MarketOpportunityExpert(CanonicalDomainExpert):
    """Domain 2: Market Opportunity Specialist."""

    def __init__(self, gateway: Any = None) -> None:
        super().__init__(gateway=gateway)
        self._current_external_items: Optional[List[ResearchEvidenceItem]] = None

    def get_domain_key(self) -> str:
        return "market_opportunity"

    def get_fallback_prompt_key(self) -> str:
        return "market"

    def gather_external_research(
        self,
        profile: Any,
        claims: List[Any],
        metadata: dict[str, Any]
    ) -> List[ResearchEvidenceItem]:
        """Gathers bounded external market research if research provider is enabled.

        Queries:
        1. Market Size & Growth (TAM/SAM/SOM benchmarks)
        2. Competitor Intelligence & Benchmarks
        3. Industry Trends / Regulatory Tailwinds (if query budget permits)
        """
        service = ExternalResearchService.get_instance()
        if not service.is_available():
            return []

        settings = get_settings()
        max_queries = getattr(settings, "research_max_queries_per_eval", 4)
        evaluation_id = metadata.get("evaluation_id")

        # Extract company and sector context safely
        company_name = ""
        if hasattr(profile, "startup") and profile.startup:
            company_name = getattr(profile.startup, "startup_name", "")
        if not company_name:
            company_name = getattr(profile, "company_name", getattr(profile, "name", "")) or "Startup"

        sector = getattr(profile, "sector", "") or "DeepTech"

        # Find target market and competitors from claims if available
        target_market = ""
        competitors: List[str] = []
        for c in claims:
            fk = getattr(c, "field", None)
            fkey = str(getattr(fk, "field_key", "") if fk else getattr(c, "field_name", "")).lower()
            val = str(c.value_string or "")
            if "target_market" in fkey or "mo_03" in fkey:
                if val:
                    target_market = val
            elif "competitor" in fkey or "mo_07" in fkey or "competition" in fkey:
                if val and val not in competitors and len(val) < 60:
                    competitors.append(val)

        if not target_market:
            target_market = sector

        evidence_items: List[ResearchEvidenceItem] = []
        queries_executed = 0

        # Query 1: Market Size & Growth
        if queries_executed < max_queries:
            try:
                res1 = service.research_market_size_and_growth(
                    sector=sector,
                    target_market=target_market,
                    evaluation_id=evaluation_id,
                )
                if res1.evidence_items:
                    evidence_items.extend(res1.evidence_items)
                queries_executed += 1
            except AIBudgetExhaustedError:
                logger.warning("[MARKET] External research stopped: budget ceiling reached.")
                return evidence_items
            except Exception as e:
                logger.warning(f"[MARKET] Market size external research failed: {e}")

        # Query 2: Competitor Intelligence
        if queries_executed < max_queries:
            try:
                res2 = service.research_competitors(
                    company_name=company_name,
                    sector=sector,
                    competitor_names=competitors[:4] if competitors else None,
                    evaluation_id=evaluation_id,
                )
                if res2.evidence_items:
                    evidence_items.extend(res2.evidence_items)
                queries_executed += 1
            except AIBudgetExhaustedError:
                logger.warning("[MARKET] External research stopped: budget ceiling reached.")
                return evidence_items
            except Exception as e:
                logger.warning(f"[MARKET] Competitor external research failed: {e}")

        # Query 3: Industry Trends (if query budget permits)
        if queries_executed < max_queries:
            try:
                res3 = service.research_industry_trends(
                    sector=sector,
                    technology_domain=target_market,
                    evaluation_id=evaluation_id,
                )
                if res3.evidence_items:
                    evidence_items.extend(res3.evidence_items)
                queries_executed += 1
            except AIBudgetExhaustedError:
                logger.warning("[MARKET] External research stopped: budget ceiling reached.")
                return self.corroborate_evidence_items(evidence_items)
            except Exception as e:
                logger.warning(f"[MARKET] Industry trends external research failed: {e}")

        return self.corroborate_evidence_items(evidence_items)

    def corroborate_evidence_items(
        self,
        items: List[ResearchEvidenceItem]
    ) -> List[ResearchEvidenceItem]:
        """Evaluates multi-source corroboration across distinct domains.

        Institutional Rule:
        Requires >= 2 distinct source domains supporting the same topic before upgrading
        an external finding to INDEPENDENTLY_CORROBORATED or CORROBORATED_EXTERNAL_BENCHMARK.
        Duplicate domains (e.g. 2 articles on the same site) remain SINGLE_SOURCE.
        """
        by_type: dict[str, List[ResearchEvidenceItem]] = {}
        for it in items:
            by_type.setdefault(it.source_type, []).append(it)

        for st, group in by_type.items():
            distinct_domains = {it.source_domain for it in group if it.source_domain and it.source_domain != "web"}
            if len(distinct_domains) >= 2:
                for it in group:
                    if it.support_status != "INCONCLUSIVE":
                        it.corroboration_status = "INDEPENDENTLY_CORROBORATED"
                        if it.verification_grade == "RETRIEVED_SEARCH_RESULT":
                            it.verification_grade = "CORROBORATED_EXTERNAL_BENCHMARK"
                            it.requires_verification = False
            else:
                for it in group:
                    if it.corroboration_status == "UNVERIFIED_CANDIDATE":
                        it.corroboration_status = "SINGLE_SOURCE"
        return items

    def generate_reasoning(
        self,
        profile: Any,
        claims: list[Any],
        evidence: list[Any],
        conflicts: list[Any],
        metadata: dict[str, Any]
    ) -> str:
        """Injects external research findings with strict provenance tags into prompt reasoning."""
        base_context = super().generate_reasoning(profile, claims, evidence, conflicts, metadata)
        external_items = getattr(self, "_current_external_items", None)
        if not external_items:
            return base_context

        has_mock = any(getattr(item, "is_mock", False) or item.provenance == "MOCK_SIMULATED_RESEARCH" for item in external_items)
        if has_mock:
            header = "\n--- SIMULATED TEST RESEARCH EVIDENCE (Mock Offline Provider - Not Real Search) ---"
        else:
            header = "\n--- INDEPENDENT EXTERNAL RESEARCH EVIDENCE (Strict Provenance: EXTERNAL_INDEPENDENT_RESEARCH) ---"

        ext_lines = [
            header,
            "NOTE: The following are external industry benchmarks and market research data.",
            "They serve to corroborate industry context and benchmarks, but do NOT automatically prove primary internal startup claims.",
        ]
        for idx, item in enumerate(external_items, 1):
            rel_str = f"{item.relevance_score:.2f}" if item.relevance_score is not None else "N/A"
            mock_tag = " [SIMULATED TEST FIXTURE]" if getattr(item, "is_mock", False) else ""
            ext_lines.append(
                f"[External Source {idx}{mock_tag}]: {item.title}\n"
                f"  Domain: {item.source_domain} (Authority: {item.source_authority}) | URL: {item.url}\n"
                f"  Provenance: {item.provenance} | Published: {item.publication_date or 'N/A'} ({item.freshness_status}) | Query Relevance: {rel_str}\n"
                f"  Grade: {item.verification_grade} | Corroboration: {item.corroboration_status} | Support: {item.support_status}\n"
                f"  Excerpt: {item.excerpt}\n"
                f"  Summary: {item.summary}"
            )
        ext_lines.append("--------------------------------------------------------------------------------------------------")
        return base_context + "\n" + "\n".join(ext_lines)

    def evaluate(
        self,
        profile: Any,
        claims: list[Any],
        evidence: list[Any],
        conflicts: list[Any],
        metadata: dict[str, Any]
    ) -> DomainAssessmentReport:
        """Executes Market Opportunity evaluation, attaching external research with strict provenance."""
        # 1. Gather external research (returns [] if research_provider is disabled)
        external_items = self.gather_external_research(profile, claims, metadata)
        self._current_external_items = external_items

        try:
            # 2. Run canonical domain specialist evaluation
            report = super().evaluate(profile, claims, evidence, conflicts, metadata)
        finally:
            self._current_external_items = None

        # 3. Attach external evidence items to report and individual criteria
        if external_items:
            report.external_research_evidence = [item.model_dump() for item in external_items]
            report.confidence_limitations = (
                f"Corroborated by {len(external_items)} independent external research sources."
            )

            # Categorize items by source_type
            market_sources = [
                item.model_dump() for item in external_items
                if item.source_type in ("market_size_growth", "industry_trends")
            ]
            comp_sources = [
                item.model_dump() for item in external_items
                if item.source_type in ("competitor_intelligence", "funding_lookup")
            ]

            for cid, crit in report.criteria_evaluations.items():
                target_sources = []
                if cid in ("MO-01", "MO-02", "MO-03", "MO-04", "MO-05"):
                    target_sources = market_sources
                elif cid in ("MO-07", "MO-08", "MO-09", "MO-10"):
                    target_sources = comp_sources

                if target_sources:
                    for src in target_sources:
                        src_copy = dict(src)
                        src_copy["claimed_criterion_id"] = cid
                        src_copy["criterion_name"] = crit.criterion_name

                        # Check if excerpt contains supporting metrics matching startup claim
                        claim_val = str(crit.extracted_startup_response or "").lower()
                        excerpt_text = str(src.get("excerpt", "")).lower()

                        digits = [w for w in claim_val.split() if any(c.isdigit() for c in w)]
                        if digits and any(d in excerpt_text for d in digits):
                            src_copy["support_status"] = "EXPLICIT_SUPPORT"
                        elif src_copy.get("support_status") == "INCONCLUSIVE":
                            src_copy["support_status"] = "INCONCLUSIVE"
                        else:
                            src_copy["support_status"] = "INDIRECT_CONTEXT"

                        crit.external_research_sources.append(src_copy)
                        loc = f"External: {src.get('source_domain', 'web')}"
                        if loc not in crit.source_locations:
                            crit.source_locations.append(loc)

                    # Explicitly record verification limitation when candidate source requires confirmation
                    unverified = [s for s in crit.external_research_sources if s.get("requires_verification", True)]
                    if unverified and not crit.confidence_limitations:
                        crit.confidence_limitations = f"External research retrieved for {cid} provides candidate context requiring independent verification."

        return report

    def refine_verification_status(
        self,
        criterion_id: str,
        value: Optional[str],
        default_status: VerificationStatus,
        all_claims: List[Any]
    ) -> VerificationStatus:
        """Distinguishes founder self-reported figures vs cited analyst research vs estimates.

        Strict Provenance Rule: External research alone does NOT elevate internal claims
        to VERIFIED_DOCUMENTED without submitted deck/application documentation.
        """
        if criterion_id == "MO-04":  # CAGR & source citation
            cagr_source_claim = next((c for c in all_claims if getattr(getattr(c, "field", None), "field_key", "").lower().startswith("mo_04_cagr_source")), None)
            if cagr_source_claim and cagr_source_claim.value_string:
                return VerificationStatus.VERIFIED_DOCUMENTED
            elif value and "%" in str(value):
                # Has a percentage but missing reputable citation
                return VerificationStatus.PLAUSIBLE_ESTIMATE
            return VerificationStatus.UNSUPPORTED_ASSUMPTION

        if criterion_id == "MO-01":  # TAM
            if value and any(c.isdigit() for c in str(value)):
                # If primary deck evidence exists
                if default_status == VerificationStatus.VERIFIED_DOCUMENTED:
                    return VerificationStatus.VERIFIED_DOCUMENTED
                return VerificationStatus.SELF_REPORTED_ONLY

        return default_status
