"""base.py - Base Canonical Domain Specialist Expert Agent.

Extends ExpertAgent with:
- Ownership of canonical LaunchIndex criteria
- Criterion-level structured evaluation (CriterionAssessment)
- Native integration with EvaluationCostLedger and shared $0.55 budget
- DomainAssessmentReport output contract (100% duck-type compatible with AgentAssessment)
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.services.ai.cost_ledger import CostLedgerManager
from app.services.ai.gateway import AIGateway, create_ai_gateway
from app.services.ai.schemas import AICompletionRequest
from app.services.ai.exceptions import AIBudgetExhaustedError, AIResponseParseError, AIProviderError
from app.modules.evaluation.expert_agent import ExpertAgent
from app.modules.evaluation.schemas import (
    Observation,
    Risk,
    Question,
    ConfidenceHierarchy,
    MissingEvidence,
    AgentAssessment,
)
from app.modules.evaluation.domain_schemas import (
    DomainAssessmentReport,
    CriterionAssessment,
    VerificationStatus,
    CompactCriterionResult,
    CompactDomainRisk,
    CompactDomainAssessment,
    DomainCriterionBatchOutput,
    BatchCriterionResult,
)
from app.modules.evaluation.domains.batching import (
    DOMAIN_BATCH_COMPACT_SCHEMA,
    batch_criteria,
    build_batch_evidence_handles,
    build_domain_batch_prompts,
    evidence_location,
    resolve_evidence_references,
    get_domain_batch_checkpoint_path,
    load_domain_batch_checkpoint,
    merge_domain_criterion_batches,
    resolve_domain_batch_output_token_limit,
    save_domain_batch_checkpoint,
    synthesize_domain_summary_and_findings,
)
from app.modules.evaluation.domains.registry import (
    get_criteria_for_domain,
    get_criterion_metadata,
    CANONICAL_DOMAINS,
)
from app.modules.evaluation.prompts.manager import PromptManager

logger = logging.getLogger(__name__)


class CanonicalDomainExpert(ExpertAgent):
    """Base class for the 6 Canonical Domain Specialist Evaluators."""

    def __init__(self, gateway: AIGateway | None = None) -> None:
        super().__init__(gateway=gateway)

    @property
    def domain_key(self) -> str:
        return self.get_domain_key()

    @property
    def domain_title(self) -> str:
        domain_info = CANONICAL_DOMAINS.get(self.domain_key, {})
        return domain_info.get("title", self.domain_key.replace("_", " ").title())

    def get_agent_version(self) -> str:
        return "2.0.0"

    def get_owned_criteria(self) -> List[str]:
        return get_criteria_for_domain(self.domain_key)

    @property
    def max_criteria_per_call(self) -> int:
        """Maximum canonical criteria evaluated in a single LLM batch call."""
        return int(get_settings().ai_domain_batch_max_criteria)

    @property
    def batch_max_output_tokens(self) -> int:
        """Maximum completion tokens permitted for a single criterion batch call."""
        return int(get_settings().ai_domain_batch_max_output_tokens)

    @property
    def max_output_tokens(self) -> int:
        """Maximum completion tokens per domain batch call (replaces monolithic 1800/2400 single-call cap)."""
        return self.batch_max_output_tokens

    def validate_inputs(
        self,
        profile: Any,
        claims: list[Any],
        evidence: list[Any],
        conflicts: list[Any],
        metadata: dict[str, Any]
    ) -> bool:
        """Verifies input claims and context exist for this domain."""
        return True

    def build_criterion_assessments(
        self,
        claims: list[Any],
        evidence: list[Any],
        assessment_observations: list[Observation]
    ) -> dict[str, CriterionAssessment]:
        """Builds structured CriterionAssessment for each criterion owned by this domain."""
        owned_criteria = self.get_owned_criteria()
        evaluations: dict[str, CriterionAssessment] = {}

        # Build claim lookup map
        claim_map: dict[str, Any] = {}
        for c in claims:
            fk = getattr(c, "field", None)
            fkey = getattr(fk, "field_key", "") if fk else ""
            if fkey:
                claim_map[fkey.lower()] = c

        evidence_map: dict[str, list[Any]] = {}
        for ev in evidence:
            cid = str(getattr(ev, "claim_id", ""))
            if cid:
                evidence_map.setdefault(cid, []).append(ev)

        for cid in owned_criteria:
            meta = get_criterion_metadata(cid)
            crit_name = meta.get("name", cid)
            slide_num = meta.get("slide", 1)

            # Match claims related to this criterion ID (e.g. "ps_01", "mo_07", "ft_01")
            cid_prefix = cid.lower().replace("-", "_")
            matched_claim = None
            for fkey, claim_obj in claim_map.items():
                if fkey.startswith(cid_prefix):
                    matched_claim = claim_obj
                    break

            val_str = None
            evidence_ids = []
            source_locations = [f"Slide {slide_num}"]
            verification_status = VerificationStatus.SELF_REPORTED_ONLY
            confidence = 0.85

            if matched_claim:
                val = (
                    matched_claim.value_string
                    if matched_claim.value_string is not None else (
                        str(matched_claim.value_number)
                        if matched_claim.value_number is not None else (
                            str(matched_claim.value_boolean)
                            if matched_claim.value_boolean is not None else (
                                str(matched_claim.value_json)
                                if matched_claim.value_json is not None else ""
                            )
                        )
                    )
                )
                val_str = str(val) if val else None
                confidence = float(getattr(matched_claim, "confidence_score", 0.85))

                # Check linked evidence
                ev_list = evidence_map.get(str(matched_claim.id), [])
                for ev in ev_list:
                    evidence_ids.append(str(ev.id))
                    sec = getattr(ev, "section_name", "")
                    pg = getattr(ev, "page_number", None)
                    loc = f"{sec} (Page {pg})" if pg else sec
                    if loc and loc not in source_locations:
                        source_locations.append(loc)

                if ev_list and any(getattr(e, "evidence_snippet", None) for e in ev_list):
                    verification_status = VerificationStatus.VERIFIED_DOCUMENTED
                else:
                    verification_status = VerificationStatus.SELF_REPORTED_ONLY
            else:
                if meta.get("is_conditional", False):
                    verification_status = VerificationStatus.NOT_APPLICABLE
                    val_str = "None disclosed (conditional field)"
                elif meta.get("is_required", True):
                    verification_status = VerificationStatus.MISSING_INFORMATION
                    val_str = "Missing from application"
                else:
                    verification_status = VerificationStatus.NOT_APPLICABLE
                    val_str = "Optional field not provided"

            # Domain-specific conditional overrides
            verification_status = self.refine_verification_status(cid, val_str, verification_status, claims)

            evaluations[cid] = CriterionAssessment(
                criterion_id=cid,
                criterion_name=crit_name,
                extracted_startup_response=val_str,
                assessment_narrative=f"Evaluated {crit_name} from application submission ({source_locations[0]}). Status: {verification_status.value}.",
                evidence_ids=evidence_ids,
                source_locations=source_locations,
                verification_status=verification_status,
                strengths=[f"Stated {crit_name}"] if val_str and verification_status == VerificationStatus.VERIFIED_DOCUMENTED else [],
                weaknesses=[f"Unverified or missing documentation for {crit_name}"] if verification_status in (VerificationStatus.SELF_REPORTED_ONLY, VerificationStatus.MISSING_INFORMATION) else [],
                risks=[],
                contradictions=[],
                confidence_score=confidence,
                confidence_limitations="Independent external verification pending external search integration" if verification_status != VerificationStatus.VERIFIED_DOCUMENTED else None,
            )

        return evaluations

    def build_criterion_assessments_from_compact(
        self,
        claims: list[Any],
        evidence: list[Any],
        compact_criteria: list[CompactCriterionResult],
        confidence_fallback: float = 0.85,
    ) -> dict[str, CriterionAssessment]:
        """Builds structured CriterionAssessment for each criterion owned by this domain,
        integrating the AI specialist's compact evaluations with claim metadata and evidence provenance.
        """
        owned_criteria = self.get_owned_criteria()
        evaluations: dict[str, CriterionAssessment] = {}

        # Build claim lookup map
        claim_map: dict[str, Any] = {}
        for c in claims:
            fk = getattr(c, "field", None)
            fkey = getattr(fk, "field_key", "") if fk else ""
            if fkey:
                claim_map[fkey.lower()] = c

        evidence_map: dict[str, list[Any]] = {}
        known_evidence_ids: set[str] = set()
        for ev in evidence:
            cid = str(getattr(ev, "claim_id", ""))
            if cid:
                evidence_map.setdefault(cid, []).append(ev)
            ev_identifier = str(getattr(ev, "evidence_id", None) or getattr(ev, "id", "") or "").strip()
            if ev_identifier:
                known_evidence_ids.add(ev_identifier)

        legacy_field_aliases: dict[str, tuple[str, ...]] = {
            "ps_01": ("problem_solved",),
            "ps_02": ("target_market",),
            "ps_06": ("solution_value_prop", "description"),
            "bc_01": ("business_model",),
            "ii_07": ("patents", "ip_status"),
            "ft_01": ("founder_names",),
        }

        # Build compact_map verifying criterion IDs against registry
        compact_map: dict[str, CompactCriterionResult] = {}
        for c in compact_criteria:
            raw_cid = getattr(c, "criterion_id", None)
            if raw_cid and isinstance(raw_cid, str):
                normalized_cid = raw_cid.upper().strip()
                if normalized_cid in owned_criteria:
                    compact_map[normalized_cid] = c

        for cid in owned_criteria:
            meta = get_criterion_metadata(cid)
            crit_name = meta.get("name", cid) if isinstance(meta, dict) else cid
            slide_num = meta.get("slide", 1) if isinstance(meta, dict) else 1
            source_locations = [f"Slide {slide_num}"]

            # Find matching extracted claim (with legacy form-profile aliases as fallback)
            cid_prefix = cid.lower().replace("-", "_")
            matched_claim = None
            for fkey, claim_obj in claim_map.items():
                if fkey.startswith(cid_prefix):
                    matched_claim = claim_obj
                    break
            if matched_claim is None:
                for alias_key in legacy_field_aliases.get(cid_prefix, ()):
                    if alias_key in claim_map:
                        matched_claim = claim_map[alias_key]
                        break

            val_str = None
            claim_confidence = confidence_fallback
            if matched_claim:
                val = (
                    matched_claim.value_string
                    if matched_claim.value_string is not None else (
                        str(matched_claim.value_number)
                        if matched_claim.value_number is not None else (
                            str(matched_claim.value_boolean)
                            if matched_claim.value_boolean is not None else (
                                str(matched_claim.value_json)
                                if matched_claim.value_json is not None else ""
                            )
                        )
                    )
                )
                val_str = str(val) if val else None
                claim_confidence = float(getattr(matched_claim, "confidence_score", confidence_fallback))
                ev_list = evidence_map.get(str(matched_claim.id), [])
                claim_ev_ids = [str(getattr(ev, "evidence_id", getattr(ev, "id", ""))) for ev in ev_list if str(getattr(ev, "evidence_id", getattr(ev, "id", ""))).strip()]
                for ev in ev_list:
                    sec = getattr(ev, "section_name", "")
                    pg = getattr(ev, "page_number", None)
                    loc = f"{sec} (Page {pg})" if pg else sec
                    if loc and loc not in source_locations:
                        source_locations.append(loc)
            else:
                ev_list = []
                claim_ev_ids = []

            # Check AI specialist compact evaluation
            crit_res = compact_map.get(cid.upper())
            if crit_res and hasattr(crit_res, "verification_status") and isinstance(crit_res.verification_status, VerificationStatus):
                v_status = crit_res.verification_status
                narrative = crit_res.rationale
                seen_ev: set[str] = set()
                model_ev_ids: list[str] = []
                for eid in (crit_res.evidence_ids or []):
                    clean_eid = str(eid).strip()
                    # Evidence guard: only IDs that exist in this startup's evidence set survive.
                    if known_evidence_ids and clean_eid not in known_evidence_ids:
                        continue
                    if clean_eid and clean_eid not in seen_ev:
                        seen_ev.add(clean_eid)
                        model_ev_ids.append(clean_eid)
                evidence_ids = model_ev_ids if model_ev_ids else claim_ev_ids
                score_val = crit_res.score

                prov = getattr(crit_res, "source_provenance", None)
                if prov and str(prov).strip() and str(prov).strip() not in source_locations:
                    source_locations.append(str(prov).strip())

                # Provenance guard: cannot mark VERIFIED_DOCUMENTED when zero evidence exists
                # or when linked evidence lacks an authentic snippet
                if v_status == VerificationStatus.VERIFIED_DOCUMENTED:
                    if not evidence_ids:
                        v_status = (
                            VerificationStatus.MISSING_INFORMATION
                            if self._is_missing_placeholder(val_str)
                            else VerificationStatus.SELF_REPORTED_ONLY
                        )
                    elif ev_list and all(getattr(e, "evidence_snippet", None) is None for e in ev_list):
                        v_status = VerificationStatus.SELF_REPORTED_ONLY
            else:
                # Missing or invalid from model response: fail closed, do not invent
                if meta.get("is_conditional", False):
                    v_status = VerificationStatus.NOT_APPLICABLE
                    narrative = "None disclosed (conditional field)."
                elif meta.get("is_required", True):
                    v_status = VerificationStatus.MISSING_INFORMATION
                    narrative = f"Missing from specialist evaluation: {crit_name}."
                    claim_confidence = 0.0
                else:
                    v_status = VerificationStatus.NOT_APPLICABLE
                    narrative = "Optional field not provided."
                evidence_ids = claim_ev_ids
                score_val = None

            # Consistency rule: MISSING_INFORMATION means the applicant supplied nothing. If an
            # extracted applicant value exists, the honest grade is applicant-reported (unverified).
            if v_status == VerificationStatus.MISSING_INFORMATION and not self._is_missing_placeholder(val_str):
                v_status = VerificationStatus.SELF_REPORTED_ONLY
                narrative = f"{narrative} Applicant-reported value present; no supporting document cited."

            # Conditional refine override
            v_status = self.refine_verification_status(cid, val_str, v_status, claims)

            extra_missing = getattr(crit_res, "missing_information", None) if crit_res else None
            crit_weaknesses = (
                [f"Unverified or missing documentation for {crit_name}"]
                if v_status in (VerificationStatus.SELF_REPORTED_ONLY, VerificationStatus.MISSING_INFORMATION)
                else []
            )
            if extra_missing and str(extra_missing).strip():
                missing_note = str(extra_missing).strip()
                if missing_note not in crit_weaknesses:
                    crit_weaknesses.append(missing_note)

            evaluations[cid] = CriterionAssessment(
                criterion_id=cid,
                criterion_name=crit_name,
                extracted_startup_response=val_str,
                assessment_narrative=narrative,
                evidence_ids=evidence_ids,
                source_locations=source_locations,
                verification_status=v_status,
                score=score_val,
                strengths=[narrative] if v_status == VerificationStatus.VERIFIED_DOCUMENTED else [],
                weaknesses=crit_weaknesses,
                risks=[f"Contradiction in {crit_name}"] if v_status == VerificationStatus.CONTRADICTED else [],
                contradictions=[narrative] if v_status == VerificationStatus.CONTRADICTED else [],
                confidence_score=claim_confidence,
                confidence_limitations=(
                    str(extra_missing).strip()
                    if extra_missing and str(extra_missing).strip()
                    else ("Independent external verification pending external search integration" if v_status != VerificationStatus.VERIFIED_DOCUMENTED else None)
                ),
            )

        return evaluations

    @staticmethod
    def _is_missing_placeholder(value: Optional[str]) -> bool:
        """Returns True if a criterion value represents missing/unsubmitted/placeholder content."""
        if value is None:
            return True
        cleaned = str(value).strip().lower()
        return cleaned in (
            "",
            "none",
            "null",
            "missing",
            "missing from application",
            "none disclosed (conditional field)",
            "optional field not provided",
            "not disclosed",
            "not provided",
            "not mentioned",
            "unknown",
        )

    def refine_verification_status(
        self,
        criterion_id: str,
        value: Optional[str],
        default_status: VerificationStatus,
        all_claims: list[Any]
    ) -> VerificationStatus:
        """Domain-specific logic to refine verification statuses (e.g. conditional prototype, free vs paid)."""
        return default_status

    def _has_budget_headroom_for_retry(self, evaluation_id: str | None, request: AICompletionRequest) -> tuple[bool, str | None]:
        """Verifies ledger budget headroom before retrying a failed criterion batch."""
        if not evaluation_id:
            return True, None
        ledger = CostLedgerManager.get_instance().get_ledger(evaluation_id)
        if ledger is None:
            return True, None
        model_name = get_settings().ai_reasoning_model or getattr(self.gateway, "model", "claude-sonnet-4-6")
        est_input = max(400, (len(request.system_prompt) + len(request.user_prompt)) // 4)
        est_cost = ledger.pricing_catalog.calculate_cost(
            model=model_name,
            prompt_tokens=est_input,
            completion_tokens=int(request.max_output_tokens or self.batch_max_output_tokens),
        )
        if ledger.remaining_budget_usd < est_cost or ledger.remaining_budget_usd <= 0.0:
            return False, (
                f"Insufficient remaining budget (${ledger.remaining_budget_usd:.6f}) "
                f"to retry batch (estimated worst-case ${est_cost:.6f})"
            )
        return True, None

    @staticmethod
    def _is_truncation_error(exc: BaseException) -> bool:
        msg = str(exc).lower()
        return isinstance(exc, AIResponseParseError) and ("truncated" in msg or "finish_reason='length'" in msg or "max_tokens" in msg)

    @staticmethod
    def _resolve_batch_evidence(
        batch_out: DomainCriterionBatchOutput,
        batch_cids: list[str],
        scoped_claims: list[Any],
        scoped_evidence: list[Any],
        all_evidence: list[Any],
    ) -> DomainCriterionBatchOutput:
        """Maps cited evidence handles to real evidence IDs, rejects unknown references, and resolves
        source provenance locally from evidence metadata (never from model text)."""
        handles = build_batch_evidence_handles(batch_cids, scoped_claims, scoped_evidence)
        evidence_by_id: dict[str, Any] = {}
        for ev in list(all_evidence) + list(scoped_evidence):
            ev_id = str(getattr(ev, "evidence_id", None) or getattr(ev, "id", "") or "").strip()
            if ev_id:
                evidence_by_id.setdefault(ev_id, ev)
        resolved_items: list[BatchCriterionResult] = []
        for item in batch_out.criteria:
            resolved, rejected = resolve_evidence_references(
                list(item.evidence_ids or []), handles, set(evidence_by_id.keys())
            )
            if rejected:
                logger.warning(
                    f"[EVIDENCE GUARD] {item.criterion_id}: rejected {len(rejected)} unknown evidence reference(s)."
                )
            locations: list[str] = []
            for ev_id in resolved:
                loc = evidence_location(evidence_by_id[ev_id])
                if loc not in locations:
                    locations.append(loc)
            payload = item.model_dump()
            payload.update({
                "evidence_ids": resolved,
                "source_provenance": "; ".join(locations) or None,
            })
            resolved_items.append(BatchCriterionResult.model_validate(payload))
        return DomainCriterionBatchOutput(
            domain=batch_out.domain, batch_index=batch_out.batch_index, criteria=resolved_items
        )

    @staticmethod
    def _coerce_batch_output(
        raw_draft: Any,
        domain_key: str,
        batch_idx: int,
        expected_batch_ids: list[str],
    ) -> DomainCriterionBatchOutput:
        """Validates gateway response as DomainCriterionBatchOutput strictly matching expected_batch_ids."""
        expected_set = {c.upper().strip() for c in expected_batch_ids}

        if isinstance(raw_draft, DomainCriterionBatchOutput):
            batch_out = raw_draft
        elif isinstance(raw_draft, CompactDomainAssessment):
            filtered = [
                c for c in raw_draft.criteria
                if str(getattr(c, "criterion_id", "")).upper().strip() in expected_set
            ]
            batch_out = DomainCriterionBatchOutput(
                domain=raw_draft.domain or domain_key,
                batch_index=batch_idx,
                criteria=filtered,
            )
        elif isinstance(raw_draft, dict):
            batch_out = DomainCriterionBatchOutput.model_validate(raw_draft)
        else:
            raise AIResponseParseError(f"Unsupported domain batch response type: {type(raw_draft)}")

        seen: set[str] = set()
        for item in batch_out.criteria:
            cid = str(item.criterion_id or "").upper().strip()
            if cid not in expected_set:
                raise AIResponseParseError(
                    f"Batch {batch_idx} returned unexpected criterion '{cid}' not in {expected_batch_ids}"
                )
            if cid in seen:
                raise AIResponseParseError(f"Batch {batch_idx} returned duplicate criterion '{cid}'")
            seen.add(cid)

        missing = [cid for cid in expected_batch_ids if cid.upper().strip() not in seen]
        if missing:
            raise AIResponseParseError(
                f"Batch {batch_idx} omitted assigned criteria {missing}"
            )
        return batch_out

    def evaluate(
        self,
        profile: Any,
        claims: list[Any],
        evidence: list[Any],
        conflicts: list[Any],
        metadata: dict[str, Any]
    ) -> DomainAssessmentReport:
        """Orchestrates criterion-batched domain diligence, local deterministic merge,
        deterministic summary synthesis, and per-batch failure recovery."""
        evaluation_id = metadata.get("evaluation_id")
        startup_id = str(getattr(profile, "startup_id", getattr(profile, "id", "")))

        # 1. Filter Context to Domain's Owned Scope (Prevents cross-domain leakage)
        domain_prefix_map = {
            "problem_solution": ("ps_", ["problem", "solution", "product", "technology", "trl", "stage"]),
            "market_opportunity": ("mo_", ["market", "target_market", "tam", "sam", "som", "competitor", "competition"]),
            "founder_team": ("ft_", ["founder", "team", "advisor"]),
            "commercialisation": ("bc_", ["business", "revenue", "traction", "customer", "user"]),
            "innovation_impact": ("ii_", ["patent", "ip", "impact", "sdg"]),
            "financials_support": (("fi_", "cm_"), ["financial", "funding", "runway", "burn"]),
        }

        prefix_info = domain_prefix_map.get(self.domain_key)
        if prefix_info:
            prefixes, leg_keys = prefix_info
            if isinstance(prefixes, str):
                prefixes = (prefixes,)

            domain_claims = []
            for c in claims:
                fk = getattr(c, "field", None)
                fkey = str(getattr(fk, "field_key", "") if fk else getattr(c, "field_name", "")).lower()
                if any(fkey.startswith(p) for p in prefixes) or any(k in fkey for k in leg_keys):
                    domain_claims.append(c)

            if domain_claims:
                claims_to_use = domain_claims
                claim_ids = {str(getattr(c, "id", "")) for c in claims_to_use}
                evidence_to_use = [ev for ev in evidence if str(getattr(ev, "claim_id", "")) in claim_ids] or evidence
                conflicts_to_use = conflicts
            else:
                claims_to_use = claims
                evidence_to_use = evidence
                conflicts_to_use = conflicts
        else:
            claims_to_use = claims
            evidence_to_use = evidence
            conflicts_to_use = conflicts

        self.validate_inputs(profile, claims_to_use, evidence_to_use, conflicts_to_use, metadata)

        # 2. Load prompt provenance metadata (if registered)
        prompt_data = None
        fallback_key = getattr(self, "get_fallback_prompt_key", lambda: None)()
        for pkey in [self.domain_key, fallback_key]:
            if not pkey:
                continue
            try:
                prompt_data = PromptManager.load_prompt(domain=pkey, version="latest")
                break
            except Exception:
                continue

        if not prompt_data:
            prompt_data = {
                "system_prompt": f"You are the senior {self.domain_title} investment diligence expert at TIDES IIT Roorkee.",
                "user_prompt": "Evaluate the following startup evidence:\n\n{context}",
                "prompt_name": f"{self.domain_title} Analysis Prompt",
                "prompt_version": "2.1.0",
                "prompt_hash": "batched-v2-1-hash",
            }

        company_name = ""
        if hasattr(profile, "startup") and profile.startup:
            company_name = getattr(profile.startup, "startup_name", "")
        if not company_name:
            company_name = getattr(profile, "company_name", getattr(profile, "startup_name", getattr(profile, "name", ""))) or ""

        external_items = getattr(self, "_current_external_items", None)
        owned_criteria = self.get_owned_criteria()

        max_criteria = int(metadata.get("max_criteria_per_call") or self.max_criteria_per_call)
        batch_token_cap = int(metadata.get("batch_max_output_tokens") or self.batch_max_output_tokens)
        max_batch_retries = (
            int(metadata["domain_batch_max_retries"])
            if "domain_batch_max_retries" in metadata
            else int(get_settings().ai_domain_batch_max_retries)
        )

        batches = batch_criteria(owned_criteria, max_criteria_per_call=max_criteria)

        # Load prior incomplete checkpoint ONLY when resuming an interrupted run
        checkpoint_state = load_domain_batch_checkpoint(evaluation_id, self.domain_key)
        is_resuming = bool(checkpoint_state.get("incomplete")) or bool(metadata.get("resume_domain_batches"))
        if not is_resuming:
            checkpoint_state = {"completed_batches": {}, "failed_batches": {}, "incomplete": False, "cost_usd": 0.0}

        completed_batches: dict[str, Any] = dict(checkpoint_state.get("completed_batches") or {})
        failed_batches: dict[str, Any] = dict(checkpoint_state.get("failed_batches") or {})
        total_cost_usd = float(checkpoint_state.get("cost_usd", 0.0) or 0.0)
        model_used = checkpoint_state.get("model_used")

        batch_outputs: list[DomainCriterionBatchOutput] = []

        # 3. Execute scoped criterion batches (skipping already completed checkpoint batches)
        for batch_idx, batch_cids in enumerate(batches):
            bkey = str(batch_idx)
            if bkey in completed_batches:
                restored_batch = DomainCriterionBatchOutput.model_validate(completed_batches[bkey])
                batch_outputs.append(restored_batch)
                continue

            sys_prompt, usr_prompt = build_domain_batch_prompts(
                domain_key=self.domain_key,
                domain_title=self.domain_title,
                company_name=company_name,
                batch_index=batch_idx,
                total_batches=len(batches),
                batch_criterion_ids=batch_cids,
                claims=claims_to_use,
                evidence=evidence_to_use,
                conflicts=conflicts_to_use,
                prompt_version=prompt_data["prompt_version"],
                external_research_items=external_items,
            )

            batch_result: DomainCriterionBatchOutput | None = None
            last_exc: Exception | None = None

            def _dispatch(cids: list[str], label: str) -> tuple[DomainCriterionBatchOutput, float, str | None]:
                s_prompt, u_prompt = (sys_prompt, usr_prompt) if list(cids) == list(batch_cids) else build_domain_batch_prompts(
                    domain_key=self.domain_key,
                    domain_title=self.domain_title,
                    company_name=company_name,
                    batch_index=batch_idx,
                    total_batches=len(batches),
                    batch_criterion_ids=cids,
                    claims=claims_to_use,
                    evidence=evidence_to_use,
                    conflicts=conflicts_to_use,
                    prompt_version=prompt_data["prompt_version"],
                    external_research_items=external_items,
                )
                req = AICompletionRequest(
                    system_prompt=s_prompt,
                    user_prompt=u_prompt,
                    prompt_version=prompt_data["prompt_version"],
                    metadata={
                        "domain": self.domain_key,
                        "batch_index": batch_idx,
                        "total_batches": len(batches),
                        "batch_criterion_ids": list(cids),
                        "compact_schema": DOMAIN_BATCH_COMPACT_SCHEMA.replace("<domain_key>", self.domain_key),
                        # Distinct per dispatch so the ledger never de-duplicates a genuinely new paid call.
                        "operation_id": f"op_{self.domain_key}_b{batch_idx + 1}{label}_{uuid.uuid4().hex[:8]}",
                    },
                    evaluation_id=evaluation_id,
                    startup_id=startup_id,
                    agent_name=f"domain_{self.domain_key}_batch_{batch_idx + 1}{label}",
                    operation_type="expert_evaluation",
                    max_output_tokens=resolve_domain_batch_output_token_limit(len(cids), batch_token_cap),
                )
                if label:
                    has_headroom, headroom_reason = self._has_budget_headroom_for_retry(evaluation_id, req)
                    if not has_headroom:
                        raise RuntimeError(headroom_reason or "Insufficient budget for recovery dispatch")
                res = self.gateway.complete_json(req, response_model=DomainCriterionBatchOutput)
                raw_draft = res.data if hasattr(res, "data") else res
                coerced = self._coerce_batch_output(raw_draft, self.domain_key, batch_idx, list(cids))
                coerced = self._resolve_batch_evidence(coerced, list(cids), claims_to_use, evidence_to_use, evidence)
                cost = float(getattr(res.metadata, "cost_usd", 0.0) if hasattr(res, "metadata") else 0.0)
                mdl = getattr(res.metadata, "model", None) if hasattr(res, "metadata") else None
                return coerced, cost, mdl

            def _save_incomplete() -> None:
                checkpoint_state.update({
                    "completed_batches": completed_batches,
                    "failed_batches": failed_batches,
                    "incomplete": True,
                    "cost_usd": round(total_cost_usd, 6),
                    "model_used": model_used,
                })
                save_domain_batch_checkpoint(evaluation_id, self.domain_key, checkpoint_state)

            # Policy: identical requests are retried only for parse/validation failures and only when
            # AI_DOMAIN_BATCH_MAX_RETRIES > 0 (default 0). Truncation is never retried identically.
            for attempt in range(1 + max(0, max_batch_retries)):
                try:
                    if attempt > 0:
                        logger.warning(
                            f"[RETRY DISPATCH] {self.domain_title} batch {batch_idx + 1}: identical-request retry "
                            f"{attempt}/{max_batch_retries} after parse failure."
                        )
                    batch_result, call_cost, mdl = _dispatch(list(batch_cids), f"_r{attempt}" if attempt else "")
                    total_cost_usd += call_cost
                    model_used = mdl or model_used
                    break
                except AIBudgetExhaustedError:
                    _save_incomplete()
                    raise
                except Exception as exc:
                    last_exc = exc
                    logger.warning(
                        f"[{self.domain_title}] Batch {batch_idx + 1}/{len(batches)} attempt {attempt + 1} failed: "
                        f"{type(exc).__name__}: {str(exc)[:200]}"
                    )
                    if self._is_truncation_error(exc):
                        break  # deterministic: never resend the identical request

            # One-time split recovery: a truncated multi-criterion batch is re-run one criterion per call.
            if (
                batch_result is None
                and last_exc is not None
                and self._is_truncation_error(last_exc)
                and len(batch_cids) > 1
                and bool(metadata.get("split_on_truncation", get_settings().ai_domain_split_on_truncation))
            ):
                logger.warning(
                    f"[RETRY DISPATCH] {self.domain_title} batch {batch_idx + 1} truncated; splitting into "
                    f"{len(batch_cids)} single-criterion requests (budget-checked, distinct operation IDs)."
                )
                split_items: list[Any] = []
                try:
                    for pos, single_cid in enumerate(batch_cids):
                        single_out, call_cost, mdl = _dispatch([single_cid], f"_split{pos + 1}")
                        total_cost_usd += call_cost
                        model_used = mdl or model_used
                        split_items.extend(single_out.criteria)
                    batch_result = DomainCriterionBatchOutput(
                        domain=self.domain_key, batch_index=batch_idx, criteria=split_items
                    )
                    last_exc = None
                except AIBudgetExhaustedError:
                    _save_incomplete()
                    raise
                except Exception as exc:
                    last_exc = exc
                    batch_result = None
                    logger.warning(
                        f"[{self.domain_title}] Split recovery for batch {batch_idx + 1} failed: "
                        f"{type(exc).__name__}: {str(exc)[:200]}"
                    )

            if batch_result is None:
                err_msg = str(last_exc or "Batch execution failed")
                failed_batches[bkey] = {
                    "batch_index": batch_idx,
                    "criteria": list(batch_cids),
                    "error": err_msg,
                }
                checkpoint_state.update({
                    "completed_batches": completed_batches,
                    "failed_batches": failed_batches,
                    "incomplete": True,
                    "cost_usd": round(total_cost_usd, 6),
                    "model_used": model_used,
                })
                save_domain_batch_checkpoint(evaluation_id, self.domain_key, checkpoint_state)

                partial_compact = [crit for bo in batch_outputs for crit in bo.criteria]
                return self.build_failed_domain_report(
                    evaluation_id=evaluation_id,
                    startup_id=startup_id,
                    claims=claims,
                    evidence=evidence,
                    error_message=err_msg,
                    prompt_data=prompt_data,
                    partial_compact_criteria=partial_compact,
                    failed_batches=list(failed_batches.values()),
                    cost_usd=round(total_cost_usd, 6),
                    model_used=model_used,
                )

            completed_batches[bkey] = batch_result.model_dump(mode="json")
            failed_batches.pop(bkey, None)
            batch_outputs.append(batch_result)
            checkpoint_state.update({
                "completed_batches": completed_batches,
                "failed_batches": failed_batches,
                "incomplete": True,
                "cost_usd": round(total_cost_usd, 6),
                "model_used": model_used,
            })
            save_domain_batch_checkpoint(evaluation_id, self.domain_key, checkpoint_state)

        # 4. Deterministic Python local merge (zero LLM merge calls)
        merged_compact = merge_domain_criterion_batches(
            self.domain_key,
            batch_outputs,
            expected_batches=batches,
        )

        # Remove temporary incomplete checkpoint now that all domain batches succeeded
        if evaluation_id and not metadata.get("preserve_batch_checkpoint"):
            ckpt_path = get_domain_batch_checkpoint_path(evaluation_id, self.domain_key)
            if ckpt_path.exists():
                try:
                    ckpt_path.unlink()
                except OSError:
                    pass

        criterion_evals = self.build_criterion_assessments_from_compact(
            claims=claims,
            evidence=evidence,
            compact_criteria=merged_compact,
        )

        # 5. Deterministic Python domain-level synthesis from merged criteria
        synth = synthesize_domain_summary_and_findings(
            domain_key=self.domain_key,
            domain_title=self.domain_title,
            criterion_evals=criterion_evals,
            total_criteria_count=len(owned_criteria),
            has_external_research=bool(external_items),
        )

        return DomainAssessmentReport(
            domain=self.domain_key,
            domain_key=self.domain_key,
            domain_title=self.domain_title,
            evaluation_id=evaluation_id,
            startup_id=startup_id,
            criteria_evaluated=owned_criteria,
            criteria_evaluations=criterion_evals,
            summary=synth["summary"],
            executive_summary=synth["executive_summary"],
            executive_conclusion=synth["executive_conclusion"],
            reasoning=synth["reasoning"],
            investment_implication=synth["investment_implication"],
            observations=synth["observations"],
            risks=synth["risks"],
            questions=synth["questions"],
            missing_evidence=synth["missing_evidence"],
            confidence=synth["confidence"],
            strengths=synth["strengths"],
            weaknesses=synth["weaknesses"],
            unsupported_claims=synth["unsupported_claims"],
            contradictions=synth["contradictions"],
            missing_information=synth["missing_information"],
            follow_up_questions=synth["follow_up_questions"],
            composite_domain_confidence=synth["composite_domain_confidence"],
            confidence_limitations=synth["confidence_limitations"],
            prompt_name=prompt_data["prompt_name"],
            prompt_version=prompt_data["prompt_version"],
            prompt_hash=prompt_data["prompt_hash"],
            agent_version=self.get_agent_version(),
            model_used=model_used,
            cost_usd=round(total_cost_usd, 6),
            generated_at=datetime.now(timezone.utc),
        )

    def get_fallback_prompt_key(self) -> str:
        """Returns the legacy prompt folder key for backward compatibility."""
        return ""

    def build_failed_domain_report(
        self,
        evaluation_id: str | None,
        startup_id: str | None,
        claims: list[Any],
        evidence: list[Any],
        error_message: str,
        prompt_data: dict[str, Any] | None = None,
        partial_compact_criteria: list[CompactCriterionResult] | None = None,
        failed_batches: list[dict[str, Any]] | None = None,
        cost_usd: float = 0.0,
        model_used: str | None = None,
    ) -> DomainAssessmentReport:
        """Constructs a controlled, clearly recorded failure report when batch execution fails.

        Preserves any completed batch criteria without discarding or fabricating results,
        forces non-positive domain status (confidence=0.0, empty strengths, explicit operational Risk),
        and marks only failed/unexecuted criteria as MISSING_INFORMATION.
        """
        owned_criteria = self.get_owned_criteria()
        criterion_evals: dict[str, CriterionAssessment] = {}

        partial_evals: dict[str, CriterionAssessment] = {}
        if partial_compact_criteria:
            partial_ids = {str(c.criterion_id).upper().strip() for c in partial_compact_criteria}
            built_partial = self.build_criterion_assessments_from_compact(
                claims=claims,
                evidence=evidence,
                compact_criteria=partial_compact_criteria,
            )
            partial_evals = {cid: ev for cid, ev in built_partial.items() if cid.upper() in partial_ids}

        for cid in owned_criteria:
            if cid in partial_evals:
                criterion_evals[cid] = partial_evals[cid]
                continue

            meta = get_criterion_metadata(cid)
            name = meta.get("name", cid) if isinstance(meta, dict) else (getattr(meta, "name", cid) if meta else cid)
            extracted_val = None
            cid_prefix = cid.lower().replace("-", "_")
            for c in claims:
                fk = getattr(c, "field", None)
                fkey = str(getattr(fk, "field_key", "") if fk else getattr(c, "field_name", "")).lower()
                if fkey.startswith(cid_prefix):
                    extracted_val = getattr(c, "value_string", None) or (
                        str(getattr(c, "value_number", "")) if getattr(c, "value_number", None) is not None else None
                    )
                    break

            criterion_evals[cid] = CriterionAssessment(
                criterion_id=cid,
                criterion_name=name,
                extracted_startup_response=extracted_val,
                assessment_narrative=f"Assessment unavailable: AI model batch failure ({error_message}).",
                evidence_ids=[],
                source_locations=[],
                verification_status=VerificationStatus.MISSING_INFORMATION,
                strengths=[],
                weaknesses=[f"Evaluation incomplete: AI batch failure ({error_message})"],
                risks=[f"Unverified criterion due to batch failure: {cid}"],
                contradictions=[],
                confidence_score=0.0,
                confidence_limitations=f"AI batch failure: {error_message}",
            )

        recorded_failures = list(failed_batches or [{"batch_index": 0, "criteria": owned_criteria, "error": error_message}])
        batch_desc = ", ".join(str(b.get("batch_index")) for b in recorded_failures)
        err_summary = f"{self.domain_title} evaluation incomplete: batch failure [{batch_desc}] ({error_message})."

        synth = synthesize_domain_summary_and_findings(
            domain_key=self.domain_key,
            domain_title=self.domain_title,
            criterion_evals=criterion_evals,
            total_criteria_count=len(owned_criteria),
            incomplete_batches=recorded_failures,
        )

        return DomainAssessmentReport(
            domain=self.domain_key,
            domain_key=self.domain_key,
            domain_title=self.domain_title,
            evaluation_id=evaluation_id,
            startup_id=startup_id,
            criteria_evaluated=owned_criteria,
            criteria_evaluations=criterion_evals,
            summary=err_summary,
            executive_summary=synth["executive_summary"],
            executive_conclusion=synth["executive_conclusion"],
            reasoning=synth["reasoning"],
            investment_implication=synth["investment_implication"],
            observations=[],
            risks=synth["risks"],
            questions=synth["questions"],
            missing_evidence=synth["missing_evidence"],
            confidence=ConfidenceHierarchy(
                finding_confidence=0.0,
                evidence_confidence=0.0,
                reasoning_confidence=0.0,
                overall_domain_confidence=0.0,
            ),
            strengths=[],
            weaknesses=[f"AI evaluation failed with batch error: {error_message}"],
            unsupported_claims=[],
            contradictions=[],
            missing_information=[
                f"{cid}: {get_criterion_metadata(cid).get('name', cid) if isinstance(get_criterion_metadata(cid), dict) else cid}"
                for cid in owned_criteria
                if cid not in partial_evals
            ],
            follow_up_questions=[f"Request detailed manual verification of {self.domain_title} criteria."],
            composite_domain_confidence=0.0,
            confidence_limitations=f"AI output batch failure: {error_message}",
            prompt_name=prompt_data["prompt_name"] if prompt_data else f"{self.domain_title} Analysis Prompt",
            prompt_version=prompt_data["prompt_version"] if prompt_data else "2.1.0",
            prompt_hash=prompt_data["prompt_hash"] if prompt_data else "fallback-hash",
            agent_version=self.get_agent_version(),
            model_used=model_used,
            cost_usd=cost_usd,
            generated_at=datetime.now(timezone.utc),
        )
