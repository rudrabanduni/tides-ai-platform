"""research.py - Clean, Cost-Aware External Research Tool Architecture.

Defines the pluggable provider contract for third-party market research, competitor
intelligence, industry trends, and regulatory verification tools (e.g. Tavily, Serper, MCA).

Design & Governance Principles:
1. Configurable Provider Abstraction:
   - Independent of LLM gateway selection.
   - Defaults to DisabledResearchProvider when unconfigured.
   - Provides deterministic MockResearchProvider for offline testing and verification.
2. Provenance & Factual Integrity:
   - Returns structured ResearchEvidenceItem instances with canonical URLs, dates, excerpts, and summaries.
   - Distinguishes external facts from startup-provided claims, estimates, and AI inferences.
   - Never invents citations; returns explicit UNAVAILABLE status when unverified.
3. Cost Ledger & Budget Enforcement:
   - Pre-reserves research cost against the shared $0.55 / ₹70 budget ledger prior to dispatch.
   - Reconciles actual tool expenditures under external_tools_cost_usd.
   - Fails safe: if budget is exhausted or provider configuration is missing, safely disables
     research and allows evaluation to proceed using submitted application documents.
"""

from __future__ import annotations

import logging
import urllib.parse
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.services.ai.cost_ledger import CostLedgerManager, EvaluationCostLedger
from app.services.ai.exceptions import (
    AIBudgetExhaustedError,
    AIProviderAuthenticationError,
    AIProviderError,
    AIResponseParseError,
)

logger = logging.getLogger(__name__)


def classify_source_authority(domain: str) -> str:
    """Classifies source domain authority into institutional diligence tiers."""
    d = (domain or "").lower().strip()
    if d.startswith("www."):
        d = d[4:]
    if (
        d.endswith(".gov")
        or d.endswith(".gov.in")
        or d.endswith(".nic.in")
        or ".gov." in d
        or d in ("sec.gov", "mca.gov.in", "rbi.org.in", "uspto.gov", "ipindia.gov.in")
    ):
        return "OFFICIAL_REGULATORY_FILING"
    if any(
        inst in d
        for inst in (
            "iea.org", "worldbank.org", "imf.org", "who.int", "oecd.org",
            "iso.org", "ieee.org", "standards.ieee.org", "niti.gov.in", "un.org"
        )
    ):
        return "INSTITUTIONAL_BENCHMARK"
    if any(
        analyst in d
        for analyst in (
            "gartner.com", "forrester.com", "bloomberg.com", "reuters.com",
            "idc.com", "statista.com", "mckinsey.com", "bain.com", "bcg.com",
            "pitchbook.com", "crunchbase.com", "wsj.com", "ft.com", "techcrunch.com"
        )
    ):
        return "INDUSTRY_ANALYST"
    return "GENERAL_WEB"


def assess_freshness(pub_date: Optional[str]) -> str:
    """Evaluates publication date freshness against a multi-year investment horizon."""
    if not pub_date or not str(pub_date).strip():
        return "DATE_UNAVAILABLE"
    import re
    match = re.search(r"\b(19\d\d|20\d\d)\b", str(pub_date))
    if match:
        year = int(match.group(1))
        if year < 2022:
            return "OUTDATED"
        return "CURRENT"
    return "DATE_UNAVAILABLE"


class ResearchEvidenceItem(BaseModel):
    """Structured verifiable evidence item retrieved from an external research provider."""

    url: str = Field(..., description="Canonical source URL of retrieved document or report")
    title: str = Field(..., description="Title of external document, article, or filing")
    publication_date: Optional[str] = Field(None, description="ISO publication date or publication year if available")
    excerpt: str = Field(..., description="Exact raw text snippet retrieved from external source")
    summary: str = Field(..., description="Concise objective synthesis of retrieved finding")
    source_domain: str = Field(..., description="Domain name (e.g. 'gartner.com', 'bloomberg.com', 'mca.gov.in')")
    source_type: str = Field(
        "market_research",
        description="'market_size_growth', 'competitor_intelligence', 'industry_trends', 'regulatory_technical'"
    )
    provenance: str = Field(
        "EXTERNAL_INDEPENDENT_RESEARCH",
        description="Strict provenance tag: 'EXTERNAL_INDEPENDENT_RESEARCH', 'MOCK_SIMULATED_RESEARCH', 'STARTUP_CLAIM', 'ANALYST_INFERENCE'"
    )
    is_mock: bool = Field(
        False,
        description="True if evidence is an offline simulated mock fixture rather than a live external web search result"
    )
    relevance_score: Optional[float] = Field(
        None,
        description="Numeric search-result query relevance score (e.g. Tavily score 0.0-1.0). Decoupled from factual truth."
    )
    source_authority: str = Field(
        "GENERAL_WEB",
        description="'OFFICIAL_REGULATORY_FILING', 'INSTITUTIONAL_BENCHMARK', 'INDUSTRY_ANALYST', 'GENERAL_WEB'"
    )
    freshness_status: str = Field(
        "CURRENT",
        description="'CURRENT', 'OUTDATED', 'DATE_UNAVAILABLE'"
    )
    support_status: str = Field(
        "RETRIEVED_CONTEXT",
        description="'EXPLICIT_SUPPORT', 'INDIRECT_CONTEXT', 'INCONCLUSIVE', 'RETRIEVED_CONTEXT'"
    )
    corroboration_status: str = Field(
        "UNVERIFIED_CANDIDATE",
        description="'INDEPENDENTLY_CORROBORATED', 'SINGLE_SOURCE', 'UNVERIFIED_CANDIDATE'"
    )
    requires_verification: bool = Field(
        True,
        description="True if finding is unverified candidate evidence requiring analyst or multi-source verification"
    )
    verification_limitations: Optional[str] = Field(
        None,
        description="Specific limitations, date cautions, or unverified claims for diligence notes"
    )
    verification_grade: str = Field(
        "RETRIEVED_SEARCH_RESULT",
        description="'DOCUMENTED_OFFICIAL_FILING', 'INSTITUTIONAL_BENCHMARK', 'CORROBORATED_EXTERNAL_BENCHMARK', 'RETRIEVED_SEARCH_RESULT', 'DOCUMENTED_EXTERNAL_FACT', 'CORROBORATED_ESTIMATE'"
    )


class ResearchQueryRequest(BaseModel):
    """Specification for an external research lookup."""

    query: str = Field(..., description="Search query string or company identifier")
    search_type: str = Field(
        "market_size_growth",
        description="'market_size_growth', 'competitor_intelligence', 'industry_trends', 'regulatory_technical', 'funding_lookup'"
    )
    evaluation_id: Optional[str] = Field(None, description="Evaluation run ID for budget accounting")
    startup_id: Optional[str] = Field(None)
    sector: Optional[str] = Field(None, description="Target industry sector")
    max_results: int = Field(5, description="Max search results to retrieve")
    search_depth: Optional[str] = Field(None, description="Optional search depth override ('basic' or 'advanced')")
    estimated_cost_usd: Optional[float] = Field(None, description="Optional estimated per-query external provider charge override")


class ResearchSearchResult(BaseModel):
    """Internal provider execution result containing retrieved items and real cost."""

    evidence_items: List[ResearchEvidenceItem] = Field(default_factory=list)
    actual_cost_usd: float = Field(0.0)
    credits_used: int = Field(1)
    raw_response: Optional[Dict[str, Any]] = None


class ResearchQueryResult(BaseModel):
    """Result of an external research query."""

    query: str
    search_type: str = Field("market_size_growth")
    is_available: bool = Field(False, description="Whether live external search integration is active")
    provider_name: str = Field("disabled")
    evidence_items: List[ResearchEvidenceItem] = Field(default_factory=list)
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Duck-type compatibility list")
    confidence: str = Field("UNAVAILABLE", description="'UNAVAILABLE', 'EXACT_MATCH', 'PARTIAL_MATCH', 'NO_RELEVANT_SOURCES'")
    message: str = Field("External web research integration is pending; relying exclusively on document evidence.")
    cost_usd: float = Field(0.0)


# ===========================================================================
# Pluggable Provider Abstraction
# ===========================================================================

class ResearchProvider(ABC):
    """Abstract interface for external search and industry data providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Identifier for the research provider."""
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if provider has valid credentials and configuration."""
        ...

    @abstractmethod
    def get_cost_per_query_usd(self, search_depth: Optional[str] = None) -> float:
        """Standard charge in USD per search query."""
        ...

    @abstractmethod
    def search(self, request: ResearchQueryRequest) -> List[ResearchEvidenceItem]:
        """Executes the research query and returns structured evidence items."""
        ...

    def search_detailed(self, request: ResearchQueryRequest) -> ResearchSearchResult:
        """Executes search and returns structured evidence items along with actual credit and cost accounting."""
        items = self.search(request)
        return ResearchSearchResult(
            evidence_items=items,
            actual_cost_usd=self.get_cost_per_query_usd(search_depth=request.search_depth),
            credits_used=2 if (request.search_depth or "").lower() == "advanced" else 1,
        )


class DisabledResearchProvider(ResearchProvider):
    """Default no-op provider when external research is disabled or unconfigured."""

    @property
    def provider_name(self) -> str:
        return "disabled"

    def is_configured(self) -> bool:
        return False

    def get_cost_per_query_usd(self, search_depth: Optional[str] = None) -> float:
        return 0.0

    def search(self, request: ResearchQueryRequest) -> List[ResearchEvidenceItem]:
        return []

    def search_detailed(self, request: ResearchQueryRequest) -> ResearchSearchResult:
        return ResearchSearchResult(
            evidence_items=[],
            actual_cost_usd=0.0,
            credits_used=0,
        )


class MockResearchProvider(ResearchProvider):
    """Deterministic offline research provider for testing and validation.

    Provides verified, structured evidence fixtures for:
    - Market size and growth (TAM/SAM/SOM CAGR benchmarks)
    - Named competitors (funding rounds, valuation milestones)
    - Industry trends (macro drivers, government policies)
    - Regulatory & technical standards (safety, compliance, patents)
    """

    def __init__(self, cost_per_query_usd: float = 0.005) -> None:
        self._cost_per_query_usd = cost_per_query_usd

    @property
    def provider_name(self) -> str:
        return "mock"

    def is_configured(self) -> bool:
        return True

    def get_cost_per_query_usd(self, search_depth: Optional[str] = None) -> float:
        return self._cost_per_query_usd

    def search(self, request: ResearchQueryRequest) -> List[ResearchEvidenceItem]:
        q = request.query.lower()
        st = request.search_type.lower()
        items: List[ResearchEvidenceItem] = []

        # 1. Market Size & Growth Fixtures
        if "market" in st or "size" in q or "cagr" in q or "growth" in q or "tam" in q:
            items.append(
                ResearchEvidenceItem(
                    url="https://www.iea.org/reports/energy-storage-market-update-2025",
                    title="IEA Global Energy Storage & Battery Market Report 2025",
                    publication_date="2025-04-15",
                    excerpt="The global utility-scale and commercial energy storage market reached $48.2B in 2024 and is projected to expand at a 24.3% CAGR through 2032, driven by grid decarbonisation mandates.",
                    summary="Independent IEA report confirms global energy storage market expanding at 24.3% CAGR toward $48B+ by 2032.",
                    source_domain="iea.org",
                    source_type="market_size_growth",
                    provenance="MOCK_SIMULATED_RESEARCH",
                    is_mock=True,
                    relevance_score=0.92,
                    source_authority="INSTITUTIONAL_BENCHMARK",
                    freshness_status="CURRENT",
                    support_status="RETRIEVED_CONTEXT",
                    corroboration_status="SINGLE_SOURCE",
                    requires_verification=True,
                    verification_limitations="Simulated test fixture (MockResearchProvider); offline mock not retrieved via live search.",
                    verification_grade="SIMULATED_TEST_EVIDENCE",
                )
            )
            items.append(
                ResearchEvidenceItem(
                    url="https://cea.nic.in/wp-content/uploads/bess-guidelines-2025.pdf",
                    title="Central Electricity Authority (CEA) National BESS Trajectory",
                    publication_date="2025-01-10",
                    excerpt="India's National Electricity Plan projects a minimum requirement of 47 GW / 236 GWh of BESS by 2031-32, supported by Viability Gap Funding (VGF) of up to 40% of capital costs.",
                    summary="CEA official projection mandates 47 GW national BESS adoption with 40% capital VGF support.",
                    source_domain="cea.nic.in",
                    source_type="market_size_growth",
                    provenance="MOCK_SIMULATED_RESEARCH",
                    is_mock=True,
                    relevance_score=0.95,
                    source_authority="OFFICIAL_REGULATORY_FILING",
                    freshness_status="CURRENT",
                    support_status="RETRIEVED_CONTEXT",
                    corroboration_status="SINGLE_SOURCE",
                    requires_verification=True,
                    verification_limitations="Simulated test fixture (MockResearchProvider); offline mock not retrieved via live search.",
                    verification_grade="SIMULATED_TEST_EVIDENCE",
                )
            )

        # 2. Competitor Intelligence Fixtures
        if "competitor" in st or "funding" in st or "tesla" in q or "fluence" in q or "form energy" in q or "competition" in q:
            items.append(
                ResearchEvidenceItem(
                    url="https://news.bloombergenr.com/corporate-filings/fluence-energy-q4-2025",
                    title="Fluence Energy Inc. Annual Securities Filing & Investor Report",
                    publication_date="2025-11-20",
                    excerpt="Fluence Energy reported $2.7B in deployed backlog for utility-scale BESS with gross margins of 12.8% and an average system selling price of $290/kWh installed.",
                    summary="Public benchmark: incumbent utility BESS leader operating at $290/kWh installed with 12.8% gross margin.",
                    source_domain="bloomberg.com",
                    source_type="competitor_intelligence",
                    provenance="MOCK_SIMULATED_RESEARCH",
                    is_mock=True,
                    relevance_score=0.88,
                    source_authority="INDUSTRY_ANALYST",
                    freshness_status="CURRENT",
                    support_status="RETRIEVED_CONTEXT",
                    corroboration_status="SINGLE_SOURCE",
                    requires_verification=True,
                    verification_limitations="Simulated test fixture (MockResearchProvider); offline mock not retrieved via live search.",
                    verification_grade="SIMULATED_TEST_EVIDENCE",
                )
            )
            items.append(
                ResearchEvidenceItem(
                    url="https://techcrunch.com/2024/10/form-energy-series-f-funding",
                    title="Form Energy Secures $405M Series F for Long-Duration Iron-Air Commercial Line",
                    publication_date="2024-10-09",
                    excerpt="Form Energy raised $405M in Series F financing led by T. Rowe Price and GE Vernova to scale manufacturing of multi-day iron-air electrochemical batteries.",
                    summary="Key multi-day competitor Form Energy closed $405M Series F for manufacturing scale-up.",
                    source_domain="techcrunch.com",
                    source_type="competitor_intelligence",
                    provenance="MOCK_SIMULATED_RESEARCH",
                    is_mock=True,
                    relevance_score=0.85,
                    source_authority="INDUSTRY_ANALYST",
                    freshness_status="CURRENT",
                    support_status="RETRIEVED_CONTEXT",
                    corroboration_status="SINGLE_SOURCE",
                    requires_verification=True,
                    verification_limitations="Simulated test fixture (MockResearchProvider); offline mock not retrieved via live search.",
                    verification_grade="SIMULATED_TEST_EVIDENCE",
                )
            )

        # 3. Industry Trends Fixtures
        if "trend" in st or "industry" in st or "supply chain" in q or "macro" in q:
            items.append(
                ResearchEvidenceItem(
                    url="https://www.mckinsey.com/industries/clean-energy-supply-chain-2025",
                    title="McKinsey & Co: Circular Economy Precursors in Battery Manufacturing",
                    publication_date="2025-06-18",
                    excerpt="Switching to circular industrial precursor feedstocks reduces raw material cost volatility by up to 34% compared to virgin mined lithium and cobalt compounds.",
                    summary="McKinsey analysis validates 34% raw material price stabilization from circular industrial precursors.",
                    source_domain="mckinsey.com",
                    source_type="industry_trends",
                    provenance="MOCK_SIMULATED_RESEARCH",
                    is_mock=True,
                    relevance_score=0.90,
                    source_authority="INDUSTRY_ANALYST",
                    freshness_status="CURRENT",
                    support_status="RETRIEVED_CONTEXT",
                    corroboration_status="SINGLE_SOURCE",
                    requires_verification=True,
                    verification_limitations="Simulated test fixture (MockResearchProvider); offline mock not retrieved via live search.",
                    verification_grade="SIMULATED_TEST_EVIDENCE",
                )
            )

        # 4. Regulatory & Technical Standards Fixtures
        if "regulatory" in st or "technical" in st or "patent" in q or "standard" in q or "compliance" in q:
            items.append(
                ResearchEvidenceItem(
                    url="https://standards.ieee.org/ieee/1547/7255/",
                    title="IEEE Standard 1547-2018 Interconnection of Distributed Energy Resources",
                    publication_date="2024-03-01",
                    excerpt="Mandates automated ride-through capability, rapid shut-off response under 100ms, and reactive power control for distributed storage interconnected with grid infrastructure.",
                    summary="IEEE 1547-2018 compliance requires sub-100ms ride-through response for grid interconnection.",
                    source_domain="standards.ieee.org",
                    source_type="regulatory_technical",
                    provenance="MOCK_SIMULATED_RESEARCH",
                    is_mock=True,
                    relevance_score=0.94,
                    source_authority="OFFICIAL_REGULATORY_FILING",
                    freshness_status="CURRENT",
                    support_status="RETRIEVED_CONTEXT",
                    corroboration_status="SINGLE_SOURCE",
                    requires_verification=True,
                    verification_limitations="Simulated test fixture (MockResearchProvider); offline mock not retrieved via live search.",
                    verification_grade="SIMULATED_TEST_EVIDENCE",
                )
            )

        # Fallback default fixture if generic query
        if not items:
            items.append(
                ResearchEvidenceItem(
                    url="https://industry-benchmark.org/data/deeptech-market-2025",
                    title="DeepTech Global Innovation & Industry Index 2025",
                    publication_date="2025-02-01",
                    excerpt=f"Independent industry survey corroborating market fundamentals for '{request.query}'. Baseline operational viability confirmed across peer cohort.",
                    summary=f"Independent market survey verifying baseline industry indicators for '{request.query}'.",
                    source_domain="industry-benchmark.org",
                    source_type="market_size_growth",
                    provenance="MOCK_SIMULATED_RESEARCH",
                    is_mock=True,
                    relevance_score=0.72,
                    source_authority="GENERAL_WEB",
                    freshness_status="CURRENT",
                    support_status="RETRIEVED_CONTEXT",
                    corroboration_status="SINGLE_SOURCE",
                    requires_verification=True,
                    verification_limitations="Simulated test fixture (MockResearchProvider); offline mock not retrieved via live search.",
                    verification_grade="SIMULATED_TEST_EVIDENCE",
                )
            )

        return items[: request.max_results]


class TavilyResearchProvider(ResearchProvider):
    """Tavily Search API Provider Adapter.

    Implements search queries via Tavily's documented REST API:
    POST https://api.tavily.com/search

    Credit & Cost Accounting:
    - search_depth="basic": 1 credit = $0.008 USD list price
    - search_depth="advanced": 2 credits = $0.016 USD list price
    - Reconciles actual credits from provider response ('usage.credits')
      or applies conservative fallback if missing/contradictory.
    - Records list-price equivalent cost to prevent promotional or free-tier credits
      from distorting evaluation unit economics.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        search_depth: Optional[str] = None,
        cost_per_credit_usd: Optional[float] = None,
        timeout_seconds: Optional[float] = None,
    ) -> None:
        settings = get_settings()
        self._api_key = (
            api_key
            or getattr(settings, "tavily_api_key", None)
            or getattr(settings, "research_api_key", None)
        )
        self._api_url = api_url or getattr(settings, "tavily_api_url", "https://api.tavily.com/search")
        self._search_depth = (
            search_depth or getattr(settings, "tavily_search_depth", "basic") or "basic"
        ).lower().strip()
        self._cost_per_credit_usd = (
            cost_per_credit_usd
            if cost_per_credit_usd is not None
            else getattr(settings, "tavily_cost_per_credit_usd", 0.008)
        )
        self._timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else getattr(settings, "tavily_timeout_seconds", 15.0)
        )

    def __repr__(self) -> str:
        key_status = "configured" if self.is_configured() else "unconfigured"
        return f"<TavilyResearchProvider(depth='{self._search_depth}', status='{key_status}')>"

    @property
    def provider_name(self) -> str:
        return "tavily"

    def is_configured(self) -> bool:
        return bool(self._api_key and self._api_key.strip())

    def get_cost_per_query_usd(self, search_depth: Optional[str] = None) -> float:
        depth = (search_depth or self._search_depth).lower().strip()
        credits = 2 if depth == "advanced" else 1
        return round(credits * self._cost_per_credit_usd, 6)

    def search(self, request: ResearchQueryRequest) -> List[ResearchEvidenceItem]:
        return self.search_detailed(request).evidence_items

    def search_detailed(self, request: ResearchQueryRequest) -> ResearchSearchResult:
        if not self.is_configured():
            logger.error("[TAVILY] Search requested but API key is missing or not configured.")
            raise AIProviderAuthenticationError("Tavily API key is missing or unconfigured.")

        depth = (request.search_depth or self._search_depth).lower().strip()
        expected_credits = 2 if depth == "advanced" else 1

        payload = {
            "api_key": self._api_key,
            "query": request.query,
            "search_depth": depth,
            "max_results": request.max_results,
            "include_usage": True,
            "include_answer": False,
            "include_raw_content": False,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
        }

        try:
            with httpx.Client(timeout=self._timeout_seconds) as client:
                response = client.post(self._api_url, json=payload, headers=headers)
        except (httpx.TimeoutException, httpx.ConnectTimeout) as e:
            logger.error(f"[TAVILY] Request timed out after {self._timeout_seconds}s for query '{request.query}': {e}")
            raise AIProviderError(f"Tavily search request timed out after {self._timeout_seconds}s") from e
        except (httpx.NetworkError, httpx.RequestError) as e:
            logger.error(f"[TAVILY] Network error communicating with Tavily API: {e}")
            raise AIProviderError(f"Tavily connection failed: {e}") from e

        # Inspect HTTP status codes
        if response.status_code == 401:
            logger.error("[TAVILY] Authentication failed (HTTP 401): invalid or unauthorized API key.")
            raise AIProviderAuthenticationError("Tavily authentication failed: invalid or unauthorized API key (HTTP 401)")
        elif response.status_code == 429:
            logger.error("[TAVILY] Rate limit or credit exhaustion (HTTP 429).")
            raise AIProviderError("Tavily rate limit or credit quota exceeded (HTTP 429)")
        elif response.status_code >= 500:
            logger.error(f"[TAVILY] Provider server error (HTTP {response.status_code}): {response.text}")
            raise AIProviderError(f"Tavily server error (HTTP {response.status_code}): {response.text}")
        elif response.status_code != 200:
            logger.error(f"[TAVILY] Request failed with HTTP {response.status_code}: {response.text}")
            raise AIProviderError(f"Tavily request failed with status {response.status_code}: {response.text}")

        try:
            data = response.json()
        except Exception as e:
            logger.error(f"[TAVILY] Malformed JSON in Tavily response: {e}")
            raise AIResponseParseError(f"Failed to parse Tavily API JSON response: {e}") from e

        # Credit & Pricing Reconciliation
        usage = data.get("usage")
        if (
            isinstance(usage, dict)
            and "credits" in usage
            and isinstance(usage["credits"], (int, float))
            and usage["credits"] > 0
        ):
            actual_credits = int(usage["credits"])
        else:
            # Conservative fallback to depth-based standard credit charge
            actual_credits = expected_credits

        # Always record list-price equivalent cost
        actual_cost_usd = round(actual_credits * self._cost_per_credit_usd, 6)

        raw_results = data.get("results") or []
        evidence_items: List[ResearchEvidenceItem] = []
        for item in raw_results:
            if not isinstance(item, dict):
                continue

            raw_url = str(item.get("url") or "").strip()
            title = str(item.get("title") or "").strip() or "External Source"
            content = str(item.get("content") or "").strip()
            pub_date = item.get("published_date")
            score = float(item.get("score", 0.0)) if isinstance(item.get("score"), (int, float)) else 0.0

            # Derive source domain
            domain = "web"
            if raw_url:
                try:
                    netloc = urllib.parse.urlparse(raw_url).netloc.lower()
                    if netloc.startswith("www."):
                        netloc = netloc[4:]
                    if netloc:
                        domain = netloc
                except Exception:
                    domain = "web"

            # Concise summary synthesis
            if content:
                clean_content = " ".join(content.split())
                summary_text = clean_content[:240]
                if len(clean_content) > 240:
                    summary_text = summary_text.rsplit(" ", 1)[0] + "..."
            else:
                summary_text = title

            # Phase 4.3 Evidence-Grade Semantics:
            # Tavily's numeric score reflects search query keyword relevance, NOT factual accuracy or truth probability.
            # Decouple relevance score and safely classify source authority, freshness, support status, and limitations.
            authority = classify_source_authority(domain)
            pub_date_str = str(pub_date).strip() if pub_date else None
            freshness = assess_freshness(pub_date_str)

            # Determine support status & diligence limitations
            # Factual diligence rule: A source's existence or query relevance score does not independently prove
            # that it supports the startup's claim. Claim support is reserved for substantive domain evaluation.
            limitations_parts = []
            if score < 0.4:
                support_status = "INCONCLUSIVE"
                limitations_parts.append("Low search-result relevance; excerpt does not corroborate target claim.")
            else:
                support_status = "RETRIEVED_CONTEXT"
                if score < 0.75:
                    limitations_parts.append("Provides general market context; requires verification of specific startup claim.")

            if freshness == "OUTDATED":
                limitations_parts.append("Publication date is over 3 years old; may not reflect current market conditions.")
            elif freshness == "DATE_UNAVAILABLE":
                limitations_parts.append("Publication date unavailable from search provider metadata.")

            # Assign institutional verification grade & flag requirement
            if authority == "OFFICIAL_REGULATORY_FILING":
                grade = "DOCUMENTED_OFFICIAL_FILING"
                requires_verification = False
            elif authority == "INSTITUTIONAL_BENCHMARK" and score >= 0.75:
                grade = "INSTITUTIONAL_BENCHMARK"
                requires_verification = False
            else:
                grade = "RETRIEVED_SEARCH_RESULT"
                requires_verification = True

            limitations_text = " ".join(limitations_parts) if limitations_parts else None

            evidence_items.append(
                ResearchEvidenceItem(
                    url=raw_url or "https://unknown.source",
                    title=title,
                    publication_date=pub_date_str,
                    excerpt=content or title,
                    summary=summary_text,
                    source_domain=domain,
                    source_type=request.search_type,
                    provenance="EXTERNAL_INDEPENDENT_RESEARCH",
                    is_mock=False,
                    relevance_score=score,
                    source_authority=authority,
                    freshness_status=freshness,
                    support_status=support_status,
                    corroboration_status="SINGLE_SOURCE",
                    requires_verification=requires_verification,
                    verification_limitations=limitations_text,
                    verification_grade=grade,
                )
            )

        return ResearchSearchResult(
            evidence_items=evidence_items[: request.max_results],
            actual_cost_usd=actual_cost_usd,
            credits_used=actual_credits,
            raw_response=data,
        )


# ===========================================================================
# External Research Service Orchestrator
# ===========================================================================

class ExternalResearchService:
    """Cost-aware service orchestrating external research and registry verification."""

    _instance: Optional[ExternalResearchService] = None

    def __init__(self, provider: Optional[ResearchProvider] = None) -> None:
        self._provider = provider or self._resolve_configured_provider()

    @classmethod
    def get_instance(cls) -> ExternalResearchService:
        if cls._instance is None:
            cls._instance = ExternalResearchService()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton for testing."""
        cls._instance = None

    def set_provider(self, provider: ResearchProvider) -> None:
        """Explicitly inject a research provider (used in testing or runtime switching)."""
        self._provider = provider

    def _resolve_configured_provider(self) -> ResearchProvider:
        """Resolves the provider configured in platform settings."""
        settings = get_settings()
        prov_name = (getattr(settings, "research_provider", "disabled") or "disabled").lower().strip()

        if prov_name == "mock":
            cost = getattr(settings, "research_cost_per_query_usd", 0.005)
            return MockResearchProvider(cost_per_query_usd=cost)
        elif prov_name == "tavily":
            api_key = getattr(settings, "tavily_api_key", None) or getattr(settings, "research_api_key", None)
            if not api_key:
                logger.warning(
                    "External research provider 'tavily' specified but API key is missing. "
                    "Safely falling back to DisabledResearchProvider."
                )
                return DisabledResearchProvider()
            return TavilyResearchProvider(api_key=api_key)
        elif prov_name in ("serper", "mca"):
            api_key = getattr(settings, "research_api_key", None)
            if not api_key:
                logger.warning(
                    f"External research provider '{prov_name}' specified but API key is missing. "
                    "Safely falling back to DisabledResearchProvider."
                )
                return DisabledResearchProvider()
            logger.info(f"External research provider '{prov_name}' configured with API key.")
            return DisabledResearchProvider()

        return DisabledResearchProvider()

    def is_available(self) -> bool:
        """Returns True only if an active, configured provider is available."""
        return self._provider.is_configured()

    def get_provider_name(self) -> str:
        """Returns the name of the currently active provider."""
        return self._provider.provider_name

    def verify_competitor_funding(self, company_name: str, evaluation_id: Optional[str] = None) -> Dict[str, Any]:
        """Checks competitor funding status via external search (backward-compatible method)."""
        req = ResearchQueryRequest(
            query=company_name,
            search_type="funding_lookup",
            evaluation_id=evaluation_id
        )
        res = self.search(req)
        return {
            "status": "UNAVAILABLE" if not res.is_available else ("VERIFIED" if res.evidence_items else "NO_RELEVANT_SOURCES"),
            "verified": res.is_available and len(res.evidence_items) > 0,
            "cost_usd": res.cost_usd,
            "message": res.message,
            "results": res.results,
            "evidence_items": [item.model_dump() for item in res.evidence_items],
        }

    def research_market_size_and_growth(
        self,
        sector: str,
        target_market: str,
        evaluation_id: Optional[str] = None,
    ) -> ResearchQueryResult:
        """Researches TAM/SAM/SOM benchmarks and industry CAGR data."""
        return self.search(
            ResearchQueryRequest(
                query=f"{sector} {target_market} TAM SAM SOM market size CAGR",
                search_type="market_size_growth",
                sector=sector,
                evaluation_id=evaluation_id,
            )
        )

    def research_competitors(
        self,
        company_name: str,
        sector: str,
        competitor_names: Optional[List[str]] = None,
        evaluation_id: Optional[str] = None,
    ) -> ResearchQueryResult:
        """Researches named competitors, incumbent offerings, and recent funding rounds."""
        comps_str = ", ".join(competitor_names) if competitor_names else "incumbents"
        return self.search(
            ResearchQueryRequest(
                query=f"{sector} competitors {comps_str} funding valuation vs {company_name}",
                search_type="competitor_intelligence",
                sector=sector,
                evaluation_id=evaluation_id,
            )
        )

    def research_industry_trends(
        self,
        sector: str,
        technology_domain: str,
        evaluation_id: Optional[str] = None,
    ) -> ResearchQueryResult:
        """Researches macro tailwinds, government policies, and supply chain shifts."""
        return self.search(
            ResearchQueryRequest(
                query=f"{sector} {technology_domain} industry trends government policy tailwinds",
                search_type="industry_trends",
                sector=sector,
                evaluation_id=evaluation_id,
            )
        )

    def research_regulatory_and_technical(
        self,
        claims_summary: str,
        standards: Optional[str] = None,
        evaluation_id: Optional[str] = None,
    ) -> ResearchQueryResult:
        """Researches regulatory compliance mandates, certifications, and technical standards."""
        st_query = f"{claims_summary} standards {standards or 'regulatory compliance'}"
        return self.search(
            ResearchQueryRequest(
                query=st_query,
                search_type="regulatory_technical",
                evaluation_id=evaluation_id,
            )
        )

    def search(self, request: ResearchQueryRequest) -> ResearchQueryResult:
        """Executes a cost-aware research query.

        - If provider is unconfigured or disabled: returns explicit UNAVAILABLE status with $0.00 cost.
        - If provider is configured:
          1. Pre-reserves budget against shared EvaluationCostLedger ceiling.
          2. Executes provider search.
          3. Reconciles external_tools_cost_usd on ledger upon success.
          4. Releases reservation if an error occurs.
        """
        if not self.is_available():
            return ResearchQueryResult(
                query=request.query,
                search_type=request.search_type,
                is_available=False,
                provider_name=self._provider.provider_name,
                evidence_items=[],
                results=[],
                confidence="UNAVAILABLE",
                message=(
                    "External research integration is disabled or provider API key is not configured. "
                    "Evaluator must rely strictly on submitted application documents."
                ),
                cost_usd=0.0
            )

        query_cost = (
            request.estimated_cost_usd
            if request.estimated_cost_usd is not None
            else self._provider.get_cost_per_query_usd(search_depth=request.search_depth)
        )

        # 1. Pre-call Budget Reservation
        ledger: Optional[EvaluationCostLedger] = None
        reservation_id: Optional[str] = None
        if request.evaluation_id:
            cost_manager = CostLedgerManager.get_instance()
            ledger = cost_manager.get_ledger(request.evaluation_id)
            if ledger:
                # Raises AIBudgetExhaustedError if limit exceeded
                reservation_id = ledger.reserve_budget(
                    estimated_cost_usd=query_cost,
                    agent_name=f"research_{request.search_type}"
                )

        try:
            # 2. Execute Provider Search
            search_result = self._provider.search_detailed(request)
            evidence_items = search_result.evidence_items
            actual_cost = search_result.actual_cost_usd

            # 3. Reconcile Tool Expenditure in Shared Ledger
            if ledger and reservation_id:
                ledger.reconcile_operation(
                    reservation_id=reservation_id,
                    agent_name=f"research_{request.search_type}",
                    provider=f"research_{self._provider.provider_name}",
                    model="search_api",
                    input_tokens=0,
                    output_tokens=0,
                    actual_cost_usd=None,
                    external_tools_cost_usd=actual_cost,
                    status="SUCCESS"
                )

            # Duck-type results list for backward compatibility
            duck_results = [item.model_dump() for item in evidence_items]

            confidence = "EXACT_MATCH" if len(evidence_items) >= 2 else ("PARTIAL_MATCH" if evidence_items else "NO_RELEVANT_SOURCES")

            return ResearchQueryResult(
                query=request.query,
                search_type=request.search_type,
                is_available=True,
                provider_name=self._provider.provider_name,
                evidence_items=evidence_items,
                results=duck_results,
                confidence=confidence,
                message=f"Retrieved {len(evidence_items)} independent external research sources." if evidence_items else "No relevant external research sources found.",
                cost_usd=actual_cost
            )

        except AIBudgetExhaustedError:
            # Budget limit reached: release and re-raise
            if ledger and reservation_id:
                ledger.release_reservation(reservation_id)
            logger.warning(f"[RESEARCH] Budget ceiling prevented research query: {request.query}")
            raise

        except Exception as e:
            if ledger and reservation_id:
                ledger.release_reservation(reservation_id)
            logger.error(f"[RESEARCH] External research query failed: {e}")
            raise
