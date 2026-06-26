from abc import ABC, abstractmethod
from typing import Any


class BaseContextFilter(ABC):
    """Abstract interface for domain-specific context filters."""

    @abstractmethod
    def filter_claims(self, claims: list[Any]) -> list[Any]:
        """Filters a list of claims, returning only those relevant to the domain."""
        pass

    @abstractmethod
    def filter_conflicts(self, conflicts: list[Any]) -> list[Any]:
        """Filters a list of field conflicts, returning only those relevant to the domain."""
        pass

    @abstractmethod
    def get_required_fields(self) -> list[str]:
        """Returns the list of registry field keys required by this expert domain."""
        pass


class FounderContextFilter(BaseContextFilter):
    """Filter extracting only founder, leadership, commitment, and management claims/conflicts."""

    # Set of standard keys representing the founder domain
    FOUNDER_FIELDS = {
        "founder_names",
        "leadership_experience",
        "domain_expertise",
        "commitment_level",
        "ownership",
        "roles",
        "team_structure",
        "leadership",
        "advisors",
        "hiring",
        "execution_history"
    }

    def filter_claims(self, claims: list[Any]) -> list[Any]:
        filtered = []
        for claim in claims:
            fk = claim.field.field_key if (hasattr(claim, "field") and claim.field) else None
            if fk in self.FOUNDER_FIELDS:
                filtered.append(claim)
        return filtered

    def filter_conflicts(self, conflicts: list[Any]) -> list[Any]:
        filtered = []
        for conflict in conflicts:
            fk = conflict.field.field_key if (hasattr(conflict, "field") and conflict.field) else None
            if fk in self.FOUNDER_FIELDS:
                filtered.append(conflict)
        return filtered

    def get_required_fields(self) -> list[str]:
        return ["founder_names", "leadership_experience", "domain_expertise", "commitment_level"]


# --- Empty Placeholders for Future Experts ---

class ProductContextFilter(BaseContextFilter):
    def filter_claims(self, claims: list[Any]) -> list[Any]: return []
    def filter_conflicts(self, conflicts: list[Any]) -> list[Any]: return []
    def get_required_fields(self) -> list[str]: return []


class TRLContextFilter(BaseContextFilter):
    def filter_claims(self, claims: list[Any]) -> list[Any]: return []
    def filter_conflicts(self, conflicts: list[Any]) -> list[Any]: return []
    def get_required_fields(self) -> list[str]: return []


class FinancialContextFilter(BaseContextFilter):
    def filter_claims(self, claims: list[Any]) -> list[Any]: return []
    def filter_conflicts(self, conflicts: list[Any]) -> list[Any]: return []
    def get_required_fields(self) -> list[str]: return []


class MarketContextFilter(BaseContextFilter):
    def filter_claims(self, claims: list[Any]) -> list[Any]: return []
    def filter_conflicts(self, conflicts: list[Any]) -> list[Any]: return []
    def get_required_fields(self) -> list[str]: return []


class CompetitionContextFilter(BaseContextFilter):
    """Filter extracting only competition, competitor, defensibility, moat, and market positioning claims/conflicts."""

    COMPETITION_FIELDS = {
        "competitors",
        "competitor_names",
        "substitute_solutions",
        "differentiation_claims",
        "moat_claims",
        "barriers_to_entry",
        "patents_linked_to_defensibility",
        "market_positioning_statements",
        "customer_switching_cost_evidence",
        "network_effect_evidence",
        "distribution_advantage_evidence",
        "direct_competitors",
        "indirect_competitors",
        "differentiation",
        "defensibility",
        "moat",
        "barriers",
        "market_positioning",
        "switching_costs",
        "network_effects",
        "distribution_advantage"
    }

    def filter_claims(self, claims: list[Any]) -> list[Any]:
        filtered = []
        for claim in claims:
            fk = claim.field.field_key if (hasattr(claim, "field") and claim.field) else None
            if fk in self.COMPETITION_FIELDS:
                filtered.append(claim)
        return filtered

    def filter_conflicts(self, conflicts: list[Any]) -> list[Any]:
        filtered = []
        for conflict in conflicts:
            fk = conflict.field.field_key if (hasattr(conflict, "field") and conflict.field) else None
            if fk in self.COMPETITION_FIELDS:
                filtered.append(conflict)
        return filtered

    def get_required_fields(self) -> list[str]:
        return ["competitors", "differentiation_claims", "moat_claims"]


class IPContextFilter(BaseContextFilter):
    """Filter extracting only intellectual property, patent, trademark, copyright, ownership, and licensing claims/conflicts."""

    IP_FIELDS = {
        "patents",
        "patent_applications",
        "patent_numbers",
        "design_registrations",
        "trademarks",
        "copyrights",
        "licensing_agreements",
        "ownership_declarations",
        "proprietary_technology_claims",
        "trade_secret_claims",
        "research_publications",
        "technology_disclosures",
        "defensibility_claims",
        "patent",
        "patent_application",
        "patent_number",
        "design_registration",
        "trademark",
        "copyright",
        "licensing_agreement",
        "ownership_declaration",
        "proprietary_technology",
        "trade_secret",
        "research_publication",
        "technology_disclosure",
        "defensibility",
        "ip_ownership",
        "intellectual_property"
    }

    def filter_claims(self, claims: list[Any]) -> list[Any]:
        filtered = []
        for claim in claims:
            fk = claim.field.field_key if (hasattr(claim, "field") and claim.field) else None
            if fk in self.IP_FIELDS:
                filtered.append(claim)
        return filtered

    def filter_conflicts(self, conflicts: list[Any]) -> list[Any]:
        filtered = []
        for conflict in conflicts:
            fk = conflict.field.field_key if (hasattr(conflict, "field") and conflict.field) else None
            if fk in self.IP_FIELDS:
                filtered.append(conflict)
        return filtered

    def get_required_fields(self) -> list[str]:
        return ["patents", "ownership_declarations", "licensing_agreements"]


class RiskContextFilter(BaseContextFilter):
    """Filter extracting only risk, validation gap, and conflict claims/conflicts."""

    RISK_FIELDS = {
        "technical_risk_claims",
        "market_risk_claims",
        "regulatory_risk_claims",
        "execution_risk_claims",
        "founder_dependency_risks",
        "customer_concentration_risks",
        "supply_chain_risks",
        "financial_runway_risks",
        "evidence_gaps",
        "unresolved_conflicts"
    }

    def filter_claims(self, claims: list[Any]) -> list[Any]:
        filtered = []
        for claim in claims:
            fk = claim.field.field_key if (hasattr(claim, "field") and claim.field) else None
            if fk in self.RISK_FIELDS:
                filtered.append(claim)
        return filtered

    def filter_conflicts(self, conflicts: list[Any]) -> list[Any]:
        filtered = []
        for conflict in conflicts:
            fk = conflict.field.field_key if (hasattr(conflict, "field") and conflict.field) else None
            if fk in self.RISK_FIELDS:
                filtered.append(conflict)
        return filtered

    def get_required_fields(self) -> list[str]:
        return ["technical_risk_claims", "market_risk_claims", "financial_runway_risks"]


class InvestmentContextFilter(BaseContextFilter):
    def filter_claims(self, claims: list[Any]) -> list[Any]: return []
    def filter_conflicts(self, conflicts: list[Any]) -> list[Any]: return []
    def get_required_fields(self) -> list[str]: return []
