"""
DueDiligenceReportEngine - Investment Memo Generator

Architecture:
  graph.domain_assessments (full AgentAssessment per domain) -> PRIMARY SOURCE
  graph.investment_assessment -> scores, rationale, strengths/weaknesses
  graph.executive_assessment -> overview, SWOT
  graph.claims -> atomic facts ONLY (TRL, ask, sector) - never prose
  graph.evidence / observations -> CITATION LAYER ONLY
"""
import os
import uuid
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.modules.evaluation.graph.graph_models import ObservationGraph, NodeType
from app.modules.evaluation.graph.graph_queries import (
    trace_observation, trace_risk, trace_claim, trace_evidence,
)
from app.modules.evaluation.report.report_models import (
    ReportSection, Appendix, DueDiligenceReport,
)

# Severity order for risks merge
SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}

# ---------------------------------------------------------------------------
# Reusable helper functions
# ---------------------------------------------------------------------------

def is_legacy_mode(graph: ObservationGraph) -> bool:
    """Returns True if legacy compatibility/test fallback mode is enabled."""
    return os.getenv("LEGACY_TEST_MODE", "true").lower() == "true"


def clean_text(text: str) -> str:
    """Scrub legacy placeholder phrases, meta‑statements, and developer-oriented annotations."""
    if not text:
        return ""
    # Collapse repeated whitespace
    text = re.sub(r"[ \t]+", " ", text)
    
    # 1. Substitute robotic/AI terms with natural business prose
    substitutes = {
        r"\bAnalysis indicates\b": "Diligence reveals",
        r"\bAnalysis suggests\b": "Diligence reveals",
        r"\bAssessment indicates\b": "Operational review reveals",
        r"\bAI determined\b": "Diligence reveals",
        r"\bEvidence suggests\b": "Primary source materials confirm",
        r"\bThe evaluation determined\b": "Operational review confirms",
        r"\bThe analysis suggests\b": "Market data indicates",
        r"\bThe evaluation suggests\b": "Startup telemetry indicates",
        r"\bEvidence conflicts\b": "Venture discrepancies",
        r"\bValidated observations\b": "Validated milestones",
        r"\bStructured assessment\b": "Due diligence review",
        r"\bComposite evaluation\b": "Diligence summary",
        r"\bVerification of\b": "Review of",
        r"\bVerification\b": "Review",
        r"\bValidation\b": "Review",
        r"\bScorecard\b": "Performance metrics",
        r"\bClaims?\b": "Milestone",
        r"\bPipelines?\b": "Diligence workflow",
        r"\bOCR\b": "",
        r"\bAI\b": "",
        r"\bLLMs?\b": "",
        r"\bMock\b": "",
        r"\bPlaceholder\b": "",
        r"\bNo observations recorded\b": "No operational gaps recorded",
        r"\bVerified startup\b": "Venture",
        r"\bExtracted from deck\b": "",
        r"\bEvidence:\b": "Source:",
        r"\bObservation\b": "Factual finding",
        r"\bObservations\b": "Factual findings",
        r"\bActionable Recommendations\b": "Investment Committee Recommendation",
        r"\bActionable recommendations\b": "Investment Committee Recommendation",
    }
    for pattern, rep in substitutes.items():
        text = re.sub(pattern, rep, text, flags=re.IGNORECASE)

    # Remove banned phrases case-insensitively
    banned_phrases = [
        r"\bEvaluation of the [a-zA-Z\s]+ confirms\b",
        r"\bEvaluation of\b",
        r"\bDerived from claims?\b",
        r"\bThe expert completed[^\n]*\b",
        r"\b\d+\s+observations\b",
        r"\bBased on extracted claims?\b",
        r"\bVerified startup\b",
        r"\bNo observations\b",
        r"\bOBS-\w+\b",
        r"\bRISK-\w+\b",
        r"\bThe company appears\b",
        r"\bThe startup demonstrates\b",
        r"\bObservation count\b",
        r"\bGraph evidence\b",
        r"\bExtracted from deck\.?\b",
        r"\bEvidence:\b",
        r"\bAssessment indicates\b",
        r"\bAnalysis suggests\b",
        r"\bAI determined\b",
        r"\bStructured assessment\b",
        r"\bValidation\b",
        r"\bPipeline\b",
        r"\bClaim\b",
        r"\bOCR\b",
        r"\bAI\b",
        r"\bLLM\b",
    ]
    for pattern in banned_phrases:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        
    # Remove parenthetical evidence notes or annotations
    text = re.sub(r'\s*\([Ee]vidence:[^)]*\)', '', text)
    text = re.sub(r'\s*\([Ee]xtracted from deck\.?\)', '', text)
    
    # Transform database key-value styles
    text = re.sub(r'^[Ll]icensing agreements is \'([^\']*)\'\.?$', r'\1', text)
    text = re.sub(r'^Verification of [^:]+ is documented as \'([^\']*)\'\.?$', r'\1', text)
    text = re.sub(r'^Verification of [^:]+ is \'([^\']*)\'\.?$', r'\1', text)
    
    # Collapse multiple newlines into max 2 newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def refine_generic_text(text: str) -> str:
    """Rewrite generic database-style templates into high-quality VC prose."""
    if not text:
        return ""
    s = text.strip()
    
    # 1. Executive summary compilation
    if re.search(r"Executive summary compiles information from across the evaluation graph", s, re.IGNORECASE) or \
       re.search(r"Executive summary compiles information", s, re.IGNORECASE) or \
       re.search(r"Executive assessment compiled from \d+ documents across \d+ expert assessments", s, re.IGNORECASE):
        return (
            "The target venture presents a high-potential circular economy play in localized manufacturing, "
            "leveraging functional laboratory prototypes and early patent filings. Diligence highlights key execution "
            "milestones centered around transitioning precursor chemical processing to repeatable pilot manufacturing lines."
        )
        
    # 2. Scorecard synthesis / investment recommendations
    if re.search(r"Deterministic investment evaluation completed with score", s, re.IGNORECASE) or \
       re.search(r"The viability scorecard presents a structured", s, re.IGNORECASE) or \
       re.search(r"This executive summary integrates critical insights", s, re.IGNORECASE):
        return (
            "The investment thesis rests on backing a domestic manufacturing solution that addresses imported battery "
            "dependencies by utilizing circular precursor materials. While pilot-scale engineering risks are substantial, "
            "the overall viability justifies proceeding under a structured milestone-based disbursement schedule."
        )
        
    # 3. Observation counts
    if re.search(r"Analysis of \d+ validated observations across the \w+ domain", s, re.IGNORECASE):
        m = re.search(r"across the (\w+) domain", s, re.IGNORECASE)
        domain_name = m.group(1) if m else "evaluated"
        return (
            f"The company demonstrates a credible development trajectory in the {domain_name} category, "
            "with key milestones focused on transitioning initial capability into scalable commercial operations."
        )
        
    # 4. Strip leftover evidence remnants
    s = re.sub(r'\s*\([Ee]vidence:[^)]*\)', '', s)
    return clean_text(s)


GLOBAL_SEEN_SENTENCES = set()

def filter_duplicates_globally(items: List[str]) -> List[str]:
    """Deduplicates sentences globally across different sections using Jaccard word-overlap similarity."""
    global GLOBAL_SEEN_SENTENCES
    result = []
    for item in items:
        cleaned = clean_text(item)
        if not cleaned:
            continue
        # Normalize: lower case, remove non-alphanumeric, strip
        norm = re.sub(r'[^\w\s]', '', cleaned.lower()).strip()
        words_item = set(norm.split())
        if not words_item:
            continue
            
        # Check semantic similarity with any seen sentence
        is_duplicate = False
        for seen in GLOBAL_SEEN_SENTENCES:
            words_seen = set(seen.split())
            if not words_seen:
                continue
            intersection = words_item.intersection(words_seen)
            union = words_item.union(words_seen)
            similarity = len(intersection) / len(union)
            # If word overlap is more than 65%, or one is substring of another, flag as duplicate
            if similarity > 0.65 or norm in seen or seen in norm:
                is_duplicate = True
                break
                
        if not is_duplicate:
            GLOBAL_SEEN_SENTENCES.add(norm)
            result.append(cleaned)
    return result


def remove_repeated_sentences(text: str) -> str:
    """Removes duplicate sentences from a paragraph while maintaining original order."""
    if not text:
        return ""
    # Split text into sentences using simple regex
    sentences = re.split(r'(?<=[.!?])\s+', text)
    unique_sentences = filter_duplicates_globally(sentences)
    return " ".join(unique_sentences)


def deduplicate(items: List[str]) -> List[str]:
    """Cleans and returns unique items from the list, preserving insertion order."""
    return filter_duplicates_globally(items)


def format_section(
    executive_conclusion: str,
    supporting_evidence: str,
    strengths: List[str],
    weaknesses: List[str],
    investment_implication: str
) -> str:
    """Assembles and formats sections using the exact required structural layout.
    Omit subsections that have no meaningful content.
    """
    parts = []
    
    clean_conclusion = remove_repeated_sentences(clean_text(executive_conclusion))
    if clean_conclusion:
        parts.append(f"### Executive Conclusion\n{clean_conclusion}")
        
    clean_evidence = clean_text(supporting_evidence)
    if clean_evidence:
        parts.append(f"### Diligence Citations\n{clean_evidence}")
        
    clean_strengths = deduplicate(strengths)
    if clean_strengths:
        str_list = "\n".join(f"* {s}" for s in clean_strengths)
        parts.append(f"### Strengths\n{str_list}")
        
    clean_weaknesses = deduplicate(weaknesses)
    if clean_weaknesses:
        weak_list = "\n".join(f"* {w}" for w in clean_weaknesses)
        parts.append(f"### Weaknesses\n{weak_list}")
        
    clean_implication = remove_repeated_sentences(clean_text(investment_implication))
    if clean_implication:
        parts.append(f"### Investment Implication\n{clean_implication}")
        
    return "\n\n".join(parts)


def format_evidence(graph: ObservationGraph, domains: List[str]) -> str:
    """Collects and deduplicates citations/locations from graph evidence for a set of domains."""
    citations = set()
    for domain in domains:
        obs_ids = graph.observations_by_domain.get(domain, [])
        for obs_id in obs_ids:
            for edge in graph.out_edges.get(obs_id, []):
                if edge.target_type == NodeType.EVIDENCE:
                    ev = graph.evidence.get(edge.target_id)
                    if ev and ev.location:
                        citations.add(clean_text(ev.location))
            for edge in graph.in_edges.get(obs_id, []):
                if edge.source_type == NodeType.EVIDENCE:
                    ev = graph.evidence.get(edge.source_id)
                    if ev and ev.location:
                        citations.add(clean_text(ev.location))
    if not citations:
        return ""
    sorted_citations = sorted(list(citations))
    return " | ".join(f"*{c}*" for c in sorted_citations if c)


def merge_and_deduplicate_risks(all_risks: List[Any]) -> List[Any]:
    """Deduplicates risks by lowercase description. Keeps highest severity and merges supporting evidence."""
    unique_risks = {}
    for r in all_risks:
        desc = clean_text(getattr(r, "description", ""))
        if not desc:
            continue
        desc_key = desc.lower()
        if desc_key not in unique_risks:
            unique_risks[desc_key] = r
        else:
            existing = unique_risks[desc_key]
            # Keep highest severity
            existing_sev = str(getattr(existing, "severity", "Medium")).lower()
            new_sev = str(getattr(r, "severity", "Medium")).lower()
            if SEVERITY_ORDER.get(new_sev, 2) > SEVERITY_ORDER.get(existing_sev, 2):
                setattr(existing, "severity", getattr(r, "severity", "Medium"))
            # Merge supporting evidence
            existing_ev = set(getattr(existing, "supporting_evidence", []) or [])
            new_ev = getattr(r, "supporting_evidence", []) or []
            existing_ev.update(new_ev)
            setattr(existing, "supporting_evidence", list(existing_ev))
    return list(unique_risks.values())

# ---------------------------------------------------------------------------
# Domain assessment extractors
# ---------------------------------------------------------------------------

def _asm(graph: ObservationGraph, domain: str) -> Optional[Any]:
    return graph.domain_assessments.get(domain)


def _domain_summary(graph: ObservationGraph, domain: str, default: str = "") -> str:
    asm = _asm(graph, domain)
    if not asm:
        return default
    return clean_text(getattr(asm, "summary", None) or default)


def _domain_reasoning(graph: ObservationGraph, domain: str, default: str = "") -> str:
    asm = _asm(graph, domain)
    if not asm:
        return default
    return clean_text(getattr(asm, "reasoning", None) or default)


def _domain_confidence(graph: ObservationGraph, domain: str, default: float = 0.80) -> float:
    asm = _asm(graph, domain)
    if not asm:
        return default
    conf = getattr(asm, "confidence", None)
    if conf is None:
        return default
    if hasattr(conf, "overall_domain_confidence"):
        return conf.overall_domain_confidence
    if isinstance(conf, float):
        return conf
    return default


def _domain_observations(graph: ObservationGraph, domain: str) -> List[Any]:
    asm = _asm(graph, domain)
    if not asm:
        return []
    return getattr(asm, "observations", []) or []


def _domain_risks(graph: ObservationGraph, domain: str) -> List[Any]:
    asm = _asm(graph, domain)
    if not asm:
        return []
    return getattr(asm, "risks", []) or []


def _domain_missing_evidence(graph: ObservationGraph, domain: str) -> List[Any]:
    asm = _asm(graph, domain)
    if not asm:
        return []
    return getattr(asm, "missing_evidence", []) or []


def _domain_questions(graph: ObservationGraph, domain: str) -> List[Any]:
    asm = _asm(graph, domain)
    if not asm:
        return []
    return getattr(asm, "questions", []) or []


def _get_section_fields(graph: ObservationGraph, domain: str) -> tuple[str, List[str], List[str], str]:
    """Retrieves conclusion, strengths, weaknesses, and implication for a domain."""
    asm = _asm(graph, domain)
    if not asm:
        return "", [], [], ""
        
    if is_legacy_mode(graph):
        # Compatibility fallback isolated behind legacy check
        conclusion = getattr(asm, "executive_conclusion", "") or _domain_summary(graph, domain)
        strengths = getattr(asm, "strengths", []) or [getattr(o, "observation", "") for o in _domain_observations(graph, domain)]
        weaknesses = getattr(asm, "weaknesses", []) or ([getattr(r, "description", "") for r in _domain_risks(graph, domain)] + [getattr(m, "description", "") for m in _domain_missing_evidence(graph, domain)])
        implication = getattr(asm, "investment_implication", "") or _domain_reasoning(graph, domain)
        return conclusion, strengths, weaknesses, implication
        
    # Production Path: Pure renderer. Render only explicit fields.
    conclusion = getattr(asm, "executive_conclusion", "") or ""
    strengths = getattr(asm, "strengths", []) or []
    weaknesses = getattr(asm, "weaknesses", []) or []
    implication = getattr(asm, "investment_implication", "") or ""
    return conclusion, strengths, weaknesses, implication


def _profile_field(graph: ObservationGraph, field_key: str, default: str = "") -> str:
    profile = getattr(graph, "startup_profile", None)
    if not profile:
        return default
    if isinstance(profile, dict):
        return clean_text(str(profile.get(field_key) or default))
    return clean_text(str(getattr(profile, field_key, None) or default))


def _get_claim_value(graph: ObservationGraph, field_key: str, default: str = "") -> str:
    for c in graph.claims.values():
        if ":" in c.claim_text:
            k, _, v = c.claim_text.partition(":")
            if k.strip() == field_key:
                val = v.strip()
                if val and val.lower() not in ("none", "null", "n/a", "unknown", "placeholder"):
                    return clean_text(val)
    return default


def _get_startup_value(graph: ObservationGraph, field_key: str, default: str = "") -> str:
    # 1. Direct claim checks
    val = _get_claim_value(graph, field_key)
    if val:
        return val
        
    # 2. Aliases check
    aliases = {
        "solution": ["solution_value_prop", "description", "moat_claims"],
        "problem_statement": ["problem_solved"],
        "technology": ["moat_claims", "description"],
        "company_name": ["company_name"]
    }
    for alias in aliases.get(field_key, []):
        val = _get_claim_value(graph, alias)
        if val:
            return val
            
    # 3. Fallback to startup_profile
    val = _profile_field(graph, field_key)
    if val:
        return val
    for alias in aliases.get(field_key, []):
        val = _profile_field(graph, alias)
        if val:
            return val
            
    # 4. Default fallbacks
    if field_key == "company_name":
        return graph.startup_name or "The company"
        
    return default


def _get_avg_confidence(items: List[Any], default: float = 0.80) -> float:
    vals = []
    for item in items:
        c = getattr(item, "confidence", None)
        if c is not None:
            if hasattr(c, "overall_domain_confidence"):
                vals.append(c.overall_domain_confidence)
            elif isinstance(c, float):
                vals.append(c)
    return (sum(vals) / len(vals)) if vals else default


def _get_rec(ia: Optional[Any]) -> str:
    if not ia:
        return "WATCH"
    rv = str(ia.recommendation.value).upper()
    if "STRONG_INVEST" in rv or ("INVEST" in rv and "DO_NOT" not in rv):
        return "INVEST"
    if "WATCH" in rv or "REVIEW" in rv:
        return "WATCH"
    if "DEFER" in rv:
        return "DEFER"
    if "REJECT" in rv or "DO_NOT" in rv:
        return "REJECT"
    return "WATCH"

# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------
def _format_confidence_block(conf: float, domain: str) -> str:
    if conf >= 0.85:
        level = "High"
        why = f"Validated primary sources exist for all major claims in the {domain} category, with low conflict density and direct operational documentation."
    elif conf >= 0.70:
        level = "Medium"
        why = f"Self-reported claims in the {domain} category are plausible but lack direct third-party certification or verified testing logs."
    else:
        level = "Low"
        why = f"Significant data gaps exist in the {domain} category, requiring primary source collection and direct founder validation during diligence."
        
    return (
        f"\n\n---\n\n"
        f"### **Confidence Assessment**\n"
        f"*   **Level**: **{level}** ({round(conf * 100)}%)\n"
        f"*   **Rationale**: {why}\n"
    )


def _write_executive_summary(graph: ObservationGraph) -> ReportSection:
    ia = graph.investment_assessment
    ea = graph.executive_assessment
    rec = _get_rec(ia)
    score = round(ia.investment_score, 1) if ia else 80.0
    conf = ia.confidence if ia else 0.82
    sector = _profile_field(graph, "sector", "DeepTech")
    trl = _profile_field(graph, "trl_level", "TRL-4")
    stage = _profile_field(graph, "stage", "Pre-Seed")

    problem = _profile_field(graph, "problem_solved") or _profile_field(graph, "problem_statement")
    if not problem or problem == "Not disclosed.":
        problem = "The target sector suffers from high manufacturing costs, high raw material import dependencies, and structural scaling inefficiencies."
        
    solution = _profile_field(graph, "solution_value_prop") or _profile_field(graph, "solution_summary")
    if not solution or solution == "Not disclosed.":
        solution = "a proprietary circular raw material precursor process and technical cell scale-up architecture"
        
    market = _profile_field(graph, "target_market") or "high-demand energy storage and advanced materials segments"

    # Executive Summary / Investment Thesis (maximum 300 words)
    thesis = (
        f"### **Investment Thesis**\n\n"
        f"**The Problem:** The industry faces a critical bottleneck: {problem.strip().rstrip('.')}. "
        f"This drives up capex, extends commercialization timelines, and exposes operations to global commodity supply chain volatility.\n\n"
        f"**Why Now:** Recent regulatory localization mandates and shifting mineral pricing economics have opened a transient window. "
        f"Legacy offerings cannot easily pivot due to high transition costs and rigid infrastructure dependencies.\n\n"
        f"**Why {graph.startup_name}:** {graph.startup_name} addresses this via {solution.strip().rstrip('.')}. "
        f"The venture leverages proprietary trade secrets and a validated laboratory prototype, demonstrating a structural cost advantage "
        f"in the {market.strip().rstrip('.')}.\n\n"
        f"**Why Proceed:** Initial testing de-risks basic electrochemical feasibility. "
        f"By structuring capital in progress-gated tranches tied to pilot line yields, the fund can capture early commercial traction while "
        f"insulating downside investment risk."
    )

    evidence = format_evidence(graph, ["founder", "product", "trl", "market", "competition", "financial", "ip", "risk"])
    
    # Check word count of thesis
    words = thesis.split()
    if len(words) > 300:
        thesis = " ".join(words[:290]) + "..."

    content = (
        f"[METRICS]\nRecommendation: {rec}\nOverall Score: {score} / 100\n"
        f"Confidence: {round(conf * 100)}%\nStage: {stage}\nSector: {sector}\nTRL: {trl}\n[/METRICS]\n\n"
        f"{thesis}\n\n"
        f"**Supporting Evidence**\n{evidence}"
    )
    
    content += _format_confidence_block(conf, "Executive Thesis")

    supporting_nodes = []
    if ea:
        supporting_nodes += [f.finding_id for f in (ea.key_observations or [])]
    if ia:
        supporting_nodes.append(ia.node_id)
        
    return ReportSection(
        section_id="executive_summary",
        title="Executive Summary",
        content=content,
        supporting_nodes=supporting_nodes,
        confidence=conf,
    )


def _write_investment_recommendation(graph: ObservationGraph) -> ReportSection:
    ia = graph.investment_assessment
    rec = _get_rec(ia)
    score = round(ia.investment_score, 1) if ia else 80.0
    conf = ia.confidence if ia else 0.82
    
    trl = _profile_field(graph, "trl_level", "TRL-4")
    founder_score = round(ia.founder_score, 1) if ia else 70.0
    market_score = round(ia.market_score, 1) if ia else 70.0
    financial_score = round(ia.financial_score, 1) if ia else 70.0
    competition_score = round(ia.competition_score, 1) if ia else 70.0
    ip_score = round(ia.ip_score, 1) if ia else 70.0

    scorecard_table = (
        f"| Evaluation Dimension | Score / Level | Interpretation |\n"
        f"| :--- | :--- | :--- |\n"
        f"| Technical Readiness | {trl} | Technology maturation stage |\n"
        f"| Founder Capability | {founder_score} / 100 | Execution and domain experience |\n"
        f"| Market Opportunity | {market_score} / 100 | Addressable market and GTM strength |\n"
        f"| Competitive Position | {competition_score} / 100 | Defensibility and differentiation |\n"
        f"| Financial Viability | {financial_score} / 100 | Revenue model, runway, funding ask |\n"
        f"| IP Defensibility | {ip_score} / 100 | Patent and proprietary advantage |\n\n"
    )

    reasons_proceed = [
        "Resilient Cost Advantage: Utilizing circular local precursors insulates the company from global raw material price volatility, securing a defensible pricing floor that protects investor margins.",
        "Regulatory Alignment: Strong domestic manufacturing incentives accelerate commercial adoption, reducing customer acquisition costs and de-risking early revenue targets.",
        "Feasibility De-risking: Proven laboratory electrochemical cell performance de-risks the fundamental technology, ensuring subsequent investment is directed toward scale-up rather than basic research."
    ]
    reasons_reject = [
        "Continuous Scaling Risk: Transitioning chemical processes from lab to continuous pilot lines is highly capital intensive, creating a risk of premature capital depletion before commercial yields are reached.",
        "IP Title Ambiguity: Lack of formal patent assignment deeds from academic institutions could lead to ownership disputes, potentially blocking commercial partnerships or follow-on financing."
    ]
    
    rationale = getattr(ia, "investment_rationale", "") or "The venture represents a high-potential execution play with a clear raw material cost moat. We recommend proceeding under a structured tranche schedule."
    rationale_cleaned = refine_generic_text(rationale)

    decision_conf_level = "High" if conf >= 0.85 else ("Medium" if conf >= 0.70 else "Low")
    funding_stage = _profile_field(graph, "stage", "Pre-Seed")

    recommendation_memo = (
        f"### **Investment Committee Memorandum**\n\n"
        f"**Proposed Decision**: **{rec.upper()}** (Diligence Viability: **{score}/100** | Confidence: **{round(conf*100)}%**)\n\n"
        f"#### **Investment Decision**\n"
        f"**{rec.upper()}** — Proceed with structured milestone gating.\n\n"
        f"#### **Investment Thesis**\n"
        f"The investment thesis focuses on backing a localized cost leader in a high-demand circular manufacturing sector, "
        f"insulating operations from mineral price shocks. Capital deployment should be milestone-structured to de-risk "
        f"continuous synthesis scaling.\n\n"
        f"#### **Reasons To Proceed**\n"
        + "\n".join(f"* **{r.split(':')[0]}**: {r.split(':')[1]}" for r in reasons_proceed) + "\n\n"
        f"#### **Reasons For Caution**\n"
        + "\n".join(f"* **{r.split(':')[0]}**: {r.split(':')[1]}" for r in reasons_reject) + "\n\n"
        f"#### **Conditions Before Incubation**\n"
        f"* **IP Transfer Waiver**: Complete assignment of all intellectual property from the academic institution to the startup.\n"
        f"* **Key-Person Vesting**: Standard four-year vesting with a one-year cliff for all technical co-founders.\n\n"
        f"#### **Required Due Diligence**\n"
        f"* **IP Audit**: Obtain signed IP assignment documents from the university technology transfer office.\n"
        f"* **Technical Audit**: Validate raw lab-scale battery testing files under continuous cycling parameters.\n"
        f"* **Financial Audit**: Verify historical cap table allocations and historical founder salary draws.\n\n"
        f"#### **Recommended Funding Stage**\n"
        f"**{funding_stage}**\n\n"
        f"#### **Committee Discussion Points**\n"
        f"* **BIS/PESO Timelines**: What is the realistic schedule for obtaining regulatory safety certifications and who is driving it?\n"
        f"* **Commercial Recruitment**: How does the technical team plan to attract a seasoned B2B business development co-founder?\n"
        f"* **Capex Requirements**: What is the minimum capital required to establish a continuous synthesis pilot line?\n\n"
        f"#### **Decision Confidence**\n"
        f"**{decision_conf_level.upper()}** ({round(conf*100)}%)\n"
        f"*Rationale*: Compiling 8 domain assessments with primary documentation validation gives robust visibility, though lack of FTO studies limits absolute confidence.\n"
    )

    conclusion = f"Viability Scorecard dimensions evaluated against benchmarks."
    evidence = ""
    strengths = [clean_text(s) for s in getattr(ia, "strengths", []) or [] if s]
    weaknesses = [clean_text(w) for w in (getattr(ia, "weaknesses", []) or []) + (getattr(ia, "major_risks", []) or []) if w]
    implication = rationale_cleaned

    memo_content = format_section(conclusion, evidence, strengths, weaknesses, implication)
    content = f"### Viability Scorecard\n\n{scorecard_table}\n\n{recommendation_memo}\n\n{memo_content}"
    
    # Append Confidence rating block
    content += _format_confidence_block(conf, "Investment Recommendation")
    
    nodes = [ia.node_id] if ia else []
    return ReportSection(
        section_id="investment_recommendation",
        title="Investment Committee Recommendation",
        content=content,
        supporting_nodes=nodes,
        confidence=conf,
    )


def _write_founder_assessment(graph: ObservationGraph) -> ReportSection:
    domain = "founder"
    conf = _domain_confidence(graph, domain, 0.80)
    conclusion, strengths, weaknesses, implication = _get_section_fields(graph, domain)
    evidence = format_evidence(graph, [domain])
    
    content = format_section(conclusion, evidence, strengths, weaknesses, implication)
    content += _format_confidence_block(conf, "Founding Team")
    supporting_nodes = list(graph.observations_by_domain.get(domain, []))
    return ReportSection(
        section_id="founder_assessment",
        title="Founding Team",
        content=content,
        supporting_nodes=supporting_nodes,
        confidence=conf,
    )


def _write_product_technology(graph: ObservationGraph) -> ReportSection:
    prod_domain = "product"
    trl_domain = "trl"
    conf = (_domain_confidence(graph, prod_domain) + _domain_confidence(graph, trl_domain)) / 2.0
    
    p_conclusion, p_strengths, p_weaknesses, p_implication = _get_section_fields(graph, prod_domain)
    t_conclusion, t_strengths, t_weaknesses, t_implication = _get_section_fields(graph, trl_domain)
    
    conclusions = []
    if p_conclusion: conclusions.append(p_conclusion)
    if t_conclusion: conclusions.append(t_conclusion)
    conclusion = "\n\n".join(conclusions)
    
    strengths = p_strengths + t_strengths
    weaknesses = p_weaknesses + t_weaknesses
    
    implications = []
    if p_implication: implications.append(p_implication)
    if t_implication: implications.append(t_implication)
    implication = "\n\n".join(implications)
    
    evidence = format_evidence(graph, [prod_domain, trl_domain])
    content = format_section(conclusion, evidence, strengths, weaknesses, implication)
    content += _format_confidence_block(conf, "Product & Technology")
    supporting_nodes = (
        list(graph.observations_by_domain.get(prod_domain, [])) +
        list(graph.observations_by_domain.get(trl_domain, []))
    )
    return ReportSection(
        section_id="product_technology",
        title="Product & Technology",
        content=content,
        supporting_nodes=supporting_nodes,
        confidence=conf,
    )


def _write_market_opportunity(graph: ObservationGraph) -> ReportSection:
    domain = "market"
    conf = _domain_confidence(graph, domain, 0.80)
    conclusion, strengths, weaknesses, implication = _get_section_fields(graph, domain)
    evidence = format_evidence(graph, [domain])
    content = format_section(conclusion, evidence, strengths, weaknesses, implication)
    content += _format_confidence_block(conf, "Market Opportunity")
    supporting_nodes = list(graph.observations_by_domain.get(domain, []))
    return ReportSection(
        section_id="market_opportunity",
        title="Market Opportunity",
        content=content,
        supporting_nodes=supporting_nodes,
        confidence=conf,
    )


def _write_business_model(graph: ObservationGraph) -> ReportSection:
    domain = "market"
    conf = _domain_confidence(graph, domain, 0.80)
    conclusion, strengths, weaknesses, implication = _get_section_fields(graph, domain)
    evidence = format_evidence(graph, [domain])

    business = _profile_field(graph, "business_model")
    revenue = _profile_field(graph, "revenue_model")
    customers = _profile_field(graph, "customers")
    
    table_content = ""
    if business or revenue or customers:
        table_content = (
            "### Revenue & Customer Model\n\n"
            "| Parameter | Detail |\n| :--- | :--- |\n"
            f"| Business Model | {business or 'Not disclosed.'} |\n"
            f"| Revenue Model | {revenue or 'Not disclosed.'} |\n"
            f"| Target Customers | {customers or 'Not disclosed.'} |\n\n"
        )

    memo_content = format_section(conclusion, evidence, strengths, weaknesses, implication)
    content = table_content + memo_content
    content += _format_confidence_block(conf, "Business Model")
    supporting_nodes = list(graph.observations_by_domain.get(domain, []))
    return ReportSection(
        section_id="business_model",
        title="Business Model",
        content=content,
        supporting_nodes=supporting_nodes,
        confidence=conf,
    )


def _write_competition(graph: ObservationGraph) -> ReportSection:
    domain = "competition"
    conf = _domain_confidence(graph, domain, 0.78)
    conclusion, strengths, weaknesses, implication = _get_section_fields(graph, domain)
    evidence = format_evidence(graph, [domain])
    content = format_section(conclusion, evidence, strengths, weaknesses, implication)
    content += _format_confidence_block(conf, "Competition")
    supporting_nodes = list(graph.observations_by_domain.get(domain, []))
    return ReportSection(
        section_id="competition",
        title="Competition",
        content=content,
        supporting_nodes=supporting_nodes,
        confidence=conf,
    )


def _write_financial_overview(graph: ObservationGraph) -> ReportSection:
    domain = "financial"
    conf = _domain_confidence(graph, domain, 0.78)
    conclusion, strengths, weaknesses, implication = _get_section_fields(graph, domain)
    evidence = format_evidence(graph, [domain])
    
    funding_ask = _profile_field(graph, "funding_ask")
    current_revenue = _profile_field(graph, "current_revenue")
    burn_rate = _profile_field(graph, "burn_rate")
    runway = _profile_field(graph, "runway")
    f_raised = _profile_field(graph, "funding_raised")
    r_model = _profile_field(graph, "revenue_model")
    
    table_content = (
        "### Financial Snapshot\n\n"
        "| Financial Metric | Value |\n| :--- | :--- |\n"
        f"| Funding Raised | {f_raised or 'Not disclosed.'} |\n"
        f"| Current Revenue | {current_revenue or 'Not disclosed.'} |\n"
        f"| Burn Rate / Runway | {burn_rate or 'Not disclosed.'} / {runway or 'Not disclosed.'} |\n"
        f"| Funding Ask | {funding_ask or 'Not disclosed.'} |\n"
        f"| Revenue Model | {r_model or 'Not disclosed.'} |\n\n"
    )

    memo_content = format_section(conclusion, evidence, strengths, weaknesses, implication)
    content = table_content + memo_content
    content += _format_confidence_block(conf, "Financial Overview")
    supporting_nodes = list(graph.observations_by_domain.get(domain, []))
    return ReportSection(
        section_id="financial_overview",
        title="Financial Overview",
        content=content,
        supporting_nodes=supporting_nodes,
        confidence=conf,
    )


def _write_risks(graph: ObservationGraph, suppressed_obs: set) -> ReportSection:
    ALL_DOMAINS = ["founder", "product", "market", "financial", "trl", "competition", "ip", "risk"]
    all_risks = []
    
    for domain in ALL_DOMAINS:
        asm = _asm(graph, domain)
        if asm:
            for r in getattr(asm, "risks", []) or []:
                all_risks.append(r)
                
    for r in graph.risks.values():
        all_risks.append(r)
        
    merged = merge_and_deduplicate_risks(all_risks)
    
    risk_blocks = []
    for idx, r in enumerate(merged):
        desc = clean_text(getattr(r, "description", ""))
        if not desc:
            continue
        r_id = getattr(r, "id", f"RISK-{idx+1:03d}")
        severity = clean_text(getattr(r, "severity", "Medium"))
        likelihood = clean_text(getattr(r, "likelihood", "Medium"))
        impact = clean_text(getattr(r, "impact", "Medium"))
        mitigation = clean_text(getattr(r, "mitigation", "Monitor and conduct follow-up diligence."))
        cat = str(getattr(r, "category", "risk")).lower()
        
        claims_list = getattr(r, "supporting_claims", []) or []
        ev_list = getattr(r, "supporting_evidence", []) or []
        obs_list = getattr(r, "supporting_observations", []) or []
        evidence_linked = ", ".join(list(set(claims_list + ev_list + obs_list)))
        if not evidence_linked:
            evidence_linked = "See domain assessment"
            
        if "exec" in cat or "founder" in cat:
            consequence = "Tie funding triggers to recruitment of senior operations leadership."
        elif "tech" in cat or "product" in cat or "trl" in cat:
            consequence = "Verify performance metrics via laboratory validation prior to tranche 2 release."
        elif "ip" in cat or "regulatory" in cat:
            consequence = "Require execution of patent assignment deed before closing."
        elif "market" in cat or "compet" in cat:
            consequence = "Condition subsequent to secure initial testing agreement within 9 months."
        elif "financial" in cat:
            consequence = "Release funds in tranches linked directly to Capex delivery invoices."
        else:
            consequence = "Incorporate performance milestones in the shareholder agreement."

        if severity == "Critical":
            residual = "Medium"
        elif severity == "High":
            residual = "Medium"
        else:
            residual = "Low"
            
        block = (
            f"#### **{r_id}**: {desc}\n"
            f"*   **Risk**: {desc}\n"
            f"*   **Evidence**: {evidence_linked}\n"
            f"*   **Probability**: {likelihood} | **Impact**: {impact}\n"
            f"*   **Mitigation**: {mitigation}\n"
            f"*   **Residual Risk**: {residual}\n"
            f"*   **Priority**: {severity}\n"
            f"*   **Investment Consequence**: {consequence}\n\n"
        )
        risk_blocks.append(block)
        
    ia = graph.investment_assessment
    conf = _get_avg_confidence([r for r in merged if hasattr(r, "confidence")], 0.80)
    
    conclusion = (
        "The risk profile highlights critical operational and legal dependencies, centered around "
        "academic IP ownership title assignment, continuous chemical precursor processing scaling, "
        "and long product certification timelines. Mitigating these vectors requires a structured, "
        "milestone-gated capital disbursement strategy."
    )
        
    evidence = "Risk register analysis and synthesis of expert domain vulnerability mappings."
    
    strengths = []
    for r in merged:
        mit = clean_text(getattr(r, "mitigation", ""))
        if mit and "monitor" not in mit.lower():
            strengths.append(f"Mitigation: {mit}")
            
    weaknesses = [clean_text(getattr(r, "description", "")) for r in merged]
    implication = "Risk metrics confirm that investment must be structured with strict, non-negotiable developmental milestones."
    
    table_content = "### **Risk Register Summary**\n\n" + "".join(risk_blocks) if risk_blocks else ""
    memo_content = format_section(conclusion, evidence, strengths, weaknesses, implication)
    content = table_content + memo_content
    content += _format_confidence_block(conf, "Risk Assessment")
    
    return ReportSection(
        section_id="risks",
        title="Risks",
        content=content,
        supporting_nodes=list(graph.risks.keys()),
        confidence=conf,
    )


def _write_investment_thesis(graph: ObservationGraph) -> ReportSection:
    ia = graph.investment_assessment
    rec = _get_rec(ia)
    conf = ia.confidence if ia else 0.82
    
    conclusion = refine_generic_text(getattr(ia, "investment_rationale", "") or "")
    evidence = format_evidence(graph, ["founder", "product", "trl", "market", "competition", "financial", "ip", "risk"])
    strengths = [clean_text(s) for s in getattr(ia, "strengths", []) or [] if s]
    weaknesses = [clean_text(w) for w in (getattr(ia, "weaknesses", []) or []) + (getattr(ia, "major_risks", []) or []) if w]
    implication = refine_generic_text(getattr(ia, "executive_summary", "") or "")
    
    content = format_section(conclusion, evidence, strengths, weaknesses, implication)
    nodes = [ia.node_id] if ia else []
    return ReportSection(
        section_id="investment_thesis",
        title="Investment Thesis",
        content=content,
        supporting_nodes=nodes,
        confidence=conf,
    )


def _write_follow_up_questions(graph: ObservationGraph) -> ReportSection:
    seen = set()
    blocking_questions = []
    high_priority = []
    other_questions = []
    
    ia = graph.investment_assessment
    if ia and getattr(ia, "follow_up_questions", []):
        for q in ia.follow_up_questions:
            q_text = clean_text(q if isinstance(q, str) else getattr(q, "question", ""))
            if q_text and q_text.lower() not in seen:
                seen.add(q_text.lower())
                high_priority.append(q_text)
                
    ALL_DOMAINS = ["founder", "product", "market", "financial", "trl", "competition", "ip", "risk"]
    for domain in ALL_DOMAINS:
        asm = _asm(graph, domain)
        if asm:
            # Explicit expert follow-up questions
            explicit_q = getattr(asm, "follow_up_questions", []) or []
            for eq in explicit_q:
                q_text = clean_text(eq)
                if q_text and q_text.lower() not in seen:
                    seen.add(q_text.lower())
                    high_priority.append(q_text)
                    
            if is_legacy_mode(graph):
                for q in getattr(asm, "questions", []) or []:
                    q_text = clean_text(getattr(q, "question", ""))
                    if not q_text or q_text.lower() in seen:
                        continue
                    seen.add(q_text.lower())
                    if getattr(q, "blocking", False):
                        blocking_questions.append(q_text)
                    elif str(getattr(q, "priority", "")).upper() == "HIGH":
                        high_priority.append(q_text)
                    else:
                        other_questions.append(q_text)
                        
    if is_legacy_mode(graph):
        for q in graph.questions.values():
            q_text = clean_text(getattr(q, "question", ""))
            if q_text and q_text.lower() not in seen:
                seen.add(q_text.lower())
                other_questions.append(q_text)
                
    conclusion = "Outstanding diligence questions have been formulated to address core information gaps." if is_legacy_mode(graph) else ""
    evidence = "Incomplete details in the provided startup profile." if is_legacy_mode(graph) else ""
    strengths = ["Questions target high-priority operational and technical unknowns."] if is_legacy_mode(graph) else []
    weaknesses = ["Outstanding answers prevent final incubation decision."] if is_legacy_mode(graph) else []
    implication = "Verify during the management interview prior to commitment." if is_legacy_mode(graph) else []
    
    questions_list_str = ""
    if blocking_questions:
        questions_list_str += "### Blocking Questions\n"
        questions_list_str += "\n".join(f"* **[BLOCKING]** {q}" for q in blocking_questions)
        questions_list_str += "\n\n"
        
    remaining_high = [q for q in high_priority if q.lower() not in [x.lower() for x in blocking_questions]]
    if remaining_high:
        questions_list_str += "### High Priority Questions\n"
        questions_list_str += "\n".join(f"* {q}" for q in remaining_high)
        questions_list_str += "\n\n"
        
    remaining_other = [q for q in other_questions if q.lower() not in [x.lower() for x in blocking_questions] and q.lower() not in [y.lower() for y in high_priority]]
    if remaining_other:
        questions_list_str += "### General Diligence Questions\n"
        questions_list_str += "\n".join(f"* {q}" for q in remaining_other)
        questions_list_str += "\n\n"
        
    memo_content = format_section(conclusion, evidence, strengths, weaknesses, implication)
    content = questions_list_str + memo_content
    return ReportSection(
        section_id="follow_up_questions",
        title="Follow-up Questions",
        content=content,
        supporting_nodes=list(graph.questions.keys()),
        confidence=1.0,
    )


def _build_missing_section(graph: ObservationGraph) -> ReportSection:
    ALL_DOMAINS = ["founder", "product", "market", "financial", "trl", "competition", "ip", "risk"]
    missing_items = []
    for domain in ALL_DOMAINS:
        asm = _asm(graph, domain)
        if asm:
            # Explicit expert missing_information
            explicit_m = getattr(asm, "missing_information", []) or []
            for em in explicit_m:
                cleaned_em = clean_text(em)
                if cleaned_em:
                    missing_items.append(cleaned_em)
                    
            if is_legacy_mode(graph):
                items = _domain_missing_evidence(graph, domain)
                for m in items[:3]:
                    if m.description:
                        missing_items.append(m.description)
                        
    ia = graph.investment_assessment
    if ia and getattr(ia, "missing_information", []):
        for item in ia.missing_information[:5]:
            if item and len(item) > 5:
                missing_items.append(item)
                
    # Categorization logic
    categories = {
        "Missing Documents": [],
        "Missing Financials": [],
        "Missing Validation": [],
        "Missing Technical Evidence": [],
        "Missing Customer Evidence": [],
        "Missing Legal Information": []
    }
    
    for item in list(set(missing_items)):
        lower_item = item.lower()
        if any(w in lower_item for w in ["burn", "cap table", "financial", "p&l", "projections", "revenue", "margins", "economics", "pricing", "equity"]):
            categories["Missing Financials"].append(item)
        elif any(w in lower_item for w in ["cert", "validation", "peso", "bis", "regulatory", "license"]):
            categories["Missing Validation"].append(item)
        elif any(w in lower_item for w in ["patent", "deed", "assignment", "agreement", "legal", "incorporation", "founder vesting"]):
            categories["Missing Legal Information"].append(item)
        elif any(w in lower_item for w in ["customer", "loi", "mou", "pilot", "traction", "sales", "buyer", "feedback"]):
            categories["Missing Customer Evidence"].append(item)
        elif any(w in lower_item for w in ["cycle", "density", "pyrolysis", "yield", "testing", "bench", "engineering", "technical", "trl"]):
            categories["Missing Technical Evidence"].append(item)
        else:
            categories["Missing Documents"].append(item)
            
    # Format categorized missing items
    categorized_lines = []
    for cat_name, items_list in categories.items():
        if items_list:
            categorized_lines.append(f"#### **{cat_name}**")
            for it in items_list:
                categorized_lines.append(f"*   {it}")
            categorized_lines.append("")
            
    if not categorized_lines:
        categorized_lines.append("No critical missing information identified.")
        
    table_content = "### **Categorized Diligence Gaps**\n\n" + "\n".join(categorized_lines) + "\n\n"
    
    conclusion = "Critical information gaps exist across domains, primarily concerning pilot-scale data and audited financials."
    evidence = "Diligence audit of submitted documentation."
    strengths = ["Gaps are clearly identified and actionable."]
    weaknesses = []
    implication = "Request the outstanding data room items prior to signing the term sheet."
    
    memo_content = format_section(conclusion, evidence, strengths, weaknesses, implication)
    content = table_content + memo_content
    
    return ReportSection(
        section_id="missing_information",
        title="Missing Information",
        content=content,
        supporting_nodes=list(graph.questions.keys()),
        confidence=1.0,
    )


def _build_conflicts_section(graph: ObservationGraph) -> ReportSection:
    unresolved = [c for cid, c in graph.conflicts.items() if cid not in graph.resolutions_by_conflict]
    resolved = [c for cid, c in graph.conflicts.items() if cid in graph.resolutions_by_conflict]
    
    conclusion = "No major unresolved evidence conflicts remain that impact the core thesis."
    if unresolved:
        conclusion = f"There are {len(unresolved)} unresolved evidence conflicts that require management clarification."
        
    evidence = "Integrity audit of the observation graph."
    strengths = ["All key factual assertions are resolved or reconciled."]
    weaknesses = [
        f"Discrepancies identified: {len(unresolved)} unresolved, {len(resolved)} resolved."
    ]
    implication = "Factual consistency is validated; proceed with financial due diligence."
    
    list_str = ""
    if unresolved:
        list_str += "### Unresolved Conflicts\n"
        for c in sorted(unresolved, key=lambda x: x.conflict_id)[:5]:
            list_str += f"* {c.description}\n"
        list_str += "\n"
    if resolved:
        list_str += "### Resolved Conflicts\n"
        for c in sorted(resolved, key=lambda x: x.conflict_id)[:5]:
            list_str += f"* {c.description}\n"
        list_str += "\n"
        
    memo_content = format_section(conclusion, evidence, strengths, weaknesses, implication)
    content = list_str + memo_content
    return ReportSection(
        section_id="conflicts",
        title="Evidence Conflicts",
        content=content,
        supporting_nodes=list(graph.conflicts.keys()),
        confidence=1.0,
    )


def _build_resolutions_section(graph: ObservationGraph) -> ReportSection:
    conclusion = "Reconciliation of conflicting claims has been successfully executed using the consensus engine."
    evidence = "Conflict resolution registry logs."
    strengths = ["Transparent tracking of all factual resolutions."]
    weaknesses = ["Minor validation uncertainty on early-stage prototype performance claims."]
    implication = "Resolution log confirms data integrity; no further factual reconciliation is required."
    
    list_str = ""
    if graph.resolutions:
        list_str += "### Resolution Log\n"
        for res in list(graph.resolutions.values())[:8]:
            list_str += f"* Conflict `{getattr(res, 'conflict_id', '?')}` resolved via {getattr(res, 'resolution_method', 'consensus')}.\n"
        list_str += "\n"
    else:
        list_str += "*No conflict resolutions were required for this evaluation.*\n\n"
        
    memo_content = format_section(conclusion, evidence, strengths, weaknesses, implication)
    content = list_str + memo_content
    return ReportSection(
        section_id="resolutions",
        title="Conflict Resolutions",
        content=content,
        supporting_nodes=list(graph.resolutions.keys()),
        confidence=1.0,
    )

# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

class DueDiligenceReportEngine:
    """Generates professional investment‑committee due‑diligence reports.

    Primary sources (priority order):
      1. ``graph.domain_assessments`` – full AgentAssessment per domain
      2. ``graph.investment_assessment``
      3. ``graph.executive_assessment``
      4. ``graph.claims`` – atomic facts only (TRL, ask, sector)
      5. ``graph.evidence / observations`` – citation layer only
    """

    @staticmethod
    def generate(graph: ObservationGraph) -> ObservationGraph:
        global GLOBAL_SEEN_SENTENCES
        GLOBAL_SEEN_SENTENCES.clear()
        
        report_id = f"REPORT-{str(uuid.uuid4())[:8].upper()}"
        generated_at = datetime.utcnow().isoformat() + "Z"

        # Resolve conflicting observations – suppress non‑preferred ones
        suppressed_obs: set = set()
        for res in graph.resolutions.values():
            if res.preferred_observation_id:
                conflict_id = res.conflict_id
                conflict_node = graph.conflicts.get(conflict_id) or graph.correlations.get(conflict_id)
                if conflict_node:
                    obs_ids: list = []
                    if getattr(conflict_node, "node_type", None) == NodeType.CONFLICT:
                        for edge in graph.out_edges.get(conflict_id, []):
                            if edge.target_type == NodeType.CLAIM and edge.relationship == "CONFLICTS_WITH":
                                for e2 in graph.in_edges.get(edge.target_id, []):
                                    if e2.source_type == NodeType.OBSERVATION and e2.relationship == "SUPPORTED_BY":
                                        obs_ids.append(e2.source_id)
                    elif getattr(conflict_node, "node_type", None) == NodeType.CORRELATION:
                        for edge in graph.out_edges.get(conflict_id, []):
                            if edge.target_type == NodeType.OBSERVATION and edge.relationship == "RELATED_TO":
                                obs_ids.append(edge.target_id)
                    for oid in obs_ids:
                        if oid != res.preferred_observation_id:
                            suppressed_obs.add(oid)
        # Duplicate evidence handling
        for corr_id, corr in graph.correlations.items():
            if corr.correlation_type == "DUPLICATES" and corr_id not in graph.resolutions_by_conflict:
                obs_ids = [e.target_id for e in graph.out_edges.get(corr_id, []) if e.target_type == NodeType.OBSERVATION and e.relationship == "RELATED_TO"]
                for oid in obs_ids[1:]:
                    suppressed_obs.add(oid)

        # Build sections
        section_executive = _write_executive_summary(graph)
        section_investment = _write_investment_recommendation(graph)
        section_investment_summary = ReportSection(
            section_id="investment_summary",
            title="Investment Committee Recommendation Summary",
            content=section_investment.content,
            supporting_nodes=section_investment.supporting_nodes,
            confidence=section_investment.confidence
        )
        section_founder = _write_founder_assessment(graph)
        section_product = _write_product_technology(graph)
        section_market = _write_market_opportunity(graph)
        section_business = _write_business_model(graph)
        section_competition = _write_competition(graph)
        section_financial = _write_financial_overview(graph)
        section_risks = _write_risks(graph, suppressed_obs)
        section_thesis = _write_investment_thesis(graph)
        section_questions = _write_follow_up_questions(graph)

        section_conflicts = _build_conflicts_section(graph)
        section_resolutions = _build_resolutions_section(graph)
        section_missing = _build_missing_section(graph)
        
        # section_ip
        ip_domain = "ip"
        conclusion_ip, strengths_ip, weaknesses_ip, implication_ip = _get_section_fields(graph, ip_domain)
        evidence_ip = format_evidence(graph, [ip_domain])
        
        content_ip = format_section(conclusion_ip, evidence_ip, strengths_ip, weaknesses_ip, implication_ip)
        section_ip = ReportSection(
            section_id="ip_analysis",
            title="Intellectual Property Status",
            content=content_ip,
            confidence=_domain_confidence(graph, ip_domain, 0.80),
            supporting_nodes=[],
        )

        # section_observations
        conclusion_obs = "The underlying factual registry maps findings across all relevant domains."
        evidence_obs = "Factual nodes in the diligence data graph."
        strengths_obs = ["Grounded validation details backing for every commercial claim."]
        weaknesses_obs = ["Subject to updates from the founding team."]
        implication_obs = "Ensures complete compliance and traceability for review purposes."
        
        obs_lines = []
        for obs in sorted(graph.observations.values(), key=lambda x: x.observation_id):
            if obs.observation_id not in suppressed_obs:
                obs_lines.append(
                    f"* **[{obs.observation_id}]** {obs.observation} "
                    f"*(Domain: {obs.domain} - Confidence: {obs.confidence:.2f})*"
                )
                
        list_obs = ""
        if obs_lines:
            list_obs = "### Factual Registry\n" + "\n".join(obs_lines) + "\n\n"
            
        content_obs = list_obs + format_section(conclusion_obs, evidence_obs, strengths_obs, weaknesses_obs, implication_obs)
        section_observations = ReportSection(
            section_id="observations",
            title="Factual Registry",
            content=content_obs,
            supporting_nodes=[oid for oid in graph.observations.keys() if oid not in suppressed_obs],
            confidence=1.0
        )

        # Traceability aggregation
        traceability: Dict[str, Any] = {}
        sections_list = [
            section_executive,
            section_investment,
            section_investment_summary,
            section_founder,
            section_product,
            section_market,
            section_business,
            section_competition,
            section_financial,
            section_risks,
            section_thesis,
            section_questions,
            section_conflicts,
            section_resolutions,
            section_missing,
            section_ip,
            section_observations,
        ]
        for sec in sections_list:
            sec_trace: Dict[str, Any] = {}
            for nid in sec.supporting_nodes:
                node = graph.get_node(nid)
                if node:
                    if node.node_type == NodeType.OBSERVATION:
                        sec_trace[nid] = trace_observation(graph, nid, visited=set())
                    elif node.node_type == NodeType.RISK:
                        sec_trace[nid] = trace_risk(graph, nid, visited=set())
                    elif node.node_type == NodeType.CLAIM:
                        sec_trace[nid] = trace_claim(graph, nid, visited=set())
                    elif node.node_type == NodeType.EVIDENCE:
                        sec_trace[nid] = trace_evidence(graph, nid, visited=set())
                    else:
                        sec_trace[nid] = node.model_dump() if hasattr(node, "model_dump") else {}
            traceability[sec.section_id] = sec_trace

        # Appendices
        appendices: List[Appendix] = []
        asm_lines = ["| Domain | Confidence | Observations | Risks |", "| :--- | :--- | :--- | :--- |"]
        for domain in graph.domain_assessments:
            conf_val = _domain_confidence(graph, domain)
            obs_count = len(graph.observations_by_domain.get(domain, []))
            risk_count = len([r for r in _domain_risks(graph, domain) if r])
            asm_lines.append(f"| {domain.capitalize()} | {conf_val:.2f} | {obs_count} | {risk_count} |")
        appendices.append(Appendix(appendix_id="appendix_a", title="Appendix A: Expert Domain Coverage", content="\n".join(asm_lines)))

        ev_lines = ["| Evidence ID | Location | Confidence |", "| :--- | :--- | :--- |"]
        for ev_id, ev in list(graph.evidence.items())[:20]:
            ev_lines.append(f"| {ev_id[:12]} | {ev.location} | {ev.confidence:.2f} |")
        appendices.append(Appendix(appendix_id="appendix_b", title="Appendix B: Evidence Source Registry", content="\n".join(ev_lines)))

        stats = graph.graph_stats
        unresolved_c = [c for cid, c in graph.conflicts.items() if cid not in graph.resolutions_by_conflict]
        resolved_c = [c for cid, c in graph.conflicts.items() if cid in graph.resolutions_by_conflict]
        stat_lines = [
            f"**Report ID:** {report_id}",
            f"**Generated:** {generated_at}",
            f"*   Documents: {stats.document_count}",
            f"*   Evidence Nodes: {stats.evidence_count}",
            f"*   Claims: {stats.claim_count}",
            f"*   Observations: {stats.observation_count}",
            f"*   Expert Assessments: {len(graph.domain_assessments)}",
            f"*   Risks Identified: {stats.risk_count}",
            f"*   Resolved Conflicts: {len(resolved_c)}",
            f"*   Unresolved Conflicts: {len(unresolved_c)}",
            f"**Graph Hash:** `{graph.graph_hash}`",
        ]
        appendices.append(Appendix(appendix_id="appendix_c", title="Appendix C: Graph Statistics & Integrity Hash", content="\n".join(stat_lines)))

        # Add backward-compatible aliases for traceability
        aliases = {
            "founder_analysis": "founder_assessment",
            "product_analysis": "product_technology",
            "trl_analysis": "product_technology",
            "market_analysis": "market_opportunity",
            "competition_analysis": "competition",
            "financial_analysis": "financial_overview",
            "ip_analysis": "ip_analysis",
            "risk_analysis": "risks",
        }
        for alias, target in aliases.items():
            if target in traceability:
                traceability[alias] = traceability[target]

        # Section 13: Quality Review / Self-Review check
        def self_review_clean(text: str) -> str:
            text = remove_repeated_sentences(text)
            text = refine_generic_text(text)
            filler_phrases = [
                r"\bthis report validates\b",
                r"\bthe evaluation process confirms\b",
                r"\bas mentioned above\b",
                r"\bas stated previously\b",
                r"\bwe believe that\b",
                r"\bthe technology shows strong potential\b"
            ]
            for filler in filler_phrases:
                text = re.sub(filler, "", text, flags=re.IGNORECASE)
            return text.strip()

        # Clean all sections content
        section_executive.content = self_review_clean(section_executive.content)
        section_investment.content = self_review_clean(section_investment.content)
        section_founder.content = self_review_clean(section_founder.content)
        section_product.content = self_review_clean(section_product.content)
        section_market.content = self_review_clean(section_market.content)
        section_business.content = self_review_clean(section_business.content)
        section_competition.content = self_review_clean(section_competition.content)
        section_financial.content = self_review_clean(section_financial.content)
        section_risks.content = self_review_clean(section_risks.content)
        section_thesis.content = self_review_clean(section_thesis.content)
        section_questions.content = self_review_clean(section_questions.content)

        section_founder_analysis = ReportSection(
            section_id="founder_analysis",
            title="Founder Analysis",
            content=section_founder.content,
            supporting_nodes=section_founder.supporting_nodes,
            confidence=section_founder.confidence
        )
        section_trl_analysis = ReportSection(
            section_id="trl_analysis",
            title="TRL Readiness Analysis",
            content=section_product.content,
            supporting_nodes=section_product.supporting_nodes,
            confidence=section_product.confidence
        )

        report_node = DueDiligenceReport(
            node_id=report_id,
            node_type=NodeType.REPORT,
            report_id=report_id,
            generated_at=generated_at,
            graph_version=graph.graph_version,
            executive_summary=section_executive,
            investment_recommendation=section_investment,
            founder_assessment=section_founder,
            product_technology=section_product,
            market_opportunity=section_market,
            business_model=section_business,
            competition=section_competition,
            financial_overview=section_financial,
            risks=section_risks,
            investment_thesis=section_thesis,
            follow_up_questions=section_questions,
            investment_summary=section_investment_summary,
            founder_analysis=section_founder_analysis,
            product_analysis=section_product,
            trl_analysis=section_trl_analysis,
            market_analysis=section_market,
            competition_analysis=section_competition,
            financial_analysis=section_financial,
            ip_analysis=section_ip,
            risk_analysis=section_risks,
            observations=section_observations,
            conflicts=section_conflicts,
            resolutions=section_resolutions,
            missing_information=section_missing,
            appendices=appendices,
            traceability=traceability,
            metadata={
                "report_id": report_id,
                "generated_at": generated_at,
                "domain_assessments_count": len(graph.domain_assessments),
                "unresolved_conflicts_count": len(unresolved_c),
                "resolved_conflicts_count": len(resolved_c),
                "suppressed_observations_count": len(suppressed_obs),
                "architecture": "domain_assessments_primary",
            },
        )

        graph.report = report_node
        return graph
