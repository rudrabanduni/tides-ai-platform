"""batching.py - Deterministic Criterion-Batched Domain Evaluation Helpers.

Replaces monolithic per-domain LLM completions (which packed 10-21 criteria and
multi-part prose into a single capped call) with:
1. Canonical registry-driven criterion batching (`batch_criteria`)
2. Scoped compact batch prompts containing ONLY batch-relevant claims, evidence,
   conflicts, and external research items
3. Pure-Python local validation and merge (`merge_domain_criterion_batches`)
4. Pure-Python domain summary/risks/questions synthesis (`synthesize_domain_summary_and_findings`)
5. Atomic domain batch checkpoint persistence (test-isolated under PYTEST_CURRENT_TEST)
"""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Sequence

from app.modules.evaluation.domain_schemas import (
    CompactCriterionResult,
    CriterionAssessment,
    DomainCriterionBatchOutput,
    VerificationStatus,
)
from app.modules.evaluation.domains.registry import (
    CANONICAL_DOMAINS,
    get_criteria_for_domain,
    get_criterion_metadata,
)
from app.modules.evaluation.schemas import (
    ConfidenceHierarchy,
    MissingEvidence,
    Observation,
    Question,
    Risk,
)


def batch_criteria(criteria: Sequence[Any], max_criteria_per_call: int = 5) -> list[list[Any]]:
    """Splits an ordered sequence of canonical criteria into deterministic fixed-size batches.

    Preserves exact ordering and all criterion identifiers/metadata items without
    hardcoding criterion IDs.
    """
    if max_criteria_per_call < 1:
        raise ValueError(f"max_criteria_per_call must be >= 1, got {max_criteria_per_call}")
    items = list(criteria)
    return [items[i : i + max_criteria_per_call] for i in range(0, len(items), max_criteria_per_call)]


#: Fixed JSON envelope allowance per batch response ({"domain":...,"batch_index":...,"criteria":[...]}).
DOMAIN_BATCH_ENVELOPE_TOKENS = 80
#: Per-criterion completion allowance. A compact criterion item (short evidence handles, <=18-word
#: rationale, <=12-word missing note) is ~90-110 tokens; 220 gives >2x headroom.
DOMAIN_BATCH_TOKENS_PER_CRITERION = 220
#: Floor so that single-criterion requests still have room for a full item.
DOMAIN_BATCH_MIN_OUTPUT_TOKENS = 350

#: Compact wire-format description sent instead of the ~870-token Pydantic JSON Schema.
DOMAIN_BATCH_COMPACT_SCHEMA = (
    '{"domain":"<domain_key>","batch_index":<int>,"criteria":[{"criterion_id":"<ID>",'
    '"verification_status":"VERIFIED_DOCUMENTED|SELF_REPORTED_ONLY|PLAUSIBLE_ESTIMATE|CONTRADICTED|'
    'UNSUPPORTED_ASSUMPTION|MISSING_INFORMATION|NOT_APPLICABLE","score":<number 0-10 or null>,'
    '"evidence_ids":["E1"],"rationale":"<=18 words","missing_information":"<=12 words or null"}]}'
)


def resolve_domain_batch_output_token_limit(batch_size: int, max_tokens_cap: int = 900) -> int:
    """Computes a bounded completion token cap for one criterion batch: 80 + 220*n, floor 300."""
    if batch_size < 1:
        return min(max_tokens_cap, DOMAIN_BATCH_MIN_OUTPUT_TOKENS)
    scaled = max(
        DOMAIN_BATCH_MIN_OUTPUT_TOKENS,
        DOMAIN_BATCH_ENVELOPE_TOKENS + batch_size * DOMAIN_BATCH_TOKENS_PER_CRITERION,
    )
    return min(max_tokens_cap, scaled)


def _evidence_identifier(ev: Any) -> str:
    return str(getattr(ev, "evidence_id", None) or getattr(ev, "id", "") or "").strip()


def evidence_location(ev: Any) -> str:
    """Human-readable provenance for one evidence record, built only from stored metadata."""
    sec = getattr(ev, "section_name", None) or "Document"
    pg = getattr(ev, "page_number", None)
    doc_name = getattr(ev, "document_name", None) or getattr(ev, "source_document_id", None)
    loc = f"{sec} p.{pg}" if pg else str(sec)
    if doc_name:
        loc = f"{doc_name} / {loc}"
    return loc


def build_batch_evidence_handles(
    batch_criterion_ids: Sequence[str],
    claims: Sequence[Any],
    evidence: Sequence[Any],
) -> dict[str, Any]:
    """Deterministically assigns short per-batch handles ("E1", "E2", ...) to the evidence
    records that the batch prompt shows the model.

    Full evidence UUIDs cost ~15-20 output tokens each; with several citations per criterion they
    were a major contributor to the PETREVOLT domain truncation. The model cites handles; the
    backend maps them back to real evidence IDs and rejects anything it did not show.
    The ordering mirrors `build_domain_batch_prompts` exactly.
    """
    evidence_by_claim: dict[str, list[Any]] = {}
    for ev in evidence:
        cid_key = str(getattr(ev, "claim_id", "") or "")
        if cid_key:
            evidence_by_claim.setdefault(cid_key, []).append(ev)

    handles: dict[str, Any] = {}
    seen: set[str] = set()

    def _add(ev: Any) -> None:
        ev_id = _evidence_identifier(ev)
        if not ev_id or ev_id in seen:
            return
        # Only evidence with an actual document passage can be cited.
        if not str(getattr(ev, "evidence_snippet", "") or "").strip():
            return
        seen.add(ev_id)
        handles[f"E{len(handles) + 1}"] = ev

    any_matched = False
    for cid in batch_criterion_ids:
        crit_claims = _match_claims_for_criterion(cid, claims)
        if crit_claims:
            any_matched = True
        for cl in crit_claims[:3]:
            for ev in evidence_by_claim.get(str(getattr(cl, "id", "") or ""), [])[:4]:
                _add(ev)
    if not any_matched and claims:
        for cl in list(claims)[:5]:
            for ev in evidence_by_claim.get(str(getattr(cl, "id", "") or ""), [])[:2]:
                _add(ev)
    return handles


def resolve_evidence_references(
    refs: Sequence[Any],
    handles: dict[str, Any],
    known_evidence_ids: set[str],
) -> tuple[list[str], list[str]]:
    """Maps model-cited evidence references to real evidence IDs.

    Accepts a per-batch handle ("E3") or an exact evidence ID that exists in the startup's evidence
    set. Everything else is rejected (never invented). Returns (resolved_ids, rejected_refs).
    """
    resolved: list[str] = []
    rejected: list[str] = []
    for raw in refs or []:
        ref = str(raw or "").strip()
        if not ref:
            continue
        key = ref.upper()
        if key in handles:
            real_id = _evidence_identifier(handles[key])
        elif ref in known_evidence_ids:
            real_id = ref
        else:
            rejected.append(ref)
            continue
        if real_id and real_id not in resolved:
            resolved.append(real_id)
    return resolved, rejected


def _extract_claim_field_key(claim: Any) -> str:
    fk = getattr(claim, "field", None)
    raw = getattr(fk, "field_key", "") if fk else getattr(claim, "field_name", "")
    return str(raw or "").strip().lower()


def _extract_claim_value(claim: Any) -> str:
    for attr in ("value_string", "value_number", "value_boolean", "value_json"):
        val = getattr(claim, attr, None)
        if val is not None:
            text = str(val).strip()
            if text:
                return text
    return ""


def _truncate_text(text: str, limit: int = 240) -> str:
    clean = re.sub(r"\s+", " ", (text or "")).strip()
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3].rstrip() + "..."


def _match_claims_for_criterion(cid: str, claims: Sequence[Any]) -> list[Any]:
    cid_prefix = cid.lower().replace("-", "_")
    matched: list[Any] = []
    for c in claims:
        fkey = _extract_claim_field_key(c)
        if fkey == cid_prefix or fkey.startswith(cid_prefix + "_") or fkey.startswith(cid_prefix):
            matched.append(c)
    return matched


def build_domain_batch_prompts(
    *,
    domain_key: str,
    domain_title: str,
    company_name: str,
    batch_index: int,
    total_batches: int,
    batch_criterion_ids: Sequence[str],
    claims: Sequence[Any],
    evidence: Sequence[Any],
    conflicts: Sequence[Any],
    prompt_version: str = "2.1.0",
    external_research_items: Sequence[dict[str, Any]] | None = None,
    domain_rubric_notes: str = "",
) -> tuple[str, str]:
    """Builds tightly scoped system and user prompts for ONE criterion batch.

    Includes ONLY the rubric criteria, claims, evidence IDs/locations/snippets,
    conflicts, and external research relevant to `batch_criterion_ids`.
    Never repeats full startup profile, full evidence graph, other batches' criteria,
    or multi-paragraph essay directives.
    """
    system_prompt = (
        f"You are the {domain_title} due diligence specialist for TIDES IIT Roorkee. "
        f"Evaluate ONLY the assigned criterion batch ({batch_index + 1} of {total_batches}) "
        f"and emit strict JSON conforming to DomainCriterionBatchOutput.\n"
        "Rules:\n"
        "- Output ONLY criteria listed in ASSIGNED CRITERIA; never omit or invent IDs.\n"
        "- Cite evidence ONLY by the bracketed handles shown (e.g. \"E2\"); never invent handles or IDs.\n"
        "- Grade conservatively: VERIFIED_DOCUMENTED only when a cited handle's snippet supports it.\n"
        "- Applicant statements without a supporting document are SELF_REPORTED_ONLY, never verified.\n"
        "- Use MISSING_INFORMATION when the value is absent; missing evidence is a gap, not a weakness score.\n"
        "- Set score (0.0-10.0) only when supported by rubric/evidence; otherwise null.\n"
        "- rationale <= 18 words; missing_information <= 12 words or null. No summaries, no provenance text.\n"
        "- Output minified single-line JSON only."
    )
    if domain_rubric_notes.strip():
        system_prompt += f"\nDomain focus: {_truncate_text(domain_rubric_notes, 280)}"

    # Index evidence by claim_id
    evidence_by_claim: dict[str, list[Any]] = {}
    for ev in evidence:
        cid_key = str(getattr(ev, "claim_id", "") or "")
        if cid_key:
            evidence_by_claim.setdefault(cid_key, []).append(ev)

    batch_id_set = {c.upper() for c in batch_criterion_ids}
    batch_prefixes = tuple(c.lower().replace("-", "_") for c in batch_criterion_ids)
    handle_by_evidence_id = {
        _evidence_identifier(ev): handle
        for handle, ev in build_batch_evidence_handles(batch_criterion_ids, claims, evidence).items()
    }

    lines: list[str] = [
        f"Company: {company_name or 'Startup Applicant'} | Domain: {domain_title} ({domain_key}) | Batch: {batch_index + 1}/{total_batches}",
        "",
        "--- ASSIGNED CRITERIA & SCOPED EVIDENCE ---",
    ]

    matched_claim_ids: set[str] = set()
    any_matched_claims = False

    for cid in batch_criterion_ids:
        meta = get_criterion_metadata(cid)
        cname = meta.get("name", cid) if isinstance(meta, dict) else cid
        slide_num = meta.get("slide", 1) if isinstance(meta, dict) else 1
        is_cond = bool(meta.get("is_conditional", False)) if isinstance(meta, dict) else False
        is_req = bool(meta.get("is_required", True)) if isinstance(meta, dict) else True
        req_tag = "CONDITIONAL" if is_cond else ("REQUIRED" if is_req else "OPTIONAL")

        lines.append(f"[{cid}] {cname} (Slide {slide_num}, {req_tag})")
        crit_claims = _match_claims_for_criterion(cid, claims)
        if crit_claims:
            any_matched_claims = True
            for cl in crit_claims[:3]:
                cl_id = str(getattr(cl, "id", "") or "")
                if cl_id:
                    matched_claim_ids.add(cl_id)
                val_txt = _truncate_text(_extract_claim_value(cl) or "None disclosed", 240)
                conf = getattr(cl, "confidence_score", None)
                conf_tag = f" conf={float(conf):.2f}" if conf is not None else ""
                lines.append(f"  Claim ({_extract_claim_field_key(cl)}{conf_tag}): {val_txt}")
                ev_list = evidence_by_claim.get(cl_id, [])
                for ev in ev_list[:4]:
                    ev_handle = handle_by_evidence_id.get(_evidence_identifier(ev))
                    if not ev_handle:
                        continue
                    loc = evidence_location(ev)
                    snippet = _truncate_text(str(getattr(ev, "evidence_snippet", "") or ""), 180)
                    snip_part = f" :: \"{snippet}\"" if snippet else ""
                    lines.append(f"  Evidence [{ev_handle}] ({loc}){snip_part}")
        else:
            lines.append("  Claim: <none extracted for this criterion>")

    # Compact fallback ONLY if none of the criteria in this batch matched canonical prefixes
    # (supports legacy/minimal test fixtures where claims use non-prefixed keys like 'target_market')
    if not any_matched_claims and claims:
        lines.append("")
        lines.append("--- GENERAL DOMAIN SIGNALS (UNMAPPED FIELD KEYS) ---")
        for cl in list(claims)[:5]:
            cl_id = str(getattr(cl, "id", "") or "")
            fkey = _extract_claim_field_key(cl) or "claim"
            val_txt = _truncate_text(_extract_claim_value(cl), 180)
            lines.append(f"  {fkey}: {val_txt}")
            for ev in evidence_by_claim.get(cl_id, [])[:2]:
                ev_handle = handle_by_evidence_id.get(_evidence_identifier(ev))
                if not ev_handle:
                    continue
                sec = getattr(ev, "section_name", None) or "Document"
                snippet = _truncate_text(str(getattr(ev, "evidence_snippet", "") or ""), 120)
                lines.append(f"    Evidence [{ev_handle}] ({sec}): \"{snippet}\"")

    # Scoped conflicts relevant to this batch only
    scoped_conflicts = []
    for cf in conflicts:
        cf_text = str(
            getattr(cf, "field_key", None)
            or getattr(cf, "description", None)
            or getattr(cf, "conflict_type", "")
            or cf
        ).lower()
        cf_claim_a = str(getattr(cf, "claim_a_id", "") or "")
        cf_claim_b = str(getattr(cf, "claim_b_id", "") or "")
        if (
            any(p in cf_text for p in batch_prefixes)
            or any(cid.lower() in cf_text for cid in batch_id_set)
            or (cf_claim_a and cf_claim_a in matched_claim_ids)
            or (cf_claim_b and cf_claim_b in matched_claim_ids)
        ):
            scoped_conflicts.append(cf)

    if scoped_conflicts:
        lines.append("")
        lines.append("--- RELEVANT CONFLICTS ---")
        for cf in scoped_conflicts[:4]:
            desc = getattr(cf, "description", None) or str(cf)
            lines.append(f"  - {_truncate_text(str(desc), 200)}")

    # Scoped external research items (e.g. MO-01..MO-05 / MO-07..MO-10)
    def _ext_val(obj: Any, key: str, default: Any = None) -> Any:
        return obj.get(key, default) if isinstance(obj, dict) else getattr(obj, key, default)

    if external_research_items:
        scoped_ext = []
        for item in external_research_items:
            raw_criteria = _ext_val(item, "criteria") or []
            if not raw_criteria:
                claimed_cid = _ext_val(item, "claimed_criterion_id")
                if claimed_cid:
                    raw_criteria = [claimed_cid]
                else:
                    src_type = str(_ext_val(item, "source_type") or "")
                    if src_type in ("market_size_growth", "industry_trends"):
                        raw_criteria = ["MO-01", "MO-02", "MO-03", "MO-04", "MO-05"]
                    elif src_type in ("competitor_intelligence", "funding_lookup"):
                        raw_criteria = ["MO-07", "MO-08", "MO-09", "MO-10"]
            item_criteria = {str(c).upper() for c in raw_criteria}
            if not item_criteria or (item_criteria & batch_id_set):
                scoped_ext.append(item)
        if scoped_ext:
            lines.append("")
            lines.append("--- SCOPED EXTERNAL RESEARCH ---")
            for item in scoped_ext[:5]:
                src = _ext_val(item, "source") or _ext_val(item, "source_domain") or _ext_val(item, "url") or "External source"
                title = _truncate_text(str(_ext_val(item, "title") or ""), 80)
                summary = _truncate_text(str(_ext_val(item, "snippet") or _ext_val(item, "excerpt") or _ext_val(item, "summary") or ""), 180)
                lines.append(f"  - {title} ({src}): {summary}")

    lines.extend([
        "",
        "--- OUTPUT REQUIREMENTS ---",
        f"Return compact single-line minified JSON for DomainCriterionBatchOutput with domain='{domain_key}', batch_index={batch_index},",
        f"and criteria=[...] containing EXACTLY {len(batch_criterion_ids)} items in order: {list(batch_criterion_ids)}.",
    ])

    return system_prompt, "\n".join(lines)


def merge_domain_criterion_batches(
    domain_key: str,
    batch_outputs: Sequence[DomainCriterionBatchOutput | dict[str, Any]],
    expected_batches: Sequence[Sequence[str]] | None = None,
) -> list[CompactCriterionResult]:
    """Deterministically validates and merges criterion batch outputs in canonical registry order.

    Rejects:
    - Unknown or out-of-domain criteria
    - Duplicate criteria within or across batches
    - Criteria appearing in a batch they were not assigned to (cross-batch mismatch)
    - Missing canonical criteria owned by `domain_key`

    Never uses an LLM call to merge batches.
    """
    canonical_order = get_criteria_for_domain(domain_key)
    canonical_set = set(canonical_order)

    if expected_batches is not None:
        flattened_expected = [cid for batch in expected_batches for cid in batch]
        if flattened_expected != canonical_order:
            raise ValueError(
                f"Expected batches for domain '{domain_key}' do not cover canonical registry order exactly."
            )

    merged_by_id: dict[str, CompactCriterionResult] = {}

    for pos, raw_batch in enumerate(batch_outputs):
        if isinstance(raw_batch, dict):
            batch_obj = DomainCriterionBatchOutput.model_validate(raw_batch)
        elif isinstance(raw_batch, DomainCriterionBatchOutput):
            batch_obj = raw_batch
        else:
            raise ValueError(f"Unsupported batch output type at index {pos}: {type(raw_batch)}")

        if batch_obj.domain and batch_obj.domain != domain_key:
            raise ValueError(
                f"Batch {pos} domain mismatch: expected '{domain_key}', got '{batch_obj.domain}'"
            )

        expected_for_batch: set[str] | None = None
        if expected_batches is not None:
            if batch_obj.batch_index < 0 or batch_obj.batch_index >= len(expected_batches):
                raise ValueError(
                    f"Batch index {batch_obj.batch_index} out of range (expected 0..{len(expected_batches) - 1})"
                )
            expected_for_batch = {c.upper().strip() for c in expected_batches[batch_obj.batch_index]}

        for item in batch_obj.criteria:
            cid = str(item.criterion_id or "").upper().strip()
            if cid not in canonical_set:
                raise ValueError(
                    f"Unknown or out-of-domain criterion_id '{cid}' in domain '{domain_key}' batch {batch_obj.batch_index}"
                )
            if expected_for_batch is not None and cid not in expected_for_batch:
                raise ValueError(
                    f"Cross-batch criterion mismatch: '{cid}' returned in batch {batch_obj.batch_index}, "
                    f"expected {sorted(expected_for_batch)}"
                )
            if cid in merged_by_id:
                raise ValueError(f"Duplicate criterion_id '{cid}' detected while merging '{domain_key}' batches")
            # Normalize criterion_id uppercase cleanly while preserving all fields
            normalized = item.model_copy(update={"criterion_id": cid})
            merged_by_id[cid] = normalized

    missing = [cid for cid in canonical_order if cid not in merged_by_id]
    if missing:
        raise ValueError(
            f"Incomplete merge for domain '{domain_key}': missing canonical criteria {missing}"
        )

    return [merged_by_id[cid] for cid in canonical_order]


def synthesize_domain_summary_and_findings(
    *,
    domain_key: str,
    domain_title: str,
    criterion_evals: dict[str, CriterionAssessment],
    total_criteria_count: int | None = None,
    has_external_research: bool = False,
    incomplete_batches: Sequence[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Deterministically synthesizes domain-level summary, strengths, risks, questions,
    missing evidence, observations, and confidence strictly from merged criterion assessments.

    Zero LLM calls required and immune to truncated summary generation.
    Avoids robotic phrases scrubbed by ReportEngine.clean_text().
    """
    ordered_evals = list(criterion_evals.values())
    total = total_criteria_count or len(ordered_evals)

    verified = [c for c in ordered_evals if c.verification_status == VerificationStatus.VERIFIED_DOCUMENTED]
    plausible = [c for c in ordered_evals if c.verification_status == VerificationStatus.PLAUSIBLE_ESTIMATE]
    self_reported = [c for c in ordered_evals if c.verification_status == VerificationStatus.SELF_REPORTED_ONLY]
    contradicted = [c for c in ordered_evals if c.verification_status == VerificationStatus.CONTRADICTED]
    unsupported = [c for c in ordered_evals if c.verification_status == VerificationStatus.UNSUPPORTED_ASSUMPTION]
    missing = [c for c in ordered_evals if c.verification_status == VerificationStatus.MISSING_INFORMATION]

    batch_failures = list(incomplete_batches or [])

    if batch_failures:
        conf_score = 0.0
    elif total > 0:
        avg_crit_conf = sum(float(c.confidence_score or 0.0) for c in ordered_evals) / len(ordered_evals)
        substantiated_ratio = (len(verified) + 0.8 * len(plausible) + 0.55 * len(self_reported)) / total
        penalty = min(0.4, 0.08 * len(contradicted) + 0.03 * len(missing) + 0.04 * len(unsupported))
        raw_conf = 0.55 * avg_crit_conf + 0.45 * substantiated_ratio - penalty
        conf_score = round(max(0.15, min(0.95, raw_conf)), 2)
    else:
        conf_score = 0.0

    # Summary text (clean business language; note ReportValidator + ReportEngine expectations)
    if batch_failures:
        failed_ids = ", ".join(str(b.get("batch_index")) for b in batch_failures)
        summary_text = (
            f"{domain_title} evaluation incomplete: batch failure on batch index [{failed_ids}]. "
            f"{len(verified)} verified and {len(missing)} incomplete or missing criteria."
        )
        exec_summary = (
            f"Automated diligence for {domain_title} halted cleanly after batch failure(s) [{failed_ids}] "
            f"without fabricating unassessed criteria."
        )
        exec_conclusion = f"{domain_title} diligence requires manual completion for failed criterion batch(es)."
        reasoning_text = summary_text
        implication = "Milestone tranche allocation deferred pending completion of failed domain criterion batch(es)."
        strengths_list: list[str] = []
    else:
        summary_text = (
            f"{domain_title} covers {total} canonical criteria: "
            f"{len(verified)} documented with source citations, {len(plausible)} benchmark-aligned, "
            f"{len(self_reported)} founder-stated pending third-party proof, and {len(missing) + len(contradicted)} needing follow-up."
        )
        exec_summary = (
            f"{domain_title} spans {total} criteria. Primary source documents substantiate {len(verified)} item(s); "
            f"{len(self_reported)} rest on founder statements, while {len(missing)} required or optional disclosures remain absent."
        )
        if contradicted:
            exec_conclusion = (
                f"{domain_title} presents {len(contradicted)} material discrepancy(ies) requiring resolution prior to commitment."
            )
        elif len(verified) >= max(1, math.ceil(total * 0.4)):
            exec_conclusion = (
                f"{domain_title} is materially documented across core criteria, with targeted follow-up on unverified disclosures."
            )
        else:
            exec_conclusion = (
                f"{domain_title} relies largely on founder-reported assertions and requires supporting source documentation."
            )
        reasoning_text = (
            f"Criterion-by-criterion review across {total} {domain_title} dimensions yields "
            f"{len(verified)} verified documented items, {len(plausible)} plausible estimates, "
            f"{len(self_reported)} self-reported items, {len(unsupported)} unsupported assumptions, "
            f"{len(contradicted)} contradictions, and {len(missing)} missing disclosures."
        )
        implication = (
            "Milestone tranche disbursement contingent on resolving open due diligence verification items."
            if (self_reported or missing or contradicted or unsupported)
            else "Primary domain disclosures are substantiated for incubation committee review."
        )
        # Concise grounded strengths from documented/plausible criteria
        strengths_candidates = verified + plausible
        strengths_list = [
            f"{c.criterion_id} ({c.criterion_name}): {_truncate_text(c.assessment_narrative, 110)}"
            for c in strengths_candidates[:3]
        ]
        # Where documentary support is thin, surface the strongest applicant-reported positions,
        # explicitly labelled so they are never read as verified findings.
        if len(strengths_list) < 3:
            reported = sorted(
                (c for c in self_reported if c.score is not None and float(c.score) >= 6.0),
                key=lambda c: (-float(c.score or 0.0), c.criterion_id),
            )
            for c in reported[: 3 - len(strengths_list)]:
                strengths_list.append(
                    f"{c.criterion_id} ({c.criterion_name}) [applicant-reported, pending verification]: "
                    f"{_truncate_text(c.assessment_narrative, 90)}"
                )

    weaknesses_list = [
        f"Unverified or missing documentation for {c.criterion_id} ({c.criterion_name})"
        for c in (contradicted + unsupported + missing + self_reported)[:5]
    ]

    risks_list: list[Risk] = []
    for idx, c in enumerate(contradicted[:3], start=1):
        risks_list.append(
            Risk(
                id=f"RISK-{domain_key.upper()}-CONTR-{idx:02d}",
                risk_id=f"RISK-{domain_key.upper()}-CONTR-{idx:02d}",
                category="Operational",
                description=f"Discrepancy on {c.criterion_id} ({c.criterion_name}): {_truncate_text(c.assessment_narrative, 110)}",
                severity="High",
                likelihood="High",
                impact="High",
                mitigation=f"Reconcile source documents for {c.criterion_id} before committee approval.",
                supporting_evidence=list(c.evidence_ids),
                confidence=0.85,
            )
        )
    for idx, c in enumerate((unsupported + missing)[:3], start=1):
        risks_list.append(
            Risk(
                id=f"RISK-{domain_key.upper()}-GAP-{idx:02d}",
                risk_id=f"RISK-{domain_key.upper()}-GAP-{idx:02d}",
                category="Diligence",
                description=f"Substantiation gap on {c.criterion_id} ({c.criterion_name}): {_truncate_text(c.assessment_narrative, 110)}",
                severity="Medium" if c.verification_status == VerificationStatus.SELF_REPORTED_ONLY else "High",
                likelihood="Medium",
                impact="High",
                mitigation=f"Collect primary documentation covering {c.criterion_id}.",
                supporting_evidence=list(c.evidence_ids),
                confidence=0.8,
            )
        )
    for bf in batch_failures:
        b_idx = bf.get("batch_index", "unknown")
        b_err = bf.get("error", "Batch execution failed")
        risks_list.append(
            Risk(
                id=f"RISK-{domain_key.upper()}-BATCH-{b_idx}",
                risk_id=f"RISK-{domain_key.upper()}-BATCH-{b_idx}",
                category="Operational",
                severity="High",
                likelihood="High",
                impact="High",
                confidence=0.9,
                reasoning=f"Automated diligence halted for batch {b_idx} in {domain_title}: {b_err}",
                description=f"Automated due diligence incomplete for {domain_title} batch {b_idx}: {b_err}",
                mitigation="Retry or manually review the affected criterion batch.",
            )
        )

    diligence_targets = (contradicted + unsupported + missing + self_reported)[:5]
    questions_list = [
        Question(
            id=f"QST-{domain_key.upper()}-{idx:03d}",
            question=f"Provide primary documentation substantiating {c.criterion_id} ({c.criterion_name}).",
            purpose=f"Close {c.verification_status.value.lower().replace('_', ' ')} status on {c.criterion_id}",
            priority="High" if c.verification_status in (VerificationStatus.CONTRADICTED, VerificationStatus.MISSING_INFORMATION) else "Medium",
            expected_evidence="Dated primary record, contract, filing, or signed sheet",
            blocking=c.verification_status == VerificationStatus.CONTRADICTED,
            generated_by=domain_key,
        )
        for idx, c in enumerate(diligence_targets, start=1)
    ]

    missing_ev_list = [
        MissingEvidence(
            description=f"{c.criterion_id} ({c.criterion_name}): {_truncate_text(c.assessment_narrative, 120)}",
            importance="High" if c.verification_status in (VerificationStatus.MISSING_INFORMATION, VerificationStatus.CONTRADICTED) else "Medium",
        )
        for c in (missing + unsupported + self_reported)[:5]
    ]

    missing_info_list = [
        f"{c.criterion_id}: {c.criterion_name}"
        for c in (missing + unsupported)[:8]
    ]

    contradictions_list = [
        f"{c.criterion_id} ({c.criterion_name}): {_truncate_text(c.assessment_narrative, 120)}"
        for c in contradicted
    ]

    unsupported_claims_list = [
        f"{c.criterion_id}: {c.criterion_name} ({_truncate_text(str(c.extracted_startup_response or 'unverified'), 80)})"
        for c in (self_reported + unsupported)
    ]

    obs_list = (
        []
        if batch_failures
        else [
            Observation(
                observation_id=f"OBS-{domain_key.upper()}-{idx:03d}",
                observation=f"{c.criterion_id} ({c.criterion_name}): {_truncate_text(c.assessment_narrative, 120)}",
                evidence_ids=list(c.evidence_ids),
                reasoning=_truncate_text(c.assessment_narrative, 140),
                confidence=float(c.confidence_score or conf_score),
            )
            for idx, c in enumerate((verified + plausible + self_reported)[:4], start=1)
        ]
    )

    limitations = (
        f"Incomplete batch execution ({len(batch_failures)} failed batch(es))."
        if batch_failures
        else (
            "External market benchmarks incorporated alongside submitted startup records."
            if has_external_research
            else "Independent external web research unavailable; relies on submitted deck citations."
        )
    )

    return {
        "summary": summary_text,
        "executive_summary": exec_summary,
        "executive_conclusion": exec_conclusion,
        "reasoning": reasoning_text,
        "investment_implication": implication,
        "strengths": strengths_list,
        "weaknesses": weaknesses_list,
        "risks": risks_list,
        "questions": questions_list,
        "missing_evidence": missing_ev_list,
        "missing_information": missing_info_list,
        "contradictions": contradictions_list,
        "unsupported_claims": unsupported_claims_list,
        "observations": obs_list,
        "follow_up_questions": [q.question for q in questions_list],
        "composite_domain_confidence": conf_score,
        "confidence": ConfidenceHierarchy(
            finding_confidence=conf_score,
            evidence_confidence=conf_score,
            reasoning_confidence=conf_score,
            overall_domain_confidence=conf_score,
        ),
        "confidence_limitations": limitations,
    }


def _checkpoint_base_dir() -> Path:
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return Path(tempfile.gettempdir()) / "tides_pytest_domain_checkpoints"
    return Path("uploads") / "domain_checkpoints"


def get_domain_batch_checkpoint_path(evaluation_id: str, domain_key: str) -> Path:
    safe_eval = re.sub(r"[^a-zA-Z0-9._-]", "_", str(evaluation_id))
    safe_domain = re.sub(r"[^a-zA-Z0-9._-]", "_", str(domain_key))
    return _checkpoint_base_dir() / f"{safe_eval}_{safe_domain}.json"


def load_domain_batch_checkpoint(evaluation_id: str | None, domain_key: str) -> dict[str, Any]:
    if not evaluation_id:
        return {"completed_batches": {}, "failed_batches": {}}
    path = get_domain_batch_checkpoint_path(evaluation_id, domain_key)
    if not path.exists():
        return {"completed_batches": {}, "failed_batches": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("completed_batches", {})
            data.setdefault("failed_batches", {})
            return data
    except Exception:
        pass
    return {"completed_batches": {}, "failed_batches": {}}


def save_domain_batch_checkpoint(evaluation_id: str | None, domain_key: str, state: dict[str, Any]) -> None:
    if not evaluation_id:
        return
    path = get_domain_batch_checkpoint_path(evaluation_id, domain_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    os.replace(tmp_path, path)
