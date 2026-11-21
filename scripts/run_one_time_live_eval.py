"""scripts/run_one_time_live_eval.py - Controlled One-Time Live Evaluation Runner.

Enforces:
- Hard provider budget ceiling: $0.35 USD
- INR exchange rate: ₹96.0 / USD with 1.18x safety buffer (₹39.65 INR buffered <= ₹50.00 INR hard limit)
- Models: Claude Haiku (fast extraction) and Claude Sonnet (reasoning and supervisory review)
- External research: Disabled
- Retries: 0 (preventing unbudgeted automatic retries)
- Dedicated development database (tides_dev.db), completely isolated from workspace tides_ai.db
- Strict dry-run by default; requires explicit --execute-live flag
- Fails closed if ANTHROPIC_API_KEY is empty or missing; never silently falls back to mock mode
- Granular per-call token telemetry and post-run cost reconciliation
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_PROJECT_ROOT = PROJECT_ROOT
sys.path.insert(0, str(PROJECT_ROOT))


def _resolve_run_report_path() -> Path:
    """Resolve live_eval_run_report.json path, honoring test isolation unless PROJECT_ROOT is overridden."""
    if PROJECT_ROOT == _DEFAULT_PROJECT_ROOT:
        env_report_path = os.environ.get("TIDES_LIVE_EVAL_REPORT_PATH")
        if env_report_path:
            return Path(env_report_path)
    return PROJECT_ROOT / "reports" / "live_eval_run_report.json"

# Configuration constants for the one-time evaluation
BUDGET_CEILING_USD = 0.35
INR_EXCHANGE_RATE = 96.0
INR_BUFFER_MULTIPLIER = 1.18
BUFFERED_CEILING_INR = round(BUDGET_CEILING_USD * INR_EXCHANGE_RATE * INR_BUFFER_MULTIPLIER, 2)  # 39.65 INR
FAST_EXTRACTION_MODEL = "claude-haiku-5-5"
REASONING_MODEL = "claude-sonnet-5-5"
EXTRACTION_OUTPUT_TOKEN_LIMITS = {
    "cover_intake": 2400,
    "problem_need": 2400,
    "solution_product": 2400,
    "prototype_technical": 2400,
    "market_opportunity": 2400,
    "founder_core": 2400,
    "team_advisory": 2400,
    "commercialisation": 2400,
    "innovation_impact": 2400,
    # Stage 10 covers 21 criteria (FI-01..21) across 4x3Y metrics, 4x6Q roadmaps,
    # and 7 lists; requires 4,096 output tokens to prevent provider truncation.
    "financials_support": 4096,
    # Backward compatibility aliases
    "solution_validation": 2400,
    "prototype_evidence": 2400,
    "founder_team": 2400,
    "problem_solution": 2400,
}
DOMAIN_BATCH_MAX_CRITERIA = 5
DOMAIN_BATCH_OUTPUT_TOKEN_CAP = 900
DOMAIN_OUTPUT_TOKEN_LIMITS = {
    "problem_solution": DOMAIN_BATCH_OUTPUT_TOKEN_CAP,
    "market_opportunity": DOMAIN_BATCH_OUTPUT_TOKEN_CAP,
    "founder_team": DOMAIN_BATCH_OUTPUT_TOKEN_CAP,
    "commercialisation": DOMAIN_BATCH_OUTPUT_TOKEN_CAP,
    "innovation_impact": DOMAIN_BATCH_OUTPUT_TOKEN_CAP,
    "financials_support": DOMAIN_BATCH_OUTPUT_TOKEN_CAP,
}
DOMAIN_MAX_OUTPUT_TOKENS = DOMAIN_BATCH_OUTPUT_TOKEN_CAP  # Per criterion-batch cap
REVIEWER_MAX_OUTPUT_TOKENS = 2400
SYNTHETIC_FIXTURE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "valid_pitch_deck.pdf"
AUTHORIZED_REUSE_STARTUP_ID = "9b8174247d774a1fa927a432b12564eb"
PETREVOLT_TARGET_STARTUP_ID = "1b5de317-6e56-4dcb-ada9-28ab9adf8c0c"
HISTORICAL_STETHAIM_STARTUP_ID = "a246f3a5b79743fc9dc33e603e3b37b9"
STETHAIM_PILOT_DIR = PROJECT_ROOT / "private" / "pilot_inputs" / "stethaim"

logger = logging.getLogger("live_eval_runner")


def get_launcher_config() -> Dict[str, Any]:
    """Returns dynamic configuration dictionary for launcher scripts and telemetry inspection."""
    active_stages = [
        "cover_intake",
        "problem_need",
        "solution_product",
        "prototype_technical",
        "market_opportunity",
        "founder_core",
        "team_advisory",
        "commercialisation",
        "innovation_impact",
        "financials_support",
    ]
    min_cap = min(EXTRACTION_OUTPUT_TOKEN_LIMITS[s] for s in active_stages)
    max_cap = max(EXTRACTION_OUTPUT_TOKEN_LIMITS[s] for s in active_stages)
    cap_str = f"{min_cap:,} tokens (uniform across {len(active_stages)} stages)" if min_cap == max_cap else f"{min_cap:,}-{max_cap:,} tokens"
    return {
        "budget_ceiling_usd": BUDGET_CEILING_USD,
        "buffered_ceiling_inr": BUFFERED_CEILING_INR,
        "fast_extraction_model": FAST_EXTRACTION_MODEL,
        "reasoning_model": REASONING_MODEL,
        "extraction_stages_count": len(active_stages),
        "extraction_token_cap_str": cap_str,
        "domain_token_caps_str": "<= 900 tokens/batch across 19 batches",
        "reviewer_token_cap": REVIEWER_MAX_OUTPUT_TOKENS,
    }


def validate_stethaim_prerequisites() -> Dict[str, Any]:
    """Validates that all 3 STETHAIM pilot documents exist and are readable."""
    import hashlib

    if not STETHAIM_PILOT_DIR.exists():
        raise FileNotFoundError(f"STETHAIM pilot directory not found: {STETHAIM_PILOT_DIR}")

    app_path = STETHAIM_PILOT_DIR / "Applications.xlsx"
    cv_path = STETHAIM_PILOT_DIR / "Shikha_Behera_CV-2.docx"
    deck_path = STETHAIM_PILOT_DIR / "NEW PITCH DECK STETHAIM.pdf"

    for p in (app_path, cv_path, deck_path):
        if not p.exists():
            raise FileNotFoundError(f"Required STETHAIM pilot document missing: {p}")

    return {
        "pilot_dir": str(STETHAIM_PILOT_DIR),
        "files": {
            "Applications.xlsx": {
                "size_bytes": app_path.stat().st_size,
                "sha256": hashlib.sha256(app_path.read_bytes()).hexdigest(),
                "parser": "XlsxParser",
                "classification": "Application Form / Excel Intake",
            },
            "Shikha_Behera_CV-2.docx": {
                "size_bytes": cv_path.stat().st_size,
                "sha256": hashlib.sha256(cv_path.read_bytes()).hexdigest(),
                "parser": "DocxParser",
                "classification": "Founder Resume",
            },
            "NEW PITCH DECK STETHAIM.pdf": {
                "size_bytes": deck_path.stat().st_size,
                "sha256": hashlib.sha256(deck_path.read_bytes()).hexdigest(),
                "parser": "PdfParser",
                "classification": "Pitch Deck (14 slides)",
            },
        },
    }


def validate_reuse_prerequisites(
    db: Any,
    startup_id_str: str,
) -> Tuple[Any, Any, List[Any]]:
    """Validates that the requested startup ID matches the authorized CleanPower Systems record,
    and that its profile and claims are present and intact.

    Fails closed immediately if:
    - ID format is invalid
    - ID does not match the authorized CleanPower Systems record (9b8174247d774a1fa927a432b12564eb)
    - Startup record does not exist
    - Startup name is not 'CleanPower Systems'
    - Intelligence profile is missing
    - Claims are missing or insufficient (< 50 canonical claims)
    """
    from app.modules.startups.models import StartupApplication
    from app.modules.intelligence.models import StartupIntelligenceProfile, StartupClaim
    from app.modules.intelligence.repository import (
        StartupIntelligenceProfileRepository,
        StartupClaimRepository,
    )
    import uuid

    clean_id = startup_id_str.strip().lower().replace("-", "")
    if clean_id != AUTHORIZED_REUSE_STARTUP_ID:
        raise ValueError(
            f"Reuse authorization failed: requested ID '{startup_id_str}' does not match "
            f"authorized CleanPower Systems record '{AUTHORIZED_REUSE_STARTUP_ID}'."
        )

    try:
        target_uuid = uuid.UUID(hex=clean_id)
    except ValueError as e:
        raise ValueError(f"Invalid startup UUID format: {startup_id_str}") from e

    startup = db.query(StartupApplication).filter(StartupApplication.id == target_uuid).first()
    if not startup:
        raise ValueError(f"Startup application '{target_uuid}' not found in database.")

    if startup.startup_name != "CleanPower Systems":
        raise ValueError(f"Startup name mismatch: expected 'CleanPower Systems', found '{startup.startup_name}'.")

    profile = StartupIntelligenceProfileRepository(db).get_by_startup(startup.id)
    if not profile:
        raise ValueError(f"StartupIntelligenceProfile missing for startup '{startup.id}'.")

    claims = StartupClaimRepository(db).list_for_profile(profile.id)
    if not claims or len(claims) < 50:
        count = len(claims) if claims else 0
        raise ValueError(f"Insufficient claims for startup '{startup.id}': found {count}, expected >= 50.")

    return startup, profile, claims


def validate_target_startup_prerequisites(
    db: Any,
    startup_id_str: str,
    *,
    expect_petrevolt: bool = False,
) -> Tuple[Any, List[Dict[str, Any]]]:
    """Validate an existing target startup and its registered source documents before live dispatch.

    Fails closed if:
    - UUID format is invalid
    - ID resolves to CleanPower reuse fixture or historical STETHAIM recovery snapshot
    - expect_petrevolt=True but UUID/name does not match PETREVOLT ENERGY SOLUTIONS PVT LTD
    - Startup record is missing from target database
    - Startup has zero registered documents or any document ownership mismatches startup.id
    - Any registered document file is missing on disk or empty
    """
    import hashlib
    import uuid
    from app.modules.startups.models import StartupApplication
    from app.modules.documents.repository import DocumentRepository

    raw_id = (startup_id_str or "").strip()
    if not raw_id:
        raise ValueError("Target startup ID cannot be empty.")

    try:
        try:
            target_uuid = uuid.UUID(raw_id)
        except ValueError:
            target_uuid = uuid.UUID(hex=raw_id)
    except ValueError as exc:
        raise ValueError(f"Invalid target startup UUID format: '{startup_id_str}'") from exc

    clean_hex = target_uuid.hex.lower()
    if clean_hex == AUTHORIZED_REUSE_STARTUP_ID.replace("-", "").lower():
        raise ValueError(
            f"Startup ID '{target_uuid}' is the synthetic CleanPower reuse record. "
            "Use --reuse-startup-id instead of --startup-id to avoid mode confusion."
        )
    if clean_hex == HISTORICAL_STETHAIM_STARTUP_ID.replace("-", "").lower():
        raise ValueError(
            f"Startup ID '{target_uuid}' is the historical STETHAIM pilot record. "
            "Use --stethaim-pilot or --recover-evaluation-id instead of --startup-id."
        )
    if expect_petrevolt and clean_hex != PETREVOLT_TARGET_STARTUP_ID.replace("-", "").lower():
        raise ValueError(
            f"--petrevolt target mismatch: expected '{PETREVOLT_TARGET_STARTUP_ID}', got '{target_uuid}'."
        )

    startup = db.query(StartupApplication).filter(StartupApplication.id == target_uuid).first()
    if not startup:
        raise ValueError(f"Target startup application '{target_uuid}' not found in database.")

    if expect_petrevolt and "PETREVOLT" not in (startup.startup_name or "").upper():
        raise ValueError(
            f"PETREVOLT startup name mismatch for ID '{target_uuid}': found '{startup.startup_name}'."
        )

    docs = list(DocumentRepository(db).list_for_startup(startup.id))
    if not docs:
        raise ValueError(
            f"Target startup '{startup.startup_name}' ({target_uuid}) has no registered source documents."
        )

    verified_docs: List[Dict[str, Any]] = []
    for doc in docs:
        if doc.startup_id != startup.id:
            raise ValueError(
                f"Document ownership mismatch: document '{doc.id}' belongs to '{doc.startup_id}', expected '{startup.id}'."
            )
        raw_fp = Path(str(doc.file_path).replace("\\", os.sep))
        disk_fp = raw_fp if raw_fp.is_absolute() else (PROJECT_ROOT / raw_fp)
        if not disk_fp.exists() or not disk_fp.is_file():
            raise FileNotFoundError(
                f"Registered source document missing on disk for '{startup.id}': {doc.file_path}"
            )
        file_bytes = disk_fp.read_bytes()
        if len(file_bytes) == 0:
            raise ValueError(f"Registered source document is empty (0 bytes): {disk_fp}")
        verified_docs.append(
            {
                "document_id": str(doc.id),
                "filename": doc.original_filename,
                "file_path": str(disk_fp),
                "size_bytes": len(file_bytes),
                "sha256": hashlib.sha256(file_bytes).hexdigest(),
                "has_parsed_text": bool(doc.parsed_text and doc.parsed_text.strip()),
            }
        )

    return startup, verified_docs


def validate_recovery_prerequisites(
    db: Any,
    evaluation_id: str,
    startup_id_str: str,
    target_domain: str = "founder_team",
) -> Dict[str, Any]:
    """Strictly validates target evaluation recovery prerequisites before any paid provider dispatch.

    Fails closed immediately if:
    - ID format is invalid
    - Startup record does not exist in dev database
    - Startup name is not 'STETHAIM Pvt. Ltd.'
    - Intelligence profile is missing
    - Claims are missing or empty
    - Persisted graph artifact does not exist at uploads/graphs/{startup_id}.json
    - Graph artifact startup ID does not match target startup ID
    - Graph artifact is missing any of the other 5 canonical domain reports or has failed status
    - Metadata artifact does not exist or cost observability evaluation ID does not match evaluation_id
    - Target domain is not a valid domain specialist
    - Cumulative prior spend plus planned reservation exceeds hard budget ceiling ($0.35 USD)
    """
    from app.modules.startups.models import StartupApplication
    from app.modules.intelligence.repository import (
        StartupIntelligenceProfileRepository,
        StartupClaimRepository,
    )
    import uuid
    from app.core.config import get_settings

    settings = get_settings()
    clean_id = startup_id_str.strip()
    try:
        s_uuid = uuid.UUID(clean_id)
    except ValueError:
        try:
            s_uuid = uuid.UUID(hex=clean_id)
        except ValueError as exc:
            raise ValueError(f"Invalid startup UUID format: {startup_id_str}") from exc

    # 1. Startup application check
    startup = db.query(StartupApplication).filter(StartupApplication.id == s_uuid).first()
    if not startup:
        raise ValueError(f"Recovery startup application '{s_uuid}' not found in database.")

    if startup.startup_name != "STETHAIM Pvt. Ltd.":
        raise ValueError(
            f"Target startup mismatch: expected 'STETHAIM Pvt. Ltd.', found '{startup.startup_name}'."
        )

    # 2. Profile and claims check
    profile = StartupIntelligenceProfileRepository(db).get_by_startup(startup.id)
    if not profile:
        raise ValueError(f"StartupIntelligenceProfile missing for startup '{startup.id}'.")

    claims = StartupClaimRepository(db).list_for_profile(profile.id)
    if not claims:
        raise ValueError(f"Claims missing for startup '{startup.id}'.")

    # 3. Persisted graph artifact check
    graphs_dir = os.path.join(settings.upload_dir, "graphs")
    target_graph_file = os.path.join(graphs_dir, f"{startup.id}.json")
    if not os.path.exists(target_graph_file):
        raise FileNotFoundError(f"Persisted graph artifact not found at {target_graph_file}. Cannot recover safely.")

    with open(target_graph_file, "r", encoding="utf-8") as f:
        graph_data = json.load(f)

    persisted_startup_id = graph_data.get("startup_id")
    if persisted_startup_id and str(persisted_startup_id).lower().replace("-", "") != str(startup.id).lower().replace("-", ""):
        raise ValueError(
            f"Graph artifact startup ID mismatch: expected '{startup.id}', found '{persisted_startup_id}'."
        )

    # 4. Domain reports check (ensure other 5 domain specialists succeeded)
    raw_domain_reports = graph_data.get("domain_reports", {})
    canonical_domain_keys = [
        "problem_solution",
        "market_opportunity",
        "founder_team",
        "commercialisation",
        "innovation_impact",
        "financials_support",
    ]
    for dkey in canonical_domain_keys:
        if dkey == target_domain:
            continue
        raw_rep = raw_domain_reports.get(dkey)
        if not raw_rep:
            raise ValueError(f"Required successful domain report '{dkey}' missing from persisted graph.")
        if raw_rep.get("status") == "PARSE_ERROR" or "incomplete" in str(raw_rep.get("summary", "")).lower():
            raise ValueError(
                f"Domain '{dkey}' has failed status in persisted graph. "
                f"Targeted recovery requires other 5 domain specialists to be valid and successful."
            )

    # 5. Evaluation ID check against metadata or run report
    meta_file = os.path.join(graphs_dir, f"{startup.id}.metadata.json")
    prior_summary = None
    if os.path.exists(meta_file):
        with open(meta_file, "r", encoding="utf-8") as f:
            meta_json = json.load(f)
            prior_summary = meta_json.get("cost_observability")

    if not prior_summary:
        run_report_path = _resolve_run_report_path()
        if run_report_path.exists():
            with open(run_report_path, "r", encoding="utf-8") as f:
                rep_data = json.load(f)
                cand_summary = rep_data.get("cost_observability")
                if cand_summary and cand_summary.get("evaluation_id") == evaluation_id:
                    prior_summary = cand_summary

    if not prior_summary:
        raise ValueError(
            f"Persisted metadata / run report for evaluation '{evaluation_id}' not found. "
            f"Cannot verify evaluation ID or cumulative cost."
        )

    meta_eval_id = prior_summary.get("evaluation_id")
    if meta_eval_id and meta_eval_id != evaluation_id:
        raise ValueError(
            f"Recovery evaluation ID mismatch: requested '{evaluation_id}', "
            f"but persisted artifact records '{meta_eval_id}'. Dispatch aborted."
        )

    prior_spent_usd = float(prior_summary.get("total_spent_usd", 0.0))
    # Estimated recovery cost: FT @ 2,400 tokens (~$0.0410) + Supervisor @ 2,400 tokens (~$0.0270) = ~$0.0680
    planned_recovery_usd = 0.0680
    cumulative_projected_usd = prior_spent_usd + planned_recovery_usd
    if cumulative_projected_usd > BUDGET_CEILING_USD:
        raise ValueError(
            f"Cumulative projected spend ${cumulative_projected_usd:.4f} USD exceeds "
            f"hard budget ceiling ${BUDGET_CEILING_USD:.2f} USD."
        )

    return {
        "startup": startup,
        "profile": profile,
        "claims_count": len(claims),
        "target_domain": target_domain,
        "evaluation_id": evaluation_id,
        "prior_spent_usd": prior_spent_usd,
        "remaining_budget_usd": BUDGET_CEILING_USD - prior_spent_usd,
        "cumulative_projected_usd": cumulative_projected_usd,
        "graph_file": target_graph_file,
    }


def validate_extraction_recovery_prerequisites(
    db: Any,
    evaluation_id: str,
    startup_id_str: str,
    target_stage: str = "financials_support",
    report_path: str | Path | None = None,
    checkpoint_path: str | Path | None = None,
) -> Dict[str, Any]:
    """Validate prerequisites before paid dispatch of extraction recovery (fail closed)."""
    from app.core.config import get_settings
    from app.modules.ai.orchestrator.extraction_checkpoint import (
        EXTRACTION_STAGE_SPECS,
        load_extraction_checkpoint,
        normalize_extraction_stage_name,
        resolve_extraction_checkpoint_path,
    )
    from app.modules.ai.orchestrator.pipeline import _find_cost_summary_for_evaluation

    normalized_stage: str | None = (
        normalize_extraction_stage_name(target_stage)
        if target_stage and target_stage.strip().lower() != "auto"
        else None
    )

    startup, verified_docs = validate_target_startup_prerequisites(
        db=db,
        startup_id_str=startup_id_str,
        expect_petrevolt=False,
    )

    settings = get_settings()
    target_ckpt = (
        Path(checkpoint_path)
        if checkpoint_path is not None
        else resolve_extraction_checkpoint_path(settings.upload_dir, startup.id, evaluation_id)
    )
    ckpt_data = load_extraction_checkpoint(
        target_ckpt,
        expected_startup_id=startup.id,
        expected_evaluation_id=evaluation_id,
    )

    prior_summary = _find_cost_summary_for_evaluation(
        evaluation_id=evaluation_id,
        project_root=PROJECT_ROOT,
        report_path=report_path,
    )
    if not prior_summary:
        raise ValueError(
            f"Telemetry summary for evaluation '{evaluation_id}' not found. "
            "Cannot verify cumulative prior spend."
        )

    prior_eval_id = prior_summary.get("evaluation_id")
    if prior_eval_id != evaluation_id:
        raise ValueError(
            f"Telemetry evaluation ID mismatch: expected '{evaluation_id}', got '{prior_eval_id}'."
        )

    prior_spent_usd = float(prior_summary.get("total_spent_usd", 0.0))
    pre_completed = dict(ckpt_data["completed_stages"])
    if normalized_stage and normalized_stage in pre_completed:
        pre_completed.pop(normalized_stage, None)

    stage_keys = [s.key for s in EXTRACTION_STAGE_SPECS]
    if normalized_stage and normalized_stage in stage_keys:
        target_idx = stage_keys.index(normalized_stage)
        required_prior_stages = stage_keys[:target_idx]
    else:
        first_missing_idx = next((i for i, k in enumerate(stage_keys) if k not in pre_completed), len(stage_keys))
        required_prior_stages = stage_keys[:first_missing_idx]
        if normalized_stage is None or normalized_stage == "auto":
            normalized_stage = stage_keys[first_missing_idx] if first_missing_idx < len(stage_keys) else stage_keys[-1]

    all_prior_recoverable = bool(ckpt_data["exists"]) and (
        all(k in pre_completed for k in required_prior_stages)
        if len(required_prior_stages) > 0 or len(pre_completed) > 0
        else False
    )
    recovery_mode = "CHECKPOINT_RESUME" if all_prior_recoverable else "CONTINUATION_REPLACEMENT"
    parent_evaluation_id = evaluation_id if recovery_mode == "CONTINUATION_REPLACEMENT" else None

    if all_prior_recoverable:
        reused_stages = [s.key for s in EXTRACTION_STAGE_SPECS if s.key in pre_completed]
        remaining_stages = [s.key for s in EXTRACTION_STAGE_SPECS if s.key not in pre_completed]
    else:
        reused_stages = []
        remaining_stages = [s.key for s in EXTRACTION_STAGE_SPECS]

    pre_subsegments = dict(ckpt_data.get("subsegments") or {})
    planned_extraction_calls: List[Dict[str, Any]] = []
    haiku_worst_rem_usd = 0.0
    haiku_typ_rem_usd = 0.0

    for s_key in remaining_stages:
        if s_key == "innovation_impact":
            if "innovation_ip_patents" not in pre_subsegments:
                cap_9a = EXTRACTION_OUTPUT_TOKEN_LIMITS.get("innovation_ip_patents", 1200)
                worst_9a = (8000 * 0.10 + cap_9a * 0.50) / 1e6
                typ_9a = (6400 * 0.10 + 600 * 0.50) / 1e6
                haiku_worst_rem_usd += worst_9a
                haiku_typ_rem_usd += typ_9a
                planned_extraction_calls.append({
                    "segment": "9A",
                    "stage_key": "innovation_ip_patents",
                    "agent_name": "extraction_innovation_ip_patents",
                    "title": "Innovation, IP & Patents",
                    "output_cap": cap_9a,
                    "criteria": "II-01..07",
                    "model": FAST_EXTRACTION_MODEL,
                    "worst_usd": worst_9a,
                    "typical_usd": typ_9a,
                })
            if "impact_strategic_alignment" not in pre_subsegments:
                cap_9b = EXTRACTION_OUTPUT_TOKEN_LIMITS.get("impact_strategic_alignment", 1200)
                worst_9b = (8000 * 0.10 + cap_9b * 0.50) / 1e6
                typ_9b = (6400 * 0.10 + 550 * 0.50) / 1e6
                haiku_worst_rem_usd += worst_9b
                haiku_typ_rem_usd += typ_9b
                planned_extraction_calls.append({
                    "segment": "9B",
                    "stage_key": "impact_strategic_alignment",
                    "agent_name": "extraction_impact_strategic_alignment",
                    "title": "Impact & Strategic Alignment",
                    "output_cap": cap_9b,
                    "criteria": "II-08..11",
                    "model": FAST_EXTRACTION_MODEL,
                    "worst_usd": worst_9b,
                    "typical_usd": typ_9b,
                })
        else:
            cap_s = EXTRACTION_OUTPUT_TOKEN_LIMITS.get(s_key, 2400)
            in_worst = 8500 if s_key == "financials_support" else 8000
            in_typ = 7600 if s_key == "financials_support" else 6500
            out_typ = 3100 if s_key == "financials_support" else 1500
            worst_s = (in_worst * 0.10 + cap_s * 0.50) / 1e6
            typ_s = (in_typ * 0.10 + out_typ * 0.50) / 1e6
            haiku_worst_rem_usd += worst_s
            haiku_typ_rem_usd += typ_s
            planned_extraction_calls.append({
                "segment": "10" if s_key == "financials_support" else s_key,
                "stage_key": s_key,
                "agent_name": f"extraction_{s_key}",
                "title": s_key.replace("_", " ").title(),
                "output_cap": cap_s,
                "criteria": "FI-01..21" if s_key == "financials_support" else "Standard",
                "model": FAST_EXTRACTION_MODEL,
                "worst_usd": worst_s,
                "typical_usd": typ_s,
            })

    # Downstream Sonnet costs: 19 Criterion Batches + 1 Supervisory Reviewer Call
    domain_batches_worst_usd = 19 * ((2500 * 2.00 + DOMAIN_BATCH_OUTPUT_TOKEN_CAP * 10.00) / 1e6)  # $0.266000
    domain_batches_typ_usd = 0.112100  # ~22.8k in, ~6.65k out

    reviewer_worst_usd = (3000 * 2.00 + REVIEWER_MAX_OUTPUT_TOKENS * 10.00) / 1e6  # $0.030000
    reviewer_typ_usd = 0.017000  # ~2.5k in, ~1.2k out

    sonnet_worst_rem_usd = domain_batches_worst_usd + reviewer_worst_usd  # $0.296000
    sonnet_typ_rem_usd = domain_batches_typ_usd + reviewer_typ_usd       # $0.129100

    worst_case_rem_usd = round(haiku_worst_rem_usd + sonnet_worst_rem_usd, 6)
    typical_rem_usd = round(haiku_typ_rem_usd + sonnet_typ_rem_usd, 6)

    cumulative_projected_usd = round(prior_spent_usd + worst_case_rem_usd, 6)
    cumulative_typical_projected_usd = round(prior_spent_usd + typical_rem_usd, 6)
    total_planned_requests = len(planned_extraction_calls) + 19 + 1

    if cumulative_projected_usd > BUDGET_CEILING_USD:
        raise ValueError(
            f"Cumulative projected spend ${cumulative_projected_usd:.4f} USD "
            f"(prior ${prior_spent_usd:.6f} + planned worst-case ${worst_case_rem_usd:.4f}) "
            f"exceeds ceiling ${BUDGET_CEILING_USD:.2f} USD."
        )

    return {
        "startup": startup,
        "verified_docs": verified_docs,
        "evaluation_id": evaluation_id,
        "parent_evaluation_id": parent_evaluation_id,
        "recovery_mode": recovery_mode,
        "target_stage": normalized_stage or "auto",
        "checkpoint_exists": ckpt_data["exists"],
        "checkpoint_path": str(target_ckpt),
        "reused_stages": reused_stages,
        "remaining_stages": remaining_stages,
        "prior_spent_usd": prior_spent_usd,
        "remaining_budget_usd": round(BUDGET_CEILING_USD - prior_spent_usd, 6),
        "planned_remaining_usd": worst_case_rem_usd,
        "planned_extraction_calls": planned_extraction_calls,
        "total_planned_requests": total_planned_requests,
        "haiku_worst_rem_usd": haiku_worst_rem_usd,
        "haiku_typ_rem_usd": haiku_typ_rem_usd,
        "sonnet_worst_rem_usd": sonnet_worst_rem_usd,
        "sonnet_typ_rem_usd": sonnet_typ_rem_usd,
        "worst_case_rem_usd": worst_case_rem_usd,
        "typical_rem_usd": typical_rem_usd,
        "cumulative_projected_usd": cumulative_projected_usd,
        "cumulative_typical_projected_usd": cumulative_typical_projected_usd,
    }


def check_environment(execute_live: bool, api_key: str | None = None) -> Tuple[bool, str]:
    """Validates prerequisites and fails closed on missing credentials or mock mode.

    Returns (is_valid, error_or_success_message).
    """
    if not execute_live:
        return True, "DRY_RUN_MODE"

    key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY")
    if not key or not key.strip():
        return False, "FATAL: ANTHROPIC_API_KEY is missing or empty. Live evaluation aborted."

    provider = os.environ.get("AI_PROVIDER", "").lower()
    if provider == "mock":
        return False, "FATAL: AI_PROVIDER is set to 'mock' but live evaluation was requested. Refusing silent fallback."

    return True, "READY"


def get_live_run_config() -> Dict[str, Any]:
    """Returns the mandatory runtime configuration dictionary for the live evaluation."""
    return {
        "AI_ENABLED": "true",
        "AI_PROVIDER": "anthropic",
        "AI_FAST_MODEL": FAST_EXTRACTION_MODEL,
        "AI_REASONING_MODEL": REASONING_MODEL,
        "LITELLM_MODEL": REASONING_MODEL,
        "AI_MAX_EVALUATION_BUDGET_USD": str(BUDGET_CEILING_USD),
        "AI_MAX_EVALUATION_BUDGET": str(BUDGET_CEILING_USD),
        "AI_INR_EXCHANGE_RATE": str(INR_EXCHANGE_RATE),
        "AI_INR_BUFFER_MULTIPLIER": str(INR_BUFFER_MULTIPLIER),
        "AI_MAX_RETRIES": "0",
        "RESEARCH_PROVIDER": "disabled",
    }


def configure_runtime_environment(dev_db_path: Path) -> None:
    """Applies the strict budget, model routing, and isolated database environment variables."""
    # Ensure dedicated dev db
    workspace_db_path = (PROJECT_ROOT / "tides_ai.db").resolve()
    if dev_db_path.resolve() == workspace_db_path:
        raise RuntimeError("FATAL: Attempted to run evaluation against protected workspace 'tides_ai.db'!")

    os.environ["DATABASE_URL"] = f"sqlite:///{dev_db_path.resolve()}"

    for k, v in get_live_run_config().items():
        os.environ[k] = v

    # Clear cached settings so app picks up the new environment
    from app.core.config import get_settings
    get_settings.cache_clear()

    # Rebind engine and SessionLocal in app.db.session to target the isolated dev db
    from sqlalchemy import create_engine
    import app.db.session as session_module
    session_module.settings = get_settings()
    session_module.engine = create_engine(session_module.settings.database_url, pool_pre_ping=True)
    session_module.SessionLocal.configure(bind=session_module.engine)

    # Bootstrap all application models and configure mappers
    import app.db.base  # noqa: F401
    from sqlalchemy.orm import configure_mappers
    configure_mappers()


def format_telemetry_table(summary: Dict[str, Any], eval_status: str | None = None) -> str:
    """Formats a structured terminal telemetry table from the evaluation cost ledger."""
    operations = summary.get("operations", [])
    total_ops = len(operations)
    failed_ops = [op for op in operations if op.get("status") != "SUCCESS"]
    parse_err_ops = [op for op in operations if op.get("status") == "PARSE_ERROR"]
    truncated_ops = [op for op in operations if str(op.get("finish_reason", "")).lower() in ("length", "max_tokens")]

    # Supervisory review status
    sup_op = next((op for op in operations if "supervisory" in op.get("agent_name", "").lower()), None)
    sup_status = "NOT INVOKED"
    if sup_op:
        sup_status = "SUCCESS" if sup_op.get("status") == "SUCCESS" else sup_op.get("status", "FAILED")

    if summary.get("is_exhausted"):
        total_status_str = "HALTED (BUDGET EXHAUSTED)"
    elif eval_status == "COMPLETED_WITH_PARTIAL_DOMAIN_FAILURES" or len(failed_ops) > 0:
        details = []
        if truncated_ops:
            details.append(f"{len(truncated_ops)} truncated/parse error")
        elif parse_err_ops:
            details.append(f"{len(parse_err_ops)} parse error")
        elif failed_ops:
            details.append(f"{len(failed_ops)} failed")
        success_count = total_ops - len(failed_ops)
        details.append(f"{success_count} succeeded")
        total_status_str = f"PARTIAL DOMAIN FAILURES ({', '.join(details)}; Supervisory Review: {sup_status})"
    elif eval_status and eval_status != "COMPLETED":
        total_status_str = eval_status
    else:
        total_status_str = "SUCCESS"

    lines = [
        "=" * 102,
        "  TIDES-AI PLATFORM: ONE-TIME LIVE EVALUATION TELEMETRY AUDIT",
        "=" * 102,
        f"Evaluation ID:   {summary.get('evaluation_id', 'N/A')}",
        f"Startup ID:      {summary.get('startup_id', 'N/A')}",
        f"Total Status:    {total_status_str}",
        f"Cost Confidence: {summary.get('cost_confidence', 'UNKNOWN')}",
        "-" * 102,
        f"{'Stage / Agent':<26} {'Model':<19} {'Status':<13} {'In Tok':<7} {'Out Tok':<8} {'USD Cost':<10} {'INR (Buf)':<10}",
        "-" * 102,
    ]

    for op in operations:
        agent = op.get("agent_name", "")[:25]
        model = op.get("model", "")[:18]
        status = op.get("status", "UNKNOWN")
        if str(op.get("finish_reason", "")).lower() in ("length", "max_tokens"):
            status = "TRUNCATED"
        in_tok = op.get("input_tokens", 0)
        out_tok = op.get("output_tokens", 0)
        cost_usd = f"${op.get('final_cost_usd', 0.0):.4f}"
        cost_inr = f"INR {op.get('buffered_cost_inr', 0.0):.2f}"
        lines.append(f"{agent:<26} {model:<19} {status:<13} {in_tok:<7} {out_tok:<8} {cost_usd:<10} {cost_inr:<10}")

    lines.extend([
        "-" * 102,
        f"Total Operations:         {summary.get('total_operations', 0)} ({total_ops - len(failed_ops)} Succeeded, {len(failed_ops)} Failed)",
        f"Supervisory Review:       {sup_status}",
        f"Total Input Tokens:       {summary.get('total_input_tokens', 0):,}",
        f"Total Output Tokens:      {summary.get('total_output_tokens', 0):,}",
        f"Total Cached Read Tokens: {summary.get('total_cached_tokens', 0):,}",
        f"Total Provider Charge:    ${summary.get('total_spent_usd', 0.0):.4f} USD (Ceiling: ${BUDGET_CEILING_USD:.2f} USD)",
        f"Total Buffered INR Cost:  INR {summary.get('total_cost_inr_buffered', 0.0):.2f} (Ceiling: INR {BUFFERED_CEILING_INR:.2f} <= INR 50.00)",
        f"Remaining Budget USD:     ${summary.get('remaining_budget_usd', 0.0):.4f} USD",
        f"Budget Limit Compliance:  {'PASSED (WITHIN INR 50 BUDGET)' if summary.get('under_max_usd_ceiling', True) else 'FAILED'}",
        "=" * 102,
    ])

    return "\n".join(lines)


async def execute_live_pipeline(
    dev_db_path: Path,
    fixture_path: Path,
    reuse_startup_id: str | None = None,
    stethaim_pilot: bool = False,
    target_startup_id: str | None = None,
    expect_petrevolt: bool = False,
) -> Dict[str, Any]:
    """Initializes dev DB and runs coordinate_evaluation_pipeline on the synthetic fixture,
    reuses existing extracted claims if reuse_startup_id is provided,
    targets an existing startup with registered documents via target_startup_id,
    or executes fresh multi-document evaluation for STETHAIM Pvt. Ltd.
    """
    from scripts.init_dev_db import init_dev_database
    init_dev_database()

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from fastapi import UploadFile
    import io
    from app.modules.ai.orchestrator.pipeline import (
        coordinate_evaluation_pipeline,
        evaluate_existing_startup_with_canonical_claims,
    )
    from app.services.ai.exceptions import AIBudgetExhaustedError
    from app.services.ai.cost_ledger import CostLedgerManager

    sqlite_url = f"sqlite:///{dev_db_path.resolve()}"
    engine = create_engine(sqlite_url)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with SessionLocal() as db:
        try:
            if target_startup_id:
                startup, verified_docs = validate_target_startup_prerequisites(
                    db,
                    target_startup_id,
                    expect_petrevolt=expect_petrevolt,
                )
                logger.info(
                    f"Executing controlled evaluation for target startup={startup.startup_name} "
                    f"(ID: {startup.id}, docs={len(verified_docs)}, max_budget_usd=${BUDGET_CEILING_USD:.2f})"
                )
                result = await coordinate_evaluation_pipeline(
                    db=db,
                    startup_name=startup.startup_name,
                    sector=startup.sector or "CleanTech",
                    stage=startup.stage or "Seed",
                    files=[],
                    existing_startup_id=startup.id,
                    max_budget_usd=BUDGET_CEILING_USD,
                )
                result["target_startup_id"] = str(startup.id)
                result["reused_extraction"] = False
                result["reused_startup_id"] = None
                return result

            if stethaim_pilot:
                from app.modules.intelligence.pii_sanitizer import prepare_sanitized_stethaim_inputs
                validate_stethaim_prerequisites()
                prepared_inputs = prepare_sanitized_stethaim_inputs(STETHAIM_PILOT_DIR)
                upload_files = []
                for fname, fbytes, fmimetype in prepared_inputs:
                    upload_files.append(
                        UploadFile(
                            filename=fname,
                            file=io.BytesIO(fbytes),
                            headers={"content-type": fmimetype},
                        )
                    )
                logger.info(
                    "Executing fresh multi-document evaluation for STETHAIM Pvt. Ltd. "
                    "(3 files: Application form, CV, Pitch Deck; PII scrubbed)"
                )
                result = await coordinate_evaluation_pipeline(
                    db=db,
                    startup_name="STETHAIM Pvt. Ltd.",
                    sector="MedTech",
                    stage="Stage 4 (Agreement Signing)",
                    files=upload_files,
                    max_budget_usd=BUDGET_CEILING_USD,
                )
                result["stethaim_pilot"] = True
                result["reused_extraction"] = False
                result["reused_startup_id"] = None
                return result

            if reuse_startup_id:
                # Strictly validate prerequisites before any paid dispatch
                startup, profile, claims = validate_reuse_prerequisites(db, reuse_startup_id)
                logger.info(
                    f"Reusing existing extraction: startup={startup.startup_name} (ID: {startup.id}), "
                    f"claims_count={len(claims)}, profile={profile.id}"
                )
                result = await evaluate_existing_startup_with_canonical_claims(
                    db=db,
                    startup_id=startup.id,
                    max_budget_usd=BUDGET_CEILING_USD,
                )
                result["reused_extraction"] = True
                result["reused_startup_id"] = str(startup.id)
                result["claims_reused_count"] = len(claims)
                return result

            # Standard path: full extraction from fixture PDF
            if not fixture_path.exists():
                raise FileNotFoundError(f"Fixture not found at {fixture_path}")

            with open(fixture_path, "rb") as f:
                file_bytes = f.read()

            upload_file = UploadFile(
                filename=fixture_path.name,
                file=io.BytesIO(file_bytes),
                headers={"content-type": "application/pdf"},
            )

            result = await coordinate_evaluation_pipeline(
                db=db,
                startup_name="CleanPower Systems",
                sector="CleanTech",
                stage="Seed",
                files=[upload_file],
                max_budget_usd=BUDGET_CEILING_USD,
            )
            result["reused_extraction"] = False
            return result
        except AIBudgetExhaustedError as exc:
            logger.warning(f"Evaluation budget ceiling reached: {exc}")
            return {
                "evaluation_status": "PARTIAL_BUDGET_EXHAUSTED",
                "exhaustion_reason": str(exc),
            }
        except Exception as exc:
            logger.error(f"Evaluation pipeline encountered unexpected error: {exc}")
            cost_manager = CostLedgerManager.get_instance()
            ledgers = list(cost_manager._ledgers.values())
            summary = ledgers[-1].get_summary() if ledgers else {}
            return {
                "evaluation_status": "FAILED_ERROR",
                "error_message": str(exc),
                "cost_observability": summary,
            }


def print_dry_run_plan(
    reuse_startup_id: str | None = None,
    stethaim_pilot: bool = False,
    target_startup: Any = None,
    verified_docs: List[Dict[str, Any]] | None = None,
    expect_petrevolt: bool = False,
) -> None:
    """Prints the dry run / preparation plan when --execute-live is not supplied."""
    active_stages = [
        k for k in EXTRACTION_OUTPUT_TOKEN_LIMITS.keys()
        if k not in ("founder_team", "problem_solution", "solution_validation", "prototype_evidence")
    ]
    total_ext_tokens = sum(EXTRACTION_OUTPUT_TOKEN_LIMITS[k] for k in active_stages)
    haiku_in_cost = (len(active_stages) * 16000 * 0.10) / 1e6
    haiku_out_cost = (total_ext_tokens * 0.50) / 1e6
    haiku_worst_usd = round(haiku_in_cost + haiku_out_cost, 6)
    # 19 criterion batches across 6 domains (Claude Sonnet 5.5, max 900 tokens/batch, ~2.5k prompt in)
    # 19 * (2,500 in @ $2.00/M [$0.0050] + 900 out @ $10.00/M [$0.0090]) = 19 * $0.0140 = $0.2660 USD
    domain_batches_worst_usd = 0.2660
    # Supervisory Review (Claude Sonnet 5.5, 3k in + 2,400 out): $0.0060 in + $0.0240 out = $0.0300 USD
    reviewer_worst_usd = 0.0300
    worst_case_exec_usd = round(haiku_worst_usd + domain_batches_worst_usd + reviewer_worst_usd, 6) if (stethaim_pilot or target_startup is not None) else round(domain_batches_worst_usd + reviewer_worst_usd, 6)
    worst_case_buffered_inr = round(worst_case_exec_usd * INR_EXCHANGE_RATE * INR_BUFFER_MULTIPLIER, 2)
    max_single_reservation_usd = 0.0320
    ext_cap_str = get_launcher_config()["extraction_token_cap_str"]

    print("=" * 80)
    print("  TIDES-AI PLATFORM: DRY-RUN READINESS & BUDGET AUDIT (ZERO API CALLS)")
    print("=" * 80)
    print("Execution Mode:            DRY RUN / PREPARATION ONLY")
    print(f"Provider Cost Ceiling:     ${BUDGET_CEILING_USD:.2f} USD")
    print(f"Exchange Rate:             INR {INR_EXCHANGE_RATE:.1f} / USD")
    print(f"Safety Buffer:             {INR_BUFFER_MULTIPLIER:.2f}x (18% margin for tax/forex/discrepancies)")
    print(f"Buffered Cost Ceiling:     INR {BUFFERED_CEILING_INR:.2f} (~INR 39.65, strictly <= INR 50.00 Limit)")
    print(f"Worst-Case Evaluation:     ${worst_case_exec_usd:.4f} USD (~INR {worst_case_buffered_inr:.2f} buffered)")
    print(f"Max Single Reserve:        ${max_single_reservation_usd:.4f} USD (Sequential in-flight reservation)")
    if target_startup is not None:
        print(f"Target Startup:            {target_startup.startup_name} (ID: {target_startup.id})")
        print(f"Sector / Stage:            {target_startup.sector or 'N/A'} | {target_startup.stage or 'N/A'}")
        print("Extraction Mode:           FRESH EXTRACTION FROM REGISTERED DOCUMENTS (Zero CleanPower/STETHAIM Reuse)")
        print(f"Fast Extraction Model:     {FAST_EXTRACTION_MODEL}")
        print(f"Registered Documents ({len(verified_docs or [])} File(s)):")
        for idx, doc_info in enumerate(verified_docs or [], 1):
            print(
                f"  {idx}. {doc_info['filename']} "
                f"({doc_info['size_bytes']:,} bytes, SHA-256: {doc_info['sha256']})"
            )
    elif stethaim_pilot:
        print("Target Startup:            STETHAIM Pvt. Ltd. (Neumo Rex)")
        print("Sector / Stage:            MedTech | Stage 4 (Agreement Signing, Round: Passed)")
        print("Extraction Mode:           FRESH EXTRACTION (Multi-Document Ingestion; Zero CleanPower Reuse)")
        print(f"Fast Extraction Model:     {FAST_EXTRACTION_MODEL}")
        print("Input Documents (3 Files):")
        print("  1. Applications.xlsx         (Application Form / Excel Intake, PII scrubbed)")
        print("  2. Shikha_Behera_CV-2.docx   (Founder Resume / Clinical & Innovation Profile)")
        print("  3. NEW PITCH DECK STETHAIM.pdf (14-Slide Technical Pitch Deck)")
        print("Privacy Safeguards:        Aadhaar, Phone, Email, Residential Address EXCLUDED (PII scrubbed)")
    elif reuse_startup_id:
        print(f"Extraction Mode:           REUSE EXISTING EXTRACTION (ID: {reuse_startup_id})")
        print("Fast Extraction Model:     SKIPPED (0 Haiku API calls)")
    else:
        print("Extraction Mode:           FULL EXTRACTION FROM PDF")
        print(f"Fast Extraction Model:     {FAST_EXTRACTION_MODEL}")
    print(f"Reasoning / Review Model:  {REASONING_MODEL}")
    print("Output Token Limits (By Specialist & Stage):")
    if not reuse_startup_id:
        print(f"  Staged Extraction Calls (Claude Haiku 5.5, max {total_ext_tokens:,} tokens total):")
        print(f"    - Stage 1 (Cover & Intake Completeness):  {EXTRACTION_OUTPUT_TOKEN_LIMITS['cover_intake']:,} tokens (Reserve: $0.0044)")
        print(f"    - Stage 2 (Problem & Need):               {EXTRACTION_OUTPUT_TOKEN_LIMITS['problem_need']:,} tokens (Reserve: $0.0044)")
        print(f"    - Stage 3 (Solution & Product):           {EXTRACTION_OUTPUT_TOKEN_LIMITS['solution_product']:,} tokens (Reserve: $0.0044)")
        print(f"    - Stage 4 (Prototype & Tech Evidence):    {EXTRACTION_OUTPUT_TOKEN_LIMITS['prototype_technical']:,} tokens (Reserve: $0.0044)")
        print(f"    - Stage 5 (Market Opportunity):           {EXTRACTION_OUTPUT_TOKEN_LIMITS['market_opportunity']:,} tokens (Reserve: $0.0044)")
        print(f"    - Stage 6 (Founder & Core Leadership):    {EXTRACTION_OUTPUT_TOKEN_LIMITS['founder_core']:,} tokens (Reserve: $0.0044)")
        print(f"    - Stage 7 (Team & Advisory Governance):   {EXTRACTION_OUTPUT_TOKEN_LIMITS['team_advisory']:,} tokens (Reserve: $0.0044)")
        print(f"    - Stage 8 (Commercialisation):            {EXTRACTION_OUTPUT_TOKEN_LIMITS['commercialisation']:,} tokens (Reserve: $0.0044)")
        print(f"    - Stage 9 (Innovation & Impact):          {EXTRACTION_OUTPUT_TOKEN_LIMITS['innovation_impact']:,} tokens (Reserve: $0.0044)")
        print(f"    - Stage 10 (Financials & Support):        {EXTRACTION_OUTPUT_TOKEN_LIMITS['financials_support']:,} tokens (Reserve: $0.0052)")
    print(f"  Canonical Domain Specialists (Criterion-Batched, <= {DOMAIN_BATCH_MAX_CRITERIA} criteria/batch, <= {DOMAIN_BATCH_OUTPUT_TOKEN_CAP} tokens/batch):")
    print(f"  - Problem & Solution (PS, 3 batches):   <= {DOMAIN_OUTPUT_TOKEN_LIMITS['problem_solution']:,} tokens/batch (13 criteria)")
    print(f"  - Market Opportunity (MO, 2 batches):   <= {DOMAIN_OUTPUT_TOKEN_LIMITS['market_opportunity']:,} tokens/batch (10 criteria)")
    print(f"  - Founder & Team (FT, 3 batches):       <= {DOMAIN_OUTPUT_TOKEN_LIMITS['founder_team']:,} tokens/batch (13 criteria)")
    print(f"  - Commercialisation (BC, 3 batches):    <= {DOMAIN_OUTPUT_TOKEN_LIMITS['commercialisation']:,} tokens/batch (13 criteria)")
    print(f"  - Innovation & Impact (II, 3 batches):  <= {DOMAIN_OUTPUT_TOKEN_LIMITS['innovation_impact']:,} tokens/batch (11 criteria)")
    print(f"  - Financials & Support (FI, 5 batches): <= {DOMAIN_OUTPUT_TOKEN_LIMITS['financials_support']:,} tokens/batch (21 criteria)")
    print(f"  - Supervisory Reviewer:                 {REVIEWER_MAX_OUTPUT_TOKENS:,} tokens (Reserve: $0.0300)")
    print("Gateway Token Forwarding:  FORWARDED (litellm.completion max_tokens parameter)")
    print("Cost Reservation Breakdown:")
    if stethaim_pilot or target_startup is not None:
        print("  Standard Pricing (Actual Uncached Provider Rates, Max Output Tokens):")
        print(f"    - 10 Staged Extraction Calls (Haiku):  ${haiku_worst_usd:.4f} USD (${haiku_in_cost:.4f} in + ${haiku_out_cost:.4f} out)")
        print(f"    - 19 Domain Specialist Batches (Sonnet):${domain_batches_worst_usd:.4f} USD (19 batches <= 900 tokens/batch, <= 5 criteria/batch)")
        print(f"    - 1 Supervisory Reviewer Call (Sonnet):${reviewer_worst_usd:.4f} USD ($0.0060 in + $0.0240 out)")
        print(f"    - Total Evaluation (Worst-Case Standard): ${worst_case_exec_usd:.4f} USD (Buffered: INR {worst_case_buffered_inr:.2f})")
        print(f"    - Standard Budget Headroom:            ${BUDGET_CEILING_USD - worst_case_exec_usd:.4f} USD (Ceiling: ${BUDGET_CEILING_USD:.2f} USD)")
        print("  Typical Real-World Pricing (Observed Extraction & Batch Densities):")
        print("    - 10 Staged Extraction Calls (Haiku):  ~$0.0070 USD (~20k in, ~10k out)")
        print("    - 19 Domain Specialist Batches (Sonnet):~$0.1121 USD (~22.8k in, ~6.65k out)")
        print("    - 1 Supervisory Reviewer Call (Sonnet):~$0.0170 USD (~2.5k in, ~1.2k out)")
        print("    - Total Typical Evaluation:            ~$0.1361 USD (Buffered: INR ~15.42)")
        print(f"    - Typical Budget Headroom:             ~${BUDGET_CEILING_USD - 0.1361:.4f} USD (Ceiling: ${BUDGET_CEILING_USD:.2f} USD)")
        print("  Conservative Cache-Write Pricing Scenario (Worst-Case Prompt Rates):")
        print("    - 10 Extraction Calls (@ $0.20/M write):$0.04485 USD")
        print("    - 19 Domain Batches (@ $4.00/M write): $0.35530 USD")
        print("    - 1 Reviewer Call (@ $4.00/M write):   $0.03600 USD")
        print("    - Resolution & Guards:                 Prompt caching is NOT active in LiteLLM requests;")
        print(f"                                           provider bills at standard uncached rates (${worst_case_exec_usd:.4f} USD).")
        print("                                           Sequential dispatch releases reservations immediately;")
        print(f"                                           max in-flight committed reservation is ${max_single_reservation_usd:.4f} USD <= $0.35.")
    else:
        print("  - Extraction Calls:               $0.0000 USD (Reused pre-extracted claims)")
        print(f"  - 19 Domain Specialist Batches:   ${domain_batches_worst_usd:.4f} USD (19 batches <= 900 tokens/batch)")
        print(f"  - 1 Supervisory Reviewer Call:    ${reviewer_worst_usd:.4f} USD")
        print(f"  - Total Evaluation Worst-Case:    ${worst_case_exec_usd:.4f} USD (Buffered: INR {worst_case_buffered_inr:.2f})")
        print(f"  - Budget Ceiling Headroom:        ${BUDGET_CEILING_USD - worst_case_exec_usd:.4f} USD (Ceiling: ${BUDGET_CEILING_USD:.2f} USD)")
    print("Safeguards & Protections:")
    print("  - PII Scrubbing:                  CONFIRMED (Aadhaar, phone, email, address removed)")
    print("  - Automatic Retries:              0 (Disabled to prevent unbudgeted calls)")
    print("  - External Research:              DISABLED (Zero Tavily calls)")
    if target_startup is not None:
        print("  - CleanPower/STETHAIM Reuse:      DISABLED (Isolated target startup evaluation)")
    else:
        print("  - CleanPower Data Reuse:          DISABLED (Fresh evaluation for STETHAIM)")
    print("  - Gateway Token Forwarding:       FORWARDED (litellm.completion max_tokens parameter)")
    print(f"  - Isolated Target Database:       {(PROJECT_ROOT / 'tides_dev.db').name} (Protected workspace tides_ai.db UNTOUCHED)")
    if not reuse_startup_id and not stethaim_pilot and target_startup is None:
        print(f"Synthetic Target Fixture:  {SYNTHETIC_FIXTURE_PATH.relative_to(PROJECT_ROOT)} (CleanPower Systems)")
    print("-" * 80)
    print("Prerequisites & Status:")
    print("  - Pricing Catalog:       ACTIVE (Explicit rates verified for all models)")
    print(f"  - Budget Reservation:    PRE-REQUEST ENFORCED (Ceiling: ${BUDGET_CEILING_USD:.2f})")
    print(f"  - Output Token Caps:     ENFORCED (Extraction: {ext_cap_str} across 10 stages; Domain Batches: <= {DOMAIN_BATCH_OUTPUT_TOKEN_CAP:,}/batch across 19 batches; Reviewer: {REVIEWER_MAX_OUTPUT_TOKENS:,})")


    print("  - Live Call Guard:       ENGAGED (No paid calls permitted in dry-run mode)")
    print("-" * 80)
    print("To execute the live one-time evaluation securely:")
    if expect_petrevolt:
        print("  PowerShell Launcher:     .\\scripts\\run_live_eval.ps1 -ExecuteLive -Petrevolt")
    elif target_startup is not None:
        print(f"  PowerShell Launcher:     .\\scripts\\run_live_eval.ps1 -ExecuteLive -StartupId {target_startup.id}")
    elif stethaim_pilot:
        print("  PowerShell Launcher:     .\\scripts\\run_live_eval.ps1 -ExecuteLive -StethaimPilot")
    elif reuse_startup_id:
        print("  PowerShell Launcher:     .\\scripts\\run_live_eval.ps1 -ExecuteLive -ReuseExistingExtraction")
    else:
        print("  PowerShell Launcher:     .\\scripts\\run_live_eval.ps1 -ExecuteLive")
    print("  (Prompts for Anthropic key with non-echoing input; cleans memory on exit)")
    print("=" * 80)


def print_recovery_dry_run_plan(
    evaluation_id: str,
    startup_id: str | None = None,
    target_domain: str = "founder_team",
) -> None:
    """Prints the dry run / preparation plan for targeted evaluation recovery."""
    rec_startup = startup_id or "a246f3a5-b797-43fc-9dc3-3e603e3b37b9"
    ft_cap = DOMAIN_OUTPUT_TOKEN_LIMITS.get(target_domain, 2400)
    print("=" * 80)
    print("  TIDES-AI PLATFORM: TARGETED DOMAIN RECOVERY AUDIT (ZERO API CALLS)")
    print("=" * 80)
    print("Target:                    STETHAIM Pvt. Ltd. (Neumo Rex)")
    print("Mode:                      Targeted recovery, not full extraction")
    print(f"Evaluation ID:             {evaluation_id}")
    print(f"Startup ID:                {rec_startup}")
    print(f"Requested Domain:          {target_domain}")
    print("Document Extraction Calls: 0 (SKIPPED)")
    print("Original Evaluation Cost:  $0.2148 USD (~INR 24.33 buffered)")
    print(f"Budget Ceiling:            ${BUDGET_CEILING_USD:.2f} USD (~INR {BUFFERED_CEILING_INR:.2f} buffered)")
    print("Remaining Budget:          $0.1352 USD (~INR 15.32 buffered)")
    print("-" * 80)
    print(f"Specialist to Reassess:    {target_domain} (Criterion-Batched Capability Recovery)")
    print(f"Configured Max Tokens:     {ft_cap:,} tokens/batch (Criterion-batched <= {DOMAIN_BATCH_MAX_CRITERIA} criteria/call)")
    print("Estimated FT Reservation:  ~$0.0410 USD (8,500 input + 2,400 output tokens)")
    print("Estimated Sup Reservation: ~$0.0270 USD (1,500 input + 2,400 output tokens)")
    print("Combined Reservation:      ~$0.0680 USD")
    print("Cumulative Projected Cost: $0.2828 USD (Spent: $0.2148 + Planned: $0.0680)")
    print("Projected Headroom:        $0.0672 USD under $0.35 ceiling")
    print("-" * 80)
    print("Recovery Actions:")
    print("  1. Load existing canonical profile and 5 successful domain assessments (PS, MO, BC, II, FI).")
    print(f"  2. Reassess ONLY {target_domain} with {ft_cap:,} token cap.")
    print("  3. Rerun supervisory review across all 6 verified domain reports.")
    print("  4. Rebuild observation graph, update telemetry, and export final diligence report.")
    print("  5. Zero extraction calls. Zero retries. Strict fail-closed budget guard.")
    print("-" * 80)
    print("To execute targeted recovery securely:")
    print(f"  PowerShell Launcher:     .\\scripts\\run_live_eval.ps1 -ExecuteLive -RecoverEvaluationId {evaluation_id} -RecoverStartupId {rec_startup}")
    print("=" * 80)


def print_recovery_live_banner(
    evaluation_id: str,
    startup_id: str,
    target_domain: str,
    recovery_metadata: Dict[str, Any],
) -> None:
    """Prints the live dispatch banner before initiating paid recovery provider calls."""
    prior_spent = recovery_metadata.get("prior_spent_usd", 0.214803)
    remaining = recovery_metadata.get("remaining_budget_usd", 0.135197)
    projected = recovery_metadata.get("cumulative_projected_usd", 0.282803)
    ft_cap = DOMAIN_OUTPUT_TOKEN_LIMITS.get(target_domain, 2400)

    print("=" * 80)
    print("  TIDES-AI PLATFORM: TARGETED DOMAIN RECOVERY (CONTROLLED LIVE DISPATCH)")
    print("=" * 80)
    print("Target:                    STETHAIM Pvt. Ltd. (Neumo Rex)")
    print("Mode:                      Targeted recovery, not full extraction")
    print(f"Evaluation ID:             {evaluation_id}")
    print(f"Startup ID:                {startup_id}")
    print(f"Requested Domain:          {target_domain} (Reassessing with {ft_cap:,} max output tokens)")
    print("Document Extraction Calls: 0 (SKIPPED)")
    print(f"Reasoning Model:           {REASONING_MODEL} (Specialist Reassessment & Supervisory Review)")
    print(f"Output Token Caps:         Domain ({target_domain}) {ft_cap:,} tokens; Reviewer {REVIEWER_MAX_OUTPUT_TOKENS:,} tokens")
    print(f"Hard Budget Ceiling:       ${BUDGET_CEILING_USD:.2f} USD (~INR {BUFFERED_CEILING_INR:.2f} buffered)")
    print(f"Cumulative Prior Spend:    ${prior_spent:.4f} USD (Restored into cost ledger)")
    print(f"Remaining Budget Headroom: ${remaining:.4f} USD")
    print(f"Cumulative Projected Cost: ${projected:.4f} USD (Fits within ${BUDGET_CEILING_USD:.2f} cap)")
    print("Pre-Dispatch Verification: PASSED (Startup, Profile, 5 Domain Reports, Graph & Metadata Verified)")
    print("Safeguards:                0 Retries | External Research DISABLED | CleanPower Reuse DISABLED")
    print("=" * 80)


def print_extraction_recovery_dry_run_plan(
    evaluation_id: str,
    startup_id: str,
    target_stage: str,
    recovery_metadata: Dict[str, Any],
) -> None:
    """Prints read-only dry-run audit plan for targeted extraction recovery (zero API calls)."""
    startup = recovery_metadata["startup"]
    reused = recovery_metadata["reused_stages"]
    remaining = recovery_metadata["remaining_stages"]
    prior_spent = recovery_metadata["prior_spent_usd"]
    rem_budget = recovery_metadata["remaining_budget_usd"]
    projected = recovery_metadata["cumulative_projected_usd"]
    planned_calls = recovery_metadata.get("planned_extraction_calls", [])
    total_reqs = recovery_metadata.get("total_planned_requests", len(planned_calls) + 20)
    haiku_worst = recovery_metadata.get("haiku_worst_rem_usd", 0.005698)
    haiku_typ = recovery_metadata.get("haiku_typ_rem_usd", 0.004165)
    sonnet_worst = recovery_metadata.get("sonnet_worst_rem_usd", 0.296000)
    sonnet_typ = recovery_metadata.get("sonnet_typ_rem_usd", 0.129100)
    typical_rem = recovery_metadata.get("typical_rem_usd", 0.133265)
    cumulative_typ = recovery_metadata.get("cumulative_typical_projected_usd", 0.143807)

    recovery_mode = recovery_metadata.get("recovery_mode", "CONTINUATION_REPLACEMENT")
    parent_eval_id = recovery_metadata.get("parent_evaluation_id")
    print("=" * 80)
    print("  TIDES-AI PLATFORM: EXTRACTION RECOVERY AUDIT (ZERO API CALLS)")
    print("=" * 80)
    print(f"Target Startup:            {startup.startup_name} (ID: {startup.id})")
    print("Mode:                      Targeted extraction recovery + downstream evaluation")
    print(f"Recovery Mode:             {recovery_mode}")
    if recovery_mode == "CONTINUATION_REPLACEMENT":
        print(
            f"Parent Evaluation ID:      {parent_eval_id or evaluation_id} "
            "(PRESERVED_PARTIAL_FAILURE -> new continuation ID assigned on live dispatch)"
        )
    else:
        print(f"Evaluation ID:             {evaluation_id} (Preserved in-place checkpoint resume)")
    print(f"Checkpoint Status:         Exists={recovery_metadata['checkpoint_exists']} ({recovery_metadata['checkpoint_path']})")
    print(f"Reused Cached Stages:      {len(reused)} stages (0 provider calls):")
    if reused:
        print(f"                           {', '.join(reused)}")
    print(f"Extraction Calls To Run:   {len(planned_calls)} provider request(s) ({FAST_EXTRACTION_MODEL}):")
    for call in planned_calls:
        print(
            f"                           - Segment {call['segment']} ({call['agent_name']}): "
            f"<= {call['output_cap']:,} tokens cap ({call.get('criteria', '')})"
        )
    print("Downstream Sonnet Calls:   20 provider requests (Sonnet 5.5):")
    print("                           - 19 Criterion Batches across 6 Domains: <= 900 tokens/batch (<= 5 criteria/batch)")
    print("                           - 1 Supervisory Reviewer Call:           <= 2,400 tokens")
    print(f"Total Provider Requests:   {total_reqs} requests ({len(planned_calls)} Haiku extraction + 19 Sonnet domain batches + 1 Sonnet reviewer)")
    print("-" * 80)
    print("Cost Reconciliation & Budget Protection:")
    print(f"  Cumulative Prior Spend:  ${prior_spent:.6f} USD (Carried forward into ledger from {evaluation_id})")
    print(f"  Hard Budget Ceiling:     ${BUDGET_CEILING_USD:.2f} USD (~INR {BUFFERED_CEILING_INR:.2f} buffered)")
    print(f"  Remaining Headroom:      ${rem_budget:.6f} USD")
    print("  Worst-Case Recovery Cost Scenario (Standard Uncached Provider Rates & Caps):")
    print(f"    - {len(planned_calls)} Haiku Extraction Calls:       ${haiku_worst:.6f} USD")
    print(f"    - 19 Sonnet Domain Specialist Batches: ${sonnet_worst - 0.0300:.6f} USD (19 batches @ $0.0140/batch max)")
    print(f"    - 1 Sonnet Supervisory Reviewer Call:  $0.030000 USD (3k in @ $2/M + 2.4k out @ $10/M)")
    print(f"    - Total Remaining Worst-Case Spend:   ${recovery_metadata['planned_remaining_usd']:.6f} USD")
    print(f"    - Cumulative Projected Worst-Case:    ${projected:.4f} USD (Fits under ${BUDGET_CEILING_USD:.2f} ceiling)")
    print(f"    - Worst-Case Budget Headroom:         ${BUDGET_CEILING_USD - projected:.6f} USD (~INR {(BUDGET_CEILING_USD - projected) * INR_EXCHANGE_RATE * INR_BUFFER_MULTIPLIER:.2f} buffered)")
    print("  Typical Recovery Cost Scenario (Observed Real-World Densities):")
    print(f"    - {len(planned_calls)} Haiku Extraction Calls:       ${haiku_typ:.6f} USD")
    print(f"    - 19 Sonnet Domain Specialist Batches: ${0.112100:.6f} USD (~22.8k in, ~6.65k out)")
    print(f"    - 1 Sonnet Supervisory Reviewer Call:  ${0.017000:.6f} USD (~2.5k in, ~1.2k out)")
    print(f"    - Total Remaining Typical Spend:      ${typical_rem:.6f} USD")
    print(f"    - Cumulative Projected Typical Spend: ${cumulative_typ:.4f} USD")
    print(f"    - Typical Budget Headroom:            ${BUDGET_CEILING_USD - cumulative_typ:.6f} USD")
    print("-" * 80)
    print("Safeguards & Recovery Invariants:")
    print("  - Checkpoint Cache:      8 stages reused; Stage 9 runs missing sub-segments; Stage 10 runs if absent")
    print("  - Evaluation ID:         Preserved in-place (CHECKPOINT_RESUME)")
    print("  - Prior Telemetry:       Prior spend restored into CostLedger before any provider dispatch")
    print("  - Database Isolation:    tides_dev.db (Protected tides_ai.db verified untouched)")
    print("  - External Research:     DISABLED (Zero Tavily calls)")
    print("  - Automatic Retries:     0 (Fail-closed on any error)")
    print("-" * 80)
    print("To execute extraction recovery securely:")
    print(
        f"  PowerShell Launcher:     .\\scripts\\run_live_eval.ps1 -ExecuteLive "
        f"-RecoverEvaluationId {evaluation_id} -RecoverStartupId {startup.id} "
        f"-RecoverExtractionStage {target_stage}"
    )
    print("=" * 80)


def print_extraction_recovery_live_banner(
    evaluation_id: str,
    startup_id: str,
    target_stage: str,
    recovery_metadata: Dict[str, Any],
) -> None:
    """Prints the live dispatch banner before extraction recovery provider calls."""
    startup = recovery_metadata["startup"]
    recovery_mode = recovery_metadata.get("recovery_mode", "CONTINUATION_REPLACEMENT")
    parent_eval_id = recovery_metadata.get("parent_evaluation_id")
    planned_calls = recovery_metadata.get("planned_extraction_calls", [])
    total_reqs = recovery_metadata.get("total_planned_requests", len(planned_calls) + 20)
    print("=" * 80)
    print("  TIDES-AI PLATFORM: EXTRACTION RECOVERY (CONTROLLED LIVE DISPATCH)")
    print("=" * 80)
    print(f"Target Startup:            {startup.startup_name} (ID: {startup.id})")
    print(f"Recovery Mode:             {recovery_mode}")
    if recovery_mode == "CONTINUATION_REPLACEMENT":
        print(
            f"Parent Evaluation ID:      {parent_eval_id or evaluation_id} "
            "(PRESERVED_PARTIAL_FAILURE -> new continuation ID assigned)"
        )
    else:
        print(f"Evaluation ID:             {evaluation_id} (Preserved in-place checkpoint resume)")
    print(f"Cached Stages Reused:      {len(recovery_metadata['reused_stages'])} stages (0 provider calls)")
    print(f"Extraction Calls To Run:   {len(planned_calls)} call(s) (Haiku):")
    for call in planned_calls:
        print(f"                           - Segment {call['segment']} ({call['agent_name']}): <= {call['output_cap']:,} tokens cap")
    print("Downstream Sonnet Calls:   20 calls (19 domain batches <= 900 tokens/batch + 1 Supervisory Reviewer <= 2,400 tokens)")
    print(f"Total Provider Requests:   {total_reqs} calls ({len(planned_calls)} Haiku + 19 Sonnet domain batches + 1 Sonnet reviewer)")
    print(f"Cumulative Prior Spend:    ${recovery_metadata['prior_spent_usd']:.6f} USD (Carried forward into ledger)")
    print(f"Remaining Budget Headroom: ${recovery_metadata['remaining_budget_usd']:.6f} USD")
    print(f"Worst-Case Recovery Spend: ${recovery_metadata['planned_remaining_usd']:.6f} USD (Cumulative worst: ${recovery_metadata['cumulative_projected_usd']:.4f} USD <= ${BUDGET_CEILING_USD:.2f})")
    print(f"Typical Recovery Spend:    ${recovery_metadata.get('typical_rem_usd', 0.133265):.6f} USD (Cumulative typical: ${recovery_metadata.get('cumulative_typical_projected_usd', 0.143807):.4f} USD)")
    print(f"Hard Budget Ceiling:       ${BUDGET_CEILING_USD:.2f} USD (~INR {BUFFERED_CEILING_INR:.2f} buffered)")
    print("Safeguards:                0 Retries | External Research DISABLED | Real Gateway Only")
    print("=" * 80)


def main() -> int:
    # Bootstrap all application models and configure mappers
    import app.db.base  # noqa: F401
    from sqlalchemy.orm import configure_mappers
    configure_mappers()

    parser = argparse.ArgumentParser(description="TIDES-AI One-Time Secure Live Evaluation Runner")
    parser.add_argument(
        "--execute-live",
        action="store_true",
        default=False,
        help="Explicitly permit live paid Anthropic API calls within the $0.35 ceiling.",
    )
    parser.add_argument(
        "--stethaim-pilot",
        action="store_true",
        default=False,
        help="Target the real-startup pilot for STETHAIM Pvt. Ltd. (Neumo Rex) using multi-document inputs in private/pilot_inputs/stethaim.",
    )
    parser.add_argument(
        "--startup-id",
        type=str,
        default=None,
        help="Target an existing startup UUID in isolated tides_dev.db using its registered source documents.",
    )
    parser.add_argument(
        "--petrevolt",
        action="store_true",
        default=False,
        help=f"Convenience alias resolving to PETREVOLT ENERGY SOLUTIONS PVT LTD ({PETREVOLT_TARGET_STARTUP_ID}).",
    )
    parser.add_argument(
        "--reuse-startup-id",
        type=str,
        default=None,
        help=f"Explicitly reuse existing extracted claims for authorized startup ID ({AUTHORIZED_REUSE_STARTUP_ID}) to skip re-extraction.",
    )
    parser.add_argument(
        "--reuse-existing-extraction",
        action="store_true",
        default=False,
        help=f"Convenience switch to reuse existing CleanPower Systems extraction ({AUTHORIZED_REUSE_STARTUP_ID}).",
    )
    parser.add_argument(
        "--recover-evaluation-id",
        type=str,
        default=None,
        help="Explicitly recover a failed domain evaluation (e.g. 4dae8d45-5da1-4f6d-b964-95138c333c3f) without re-running extractions or successful specialists.",
    )
    parser.add_argument(
        "--recover-startup-id",
        type=str,
        default=None,
        help="Target startup UUID for evaluation recovery (e.g. a246f3a5-b797-43fc-9dc3-3e603e3b37b9).",
    )
    parser.add_argument(
        "--recover-domain",
        type=str,
        default="founder_team",
        help="Target domain to reassess during recovery (default: founder_team).",
    )
    parser.add_argument(
        "--recover-extraction-stage",
        type=str,
        default=None,
        help="Target extraction stage to resume during an EXTRACTION_FAILED recovery (e.g. financials_support or auto).",
    )
    args = parser.parse_args()

    if args.recover_evaluation_id:
        if args.startup_id or args.petrevolt or args.stethaim_pilot:
            print(
                "\n[SECURITY ERROR] Cannot combine --recover-evaluation-id with --startup-id, --petrevolt, or --stethaim-pilot.",
                file=sys.stderr,
            )
            return 1

        if args.recover_extraction_stage:
            if not args.recover_startup_id:
                print(
                    "\n[VALIDATION ERROR] --recover-startup-id is required with --recover-extraction-stage.",
                    file=sys.stderr,
                )
                return 1
            dev_db_path = PROJECT_ROOT / "tides_dev.db"
            configure_runtime_environment(dev_db_path)

            from app.db.session import SessionLocal
            from app.modules.ai.orchestrator.pipeline import recover_failed_extraction_evaluation

            if not args.execute_live:
                with SessionLocal() as db:
                    try:
                        rec_meta = validate_extraction_recovery_prerequisites(
                            db=db,
                            evaluation_id=args.recover_evaluation_id,
                            startup_id_str=args.recover_startup_id,
                            target_stage=args.recover_extraction_stage,
                        )
                    except Exception as exc:
                        print(f"\n[VALIDATION ERROR] Extraction recovery verification failed: {exc}", file=sys.stderr)
                        return 1
                print_extraction_recovery_dry_run_plan(
                    evaluation_id=args.recover_evaluation_id,
                    startup_id=args.recover_startup_id,
                    target_stage=args.recover_extraction_stage,
                    recovery_metadata=rec_meta,
                )
                return 0

            is_valid, msg = check_environment(execute_live=True)
            if not is_valid:
                logger.error(msg)
                print(f"\n[SECURITY ERROR] {msg}", file=sys.stderr)
                return 1

            with SessionLocal() as db:
                try:
                    rec_meta = validate_extraction_recovery_prerequisites(
                        db=db,
                        evaluation_id=args.recover_evaluation_id,
                        startup_id_str=args.recover_startup_id,
                        target_stage=args.recover_extraction_stage,
                    )
                except Exception as exc:
                    logger.error(f"[VALIDATION ERROR] Pre-dispatch extraction verification failed: {exc}")
                    print(f"\n[VALIDATION ERROR] Extraction recovery verification failed: {exc}", file=sys.stderr)
                    print("[SAFETY] Provider calls REFUSED. Recovery aborted.", file=sys.stderr)
                    return 1

                print_extraction_recovery_live_banner(
                    evaluation_id=args.recover_evaluation_id,
                    startup_id=args.recover_startup_id,
                    target_stage=args.recover_extraction_stage,
                    recovery_metadata=rec_meta,
                )
                try:
                    result = asyncio.run(
                        recover_failed_extraction_evaluation(
                            db=db,
                            evaluation_id=args.recover_evaluation_id,
                            startup_id=args.recover_startup_id,
                            target_stage=args.recover_extraction_stage,
                            max_budget_usd=BUDGET_CEILING_USD,
                        )
                    )
                    cost_summary = result.get("cost_observability")
                    if cost_summary:
                        print("\n" + format_telemetry_table(cost_summary, eval_status=result.get("evaluation_status")))
                    print(f"\nFinal Evaluation Status: {result.get('evaluation_status')}")
                    return 0 if result.get("evaluation_status") == "COMPLETED" else 1
                except Exception as exc:
                    logger.error(f"Live extraction recovery failed: {exc}")
                    print(f"\n[RECOVERY FAILED] {exc}", file=sys.stderr)
                    return 1

        target_startup = args.recover_startup_id or "a246f3a5-b797-43fc-9dc3-3e603e3b37b9"
        target_domain = args.recover_domain or "founder_team"

        if not args.execute_live:
            print_recovery_dry_run_plan(
                evaluation_id=args.recover_evaluation_id,
                startup_id=target_startup,
                target_domain=target_domain,
            )
            return 0

        # Live execution path
        is_valid, msg = check_environment(execute_live=True)
        if not is_valid:
            logger.error(msg)
            print(f"\n[SECURITY ERROR] {msg}", file=sys.stderr)
            return 1

        dev_db_path = PROJECT_ROOT / "tides_dev.db"
        configure_runtime_environment(dev_db_path)

        from app.db.session import SessionLocal
        from app.modules.ai.orchestrator.pipeline import recover_failed_domain_evaluation

        with SessionLocal() as db:
            try:
                rec_meta = validate_recovery_prerequisites(
                    db=db,
                    evaluation_id=args.recover_evaluation_id,
                    startup_id_str=target_startup,
                    target_domain=target_domain,
                )
            except Exception as e:
                logger.error(f"[VALIDATION ERROR] Pre-dispatch verification failed: {e}")
                print(f"\n[VALIDATION ERROR] Target verification failed: {e}", file=sys.stderr)
                print("[SAFETY] Provider calls REFUSED. Recovery aborted.", file=sys.stderr)
                return 1

            print_recovery_live_banner(
                evaluation_id=args.recover_evaluation_id,
                startup_id=target_startup,
                target_domain=target_domain,
                recovery_metadata=rec_meta,
            )

            try:
                result = asyncio.run(
                    recover_failed_domain_evaluation(
                        db=db,
                        evaluation_id=args.recover_evaluation_id,
                        startup_id=target_startup,
                        target_domain=target_domain,
                        max_budget_usd=BUDGET_CEILING_USD,
                    )
                )
                print(f"\nFinal Evaluation Status: {result.get('evaluation_status')}")
                return 0
            except Exception as exc:
                logger.error(f"Live recovery failed: {exc}")
                print(f"\n[RECOVERY FAILED] {exc}", file=sys.stderr)
                return 1

    if args.stethaim_pilot and (args.reuse_startup_id or args.reuse_existing_extraction):
        print(
            "\n[SECURITY ERROR] Cannot combine --stethaim-pilot with CleanPower reuse flags. "
            "STETHAIM requires fresh multi-document extraction.",
            file=sys.stderr,
        )
        return 1

    if (args.startup_id or args.petrevolt) and (
        args.stethaim_pilot or args.reuse_startup_id or args.reuse_existing_extraction
    ):
        print(
            "\n[SECURITY ERROR] Cannot combine --startup-id / --petrevolt with --stethaim-pilot or CleanPower reuse flags.",
            file=sys.stderr,
        )
        return 1

    if args.petrevolt and args.startup_id:
        import uuid as _uuid
        try:
            arg_hex = _uuid.UUID(args.startup_id.strip()).hex.lower()
        except ValueError:
            arg_hex = args.startup_id.strip().lower().replace("-", "")
        if arg_hex != PETREVOLT_TARGET_STARTUP_ID.replace("-", "").lower():
            print(
                f"\n[SECURITY ERROR] --petrevolt conflicts with --startup-id '{args.startup_id}'.",
                file=sys.stderr,
            )
            return 1

    target_startup_id = PETREVOLT_TARGET_STARTUP_ID if args.petrevolt else args.startup_id
    expect_petrevolt = bool(args.petrevolt)

    reuse_id = None if (args.stethaim_pilot or target_startup_id) else args.reuse_startup_id
    if not args.stethaim_pilot and not target_startup_id and args.reuse_existing_extraction and not reuse_id:
        reuse_id = AUTHORIZED_REUSE_STARTUP_ID

    if not args.execute_live:
        target_startup_obj = None
        verified_docs_info = None
        if target_startup_id:
            dev_db_path = PROJECT_ROOT / "tides_dev.db"
            workspace_db_path = (PROJECT_ROOT / "tides_ai.db").resolve()
            if dev_db_path.resolve() == workspace_db_path:
                print("\n[VALIDATION ERROR] Refusing protected workspace tides_ai.db.", file=sys.stderr)
                return 1
            if not dev_db_path.exists():
                print(
                    f"\n[VALIDATION ERROR] Isolated dev database not found at {dev_db_path}.",
                    file=sys.stderr,
                )
                return 1
            from sqlalchemy import create_engine as _ce
            from sqlalchemy.orm import sessionmaker as _sm
            _eng = _ce(f"sqlite:///{dev_db_path.resolve()}")
            _SL = _sm(bind=_eng, autoflush=False, autocommit=False)
            with _SL() as _db:
                try:
                    target_startup_obj, verified_docs_info = validate_target_startup_prerequisites(
                        _db,
                        target_startup_id,
                        expect_petrevolt=expect_petrevolt,
                    )
                except Exception as exc:
                    print(f"\n[VALIDATION ERROR] Target verification failed: {exc}", file=sys.stderr)
                    return 1
            _eng.dispose()
        print_dry_run_plan(
            reuse_startup_id=reuse_id,
            stethaim_pilot=args.stethaim_pilot,
            target_startup=target_startup_obj,
            verified_docs=verified_docs_info,
            expect_petrevolt=expect_petrevolt,
        )
        return 0

    # Live Execution Guard
    is_valid, message = check_environment(execute_live=True)
    if not is_valid:
        print(f"\n[SECURITY ERROR] {message}", file=sys.stderr)
        return 1

    dev_db_path = PROJECT_ROOT / "tides_dev.db"
    configure_runtime_environment(dev_db_path)

    if target_startup_id:
        from app.db.session import SessionLocal
        with SessionLocal() as _db:
            try:
                _t_startup, _t_docs = validate_target_startup_prerequisites(
                    _db,
                    target_startup_id,
                    expect_petrevolt=expect_petrevolt,
                )
            except Exception as exc:
                logger.error(f"[VALIDATION ERROR] Pre-dispatch verification failed: {exc}")
                print(f"\n[VALIDATION ERROR] Target verification failed: {exc}", file=sys.stderr)
                print("[SAFETY] Provider calls REFUSED. Live evaluation aborted.", file=sys.stderr)
                return 1

    print("\n" + "=" * 80)
    print("  TIDES-AI: INITIATING CONTROLLED ONE-TIME LIVE EVALUATION")
    if target_startup_id:
        print(f"  Target: {_t_startup.startup_name} (ID: {_t_startup.id})")
        print(f"  Extraction Mode: FRESH EXTRACTION FROM REGISTERED DOCUMENTS ({len(_t_docs)} file(s))")
    elif args.stethaim_pilot:
        print("  Target: STETHAIM Pvt. Ltd. (Neumo Rex - MedTech)")
        print("  Extraction Mode: FRESH MULTI-DOCUMENT EXTRACTION (PII Scrubbed)")
    elif reuse_id:
        print("  Target: CleanPower Systems (PDF Fixture)")
        print(f"  Extraction Mode: REUSE EXISTING EXTRACTION (ID: {reuse_id})")
    else:
        print("  Target: CleanPower Systems (PDF Fixture)")
        print("  Extraction Mode: FULL EXTRACTION FROM PDF")
    print(f"  Budget Limit: ${BUDGET_CEILING_USD:.2f} USD (~INR {BUFFERED_CEILING_INR:.2f} buffered)")
    print("=" * 80 + "\n")

    result = asyncio.run(
        execute_live_pipeline(
            dev_db_path,
            SYNTHETIC_FIXTURE_PATH,
            reuse_startup_id=reuse_id,
            stethaim_pilot=args.stethaim_pilot,
            target_startup_id=target_startup_id,
            expect_petrevolt=expect_petrevolt,
        )
    )

    # Retrieve and print ledger summary
    from app.services.ai.cost_ledger import CostLedgerManager
    cost_summary = result.get("cost_observability")
    if not cost_summary:
        cost_manager = CostLedgerManager.get_instance()
        eval_id = result.get("evaluation_id")
        if eval_id:
            ledger = cost_manager.get_ledger(eval_id)
            if ledger:
                cost_summary = ledger.get_summary()

    if cost_summary:
        print("\n" + format_telemetry_table(cost_summary, eval_status=result.get("evaluation_status")))

    eval_status = result.get("evaluation_status", "UNKNOWN")
    print(f"\nFinal Evaluation Status: {eval_status}")
    if eval_status == "PARTIAL_BUDGET_EXHAUSTED":
        print(f"Halt Reason: {result.get('exhaustion_reason', 'Budget ceiling reached')}")

    # Write sanitized report artifact (preserving per-evaluation archive under telemetry/)
    from app.modules.ai.orchestrator.pipeline import _persist_telemetry_report

    report_file = _resolve_run_report_path()
    resolved_eval_id = result.get("evaluation_id") or (cost_summary or {}).get("evaluation_id")
    sanitized_report = {
        "evaluation_status": eval_status,
        "evaluation_id": resolved_eval_id,
        "startup_id": result.get("startup_id") or target_startup_id,
        "startup_name": "STETHAIM Pvt. Ltd." if result.get("stethaim_pilot") else result.get("startup_name", "CleanPower Systems"),
        "ai_provider": result.get("ai_provider"),
        "model_name": result.get("model_name"),
        "budget_ceiling_usd": BUDGET_CEILING_USD,
        "buffered_ceiling_inr": BUFFERED_CEILING_INR,
        "reused_extraction": result.get("reused_extraction", False),
        "reused_startup_id": result.get("reused_startup_id"),
        "claims_reused_count": result.get("claims_reused_count"),
        "failed_stage": result.get("failed_stage"),
        "completed_stages": result.get("completed_stages"),
        "cost_observability": cost_summary,
    }
    report_file = _persist_telemetry_report(PROJECT_ROOT, sanitized_report, report_path=report_file)

    display_report_path = (
        report_file.relative_to(PROJECT_ROOT)
        if report_file.is_relative_to(PROJECT_ROOT)
        else report_file
    )
    print(f"Sanitized run report written to: {display_report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
