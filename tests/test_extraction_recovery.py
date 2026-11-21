"""Offline regression tests for FinancialsSupportExtraction headroom, staged extraction checkpointing,

and targeted extraction recovery under the cumulative $0.35 budget ceiling.

All tests execute offline with synthetic/mocked provider responses and isolated temp storage.
Protected workspace tides_ai.db and historical telemetry artifacts are never modified.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from litellm.utils import Choices, Message, ModelResponse, Usage
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import PROJECT_ROOT, get_settings
from app.core.enums import DocumentProcessingStatus, DocumentType
from app.db.base import Base
from app.modules.ai.orchestrator.extraction_checkpoint import (
    EXTRACTION_STAGE_SPECS,
    load_extraction_checkpoint,
    resolve_extraction_checkpoint_path,
    save_extraction_checkpoint,
)
from app.modules.ai.orchestrator.pipeline import (
    _persist_telemetry_report,
    coordinate_evaluation_pipeline,
    recover_failed_extraction_evaluation,
)
from app.modules.ai.orchestrator.startup_profile_extraction import (
    ContactInfoEntry,
    EXTRACTION_OUTPUT_TOKEN_LIMITS,
    FinancialsSupportExtraction,
    SixQuarterRoadmap,
)
from app.modules.documents.models import Document
from app.modules.evaluation.domain_schemas import (
    CompactCriterionResult,
    CompactDomainAssessment,
    DomainCriterionBatchOutput,
    SupervisoryReviewOutput,
    VerificationStatus,
)
from app.modules.evaluation.domains.registry import get_criteria_for_domain
from app.modules.startups.models import StartupApplication
from app.services.ai.cost_ledger import CostLedgerManager
from app.services.ai.exceptions import AIBudgetExhaustedError, AIResponseParseError
from app.services.ai.litellm import LiteLLMGateway
from app.services.ai.pricing import get_pricing_catalog
from app.services.ai.schemas import AICompletionMetadata, AICompletionRequest, AICompletionResult
from scripts.run_one_time_live_eval import (
    PETREVOLT_TARGET_STARTUP_ID,
    validate_extraction_recovery_prerequisites,
)


@pytest.fixture
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Isolate database, uploads, checkpoints, and telemetry reports per test."""
    db_file = tmp_path / "isolated_recovery.db"
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    report_file = tmp_path / "live_eval_run_report.json"

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    monkeypatch.setenv("TIDES_LIVE_EVAL_REPORT_PATH", str(report_file))
    monkeypatch.setenv("AI_MAX_EVALUATION_BUDGET_USD", "0.35")
    get_settings.cache_clear()

    engine = create_engine(f"sqlite:///{db_file}", pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with SessionLocal() as db:
        yield db, tmp_path, upload_dir, report_file

    engine.dispose()
    get_settings.cache_clear()


def _seed_petrevolt_style_startup(
    db: Session,
    tmp_path: Path,
    startup_id: uuid.UUID | None = None,
) -> tuple[StartupApplication, Document]:
    startup_uuid = startup_id or uuid.uuid4()
    doc_path = tmp_path / "petrevolt_deck.pdf"
    doc_path.write_bytes(b"%PDF-1.4\n%Mock PETREVOLT pitch deck bytes")

    startup = StartupApplication(
        id=startup_uuid,
        startup_name="PETREVOLT ENERGY SOLUTIONS PVT LTD",
        sector="CleanTech / Energy Storage",
        stage="Prototype / Pre-Seed",
        problem_statement="Waste PET upcycling into solid-state sodium-ion batteries.",
        solution_summary="Single-source PET upcycling into Na-ion cells.",
        business_model="B2B cell and stationary BESS supply.",
        target_market="2W/3W EVs, BESS, Defence",
    )
    db.add(startup)
    db.flush()

    doc = Document(
        id=uuid.uuid4(),
        startup_id=startup.id,
        document_type=DocumentType.PITCH_DECK,
        original_filename="PETREVOLT ENERGY SOLUTIONS- Pitch Deck.pdf",
        stored_filename="petrevolt_deck.pdf",
        file_path=str(doc_path),
        content_type="application/pdf",
        file_size=doc_path.stat().st_size,
        parsed_text=(
            "PETREVOLT ENERGY SOLUTIONS PVT LTD - Solid-state sodium-ion batteries from PET waste. "
            "Phase 2 R&D Q1 PET collection -> carbon precursor; Q2 pyrolysis; Q3 XRD/SEM/BET; "
            "Q4 half-cell test; Q5 NASICON sol-gel; Q6 polymer films. EDII-TN IVP grant received. "
            "Funding required for Phase 2 R&D and pilot plant. Contact: Coimbatore."
        ),
        processing_status=DocumentProcessingStatus.PARSED,
    )
    db.add(doc)
    db.commit()
    return startup, doc


def _build_mock_gateway_for_pipeline(call_log: list[str], fail_financials_once: bool = False):
    """Build deterministic gateway mock handling all 10 extraction schemas, 6 domain schemas, and reviewer."""
    failed_already = False

    def complete_json(
        req: AICompletionRequest | None = None,
        schema_cls: type | None = None,
        *,
        request: AICompletionRequest | None = None,
        response_model: type | None = None,
    ):
        nonlocal failed_already
        actual_req = req or request
        actual_schema = schema_cls or response_model
        assert actual_req is not None and actual_schema is not None
        call_log.append(f"{actual_req.agent_name}:{actual_req.max_output_tokens}")

        if fail_financials_once and not failed_already and actual_req.agent_name == "extraction_financials_support":
            failed_already = True
            raise AIResponseParseError(
                "Model output truncated by provider (finish_reason='length', tokens=2400). Incomplete JSON cannot be parsed."
            )

        schema_name = actual_schema.__name__
        if schema_name == "FinancialsSupportExtraction":
            data = FinancialsSupportExtraction(
                funding_raised="EDII-TN Innovation Voucher Program grant received",
                financial_assumptions=["20-30% cell cost reduction vs LFP"],
                lab_facilities_requirements=["XRD, SEM, Raman, XPS, BET testing"],
                six_quarter_product_roadmap=SixQuarterRoadmap(
                    q1="PET solvolysis carbon batches",
                    q2="Multi-stage pyrolysis 800-1600C",
                    q3="XRD SEM BET characterization",
                    q4="Electrochemical half-cell benchmarking",
                    q5="NASICON ceramic filler synthesis",
                    q6="PET polymer electrolyte membrane",
                ),
                source_attribution="PETREVOLT ENERGY SOLUTIONS- Pitch Deck.pdf",
            )
            in_tok, out_tok, cost = 7511, 950, 0.001226
        elif actual_req.agent_name.startswith("extraction_"):
            data = actual_schema()
            in_tok, out_tok, cost = 5500, 900, 0.001000
        elif schema_name == "DomainCriterionBatchOutput":
            meta = actual_req.metadata or {}
            domain_key = meta.get("domain", "problem_solution")
            batch_index = int(meta.get("batch_index", 0))
            crit_ids = list(meta.get("batch_criterion_ids") or get_criteria_for_domain(domain_key)[:5])
            data = DomainCriterionBatchOutput(
                domain=domain_key,
                batch_index=batch_index,
                criteria=[
                    CompactCriterionResult(
                        criterion_id=cid,
                        verification_status=VerificationStatus.VERIFIED_DOCUMENTED,
                        score=7.0,
                        evidence_ids=[],
                        rationale="Verified against submitted pitch deck.",
                    )
                    for cid in crit_ids
                ],
            )
            in_tok, out_tok, cost = 1200, 350, 0.008000
        elif schema_name == "CompactDomainAssessment":
            domain_key = actual_req.agent_name.replace("domain_", "")
            if domain_key not in ("problem_solution", "market_opportunity", "founder_team", "commercialisation", "innovation_impact", "financials_support"):
                domain_key = (actual_req.metadata or {}).get("domain", "problem_solution")
            crit_ids = get_criteria_for_domain(domain_key)
            data = CompactDomainAssessment(
                domain=domain_key,
                domain_conclusion=f"Evaluated {len(crit_ids)} criteria for {domain_key}.",
                criteria=[
                    CompactCriterionResult(
                        criterion_id=cid,
                        verification_status=VerificationStatus.VERIFIED_DOCUMENTED,
                        score=7.0,
                        evidence_ids=[],
                        rationale="Verified against submitted pitch deck.",
                    )
                    for cid in crit_ids
                ],
                risks=[],
            )
            in_tok, out_tok, cost = 7000, 1400, 0.028000
        elif schema_name == "SupervisoryReviewOutput":
            data = SupervisoryReviewOutput(
                executive_summary="Coherent deep-tech battery evaluation with financial disclosure gaps noted.",
                recommendation_rationale="Strong technical R&D validation; financial projections require primary disclosure.",
                overall_recommendation="CONDITIONAL",
                identified_contradictions=[],
                missing_domains=[],
                priority_diligence_questions=["Provide 3-year audited/projected financial schedule."],
                incubation_conditions=["Submit CapEx breakdown before disbursement."],
                confidence_score=0.88,
            )
            in_tok, out_tok, cost = 1500, 900, 0.012000
        else:
            data = actual_schema()
            in_tok, out_tok, cost = 1000, 200, 0.001000

        # Also reconcile against active ledger when evaluation_id is set (simulating LiteLLMGateway accounting)
        if actual_req.evaluation_id:
            ledger = CostLedgerManager.get_instance().get_ledger(actual_req.evaluation_id)
            if ledger is not None:
                res_id = ledger.reserve_budget(max(cost, 0.002), actual_req.agent_name)
                ledger.reconcile_operation(
                    reservation_id=res_id,
                    agent_name=actual_req.agent_name,
                    provider="anthropic",
                    model="claude-haiku-5-5" if actual_req.agent_name.startswith("extraction_") else "claude-sonnet-5-5",
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    actual_cost_usd=cost,
                    finish_reason="stop",
                )

        return AICompletionResult(
            data=data,
            metadata=AICompletionMetadata(
                provider="anthropic",
                model="claude-haiku-5-5" if actual_req.agent_name.startswith("extraction_") else "claude-sonnet-5-5",
                input_tokens=in_tok,
                output_tokens=out_tok,
                latency_ms=85.0,
                actual_cost_usd=cost,
                finish_reason="stop",
            ),
        )

    gw = MagicMock()
    gw.complete_json.side_effect = complete_json
    return gw


def test_only_financials_support_extraction_limit_expanded_with_compact_equivalent_nulls():
    """Verifies only financials_support expanded to 4,096 and omitted nulls validate identically."""
    for spec in EXTRACTION_STAGE_SPECS:
        if spec.key == "financials_support":
            assert EXTRACTION_OUTPUT_TOKEN_LIMITS[spec.key] == 4096
        else:
            assert EXTRACTION_OUTPUT_TOKEN_LIMITS[spec.key] == 2400

    # Omitted optional null/empty keys validate identically to explicit nulls with <40% token size
    compact_payload = {
        "funding_raised": "EDII-TN IVP grant",
        "lab_facilities_requirements": ["XRD", "SEM", "BET"],
        "six_quarter_product_roadmap": {
            "q1": "PET collection",
            "q2": "Pyrolysis 800-1600C",
            "q3": "XRD SEM Raman XPS BET",
            "q4": "Half-cell benchmark",
            "q5": "NASICON filler synthesis",
            "q6": "PET polymer electrolyte",
        },
        "contact_info": {"address": "Coimbatore, India"},
        "source_attribution": "PETREVOLT Deck Slides 5-12",
    }
    parsed_compact = FinancialsSupportExtraction.model_validate(compact_payload)
    parsed_full = FinancialsSupportExtraction.model_validate(parsed_compact.model_dump())
    assert parsed_compact == parsed_full
    assert parsed_compact.three_year_revenue is None

    minified_compact_json = json.dumps(compact_payload, separators=(",", ":"))
    indented_full_json = parsed_full.model_dump_json(indent=2)
    assert len(minified_compact_json) < len(indented_full_json)
    assert (len(indented_full_json) // 4) < EXTRACTION_OUTPUT_TOKEN_LIMITS["financials_support"]


def test_litellm_rejects_length_truncated_financials_support_json():
    """Truncated finish_reason='length' must always raise AIResponseParseError rather than parsing partial JSON."""
    gw = LiteLLMGateway(api_key="test-key", model="claude-haiku-5-5", max_retries=0)
    truncated_resp = ModelResponse(
        id="resp-trunc-fi",
        choices=[
            Choices(
                finish_reason="length",
                message=Message(content='{"three_year_revenue": {"year_1": null, "year_2": '),
            )
        ],
        created=100,
        model="claude-haiku-5-5",
        usage=Usage(prompt_tokens=7511, completion_tokens=2400, total_tokens=9911),
    )
    req = AICompletionRequest(
        system_prompt="Extract FI",
        user_prompt="Deck text",
        agent_name="extraction_financials_support",
        max_output_tokens=4096,
        estimated_input_tokens=7511,
    )
    with patch("litellm.completion", return_value=truncated_resp):
        with pytest.raises(AIResponseParseError, match="finish_reason='length'"):
            gw.complete_json(req, FinancialsSupportExtraction)


@pytest.mark.anyio
async def test_staged_extraction_checkpoints_9_stages_and_targeted_recovery_completes_within_budget(isolated_env):
    """Simulates PETREVOLT failing Stage 10, saving 9-stage checkpoint, and resuming Stage 10 only."""
    db, tmp_path, upload_dir, report_file = isolated_env
    startup, _ = _seed_petrevolt_style_startup(db, tmp_path)

    calls_phase1: list[str] = []
    gw1 = _build_mock_gateway_for_pipeline(calls_phase1, fail_financials_once=True)

    # Phase 1: fails on Stage 10 after 9 successful stages
    with patch("app.modules.ai.orchestrator.pipeline.create_ai_gateway", return_value=gw1):
        res1 = await coordinate_evaluation_pipeline(
            db=db,
            startup_name=startup.startup_name,
            sector=startup.sector,
            stage=startup.stage,
            files=[],
            existing_startup_id=startup.id,
            max_budget_usd=0.35,
        )

    assert res1["evaluation_status"] == "EXTRACTION_FAILED"
    assert res1["evaluation_id"] is not None
    assert res1["failed_stage"] == "financials_support"
    assert len(res1["completed_stages"]) == 9
    assert len(calls_phase1) == 11  # 8 monolithic + 2 subsegments (9A, 9B) + 1 financials (failed)
    assert calls_phase1[-1] == "extraction_financials_support:4096"

    eval_id = res1["evaluation_id"]
    ckpt_path = Path(res1["checkpoint_path"])
    assert ckpt_path.exists()

    # Persist partial telemetry (simulating live launcher telemetry output)
    _persist_telemetry_report(
        PROJECT_ROOT,
        {
            "evaluation_status": "EXTRACTION_FAILED",
            "evaluation_id": eval_id,
            "startup_id": str(startup.id),
            "startup_name": startup.startup_name,
            "cost_observability": res1["cost_observability"],
        },
        report_path=report_file,
    )
    prior_spent = float(res1["cost_observability"]["total_spent_usd"])
    assert prior_spent > 0.0

    # Reset in-memory ledger cache to simulate fresh recovery process reading from disk
    CostLedgerManager.get_instance()._ledgers.pop(eval_id, None)

    # Validate recovery prerequisites cleanly (zero API calls)
    prereq = validate_extraction_recovery_prerequisites(
        db=db,
        evaluation_id=eval_id,
        startup_id_str=str(startup.id),
        target_stage="financials_support",
        report_path=report_file,
        checkpoint_path=ckpt_path,
    )
    assert len(prereq["reused_stages"]) == 9
    assert prereq["remaining_stages"] == ["financials_support"]
    assert prereq["prior_spent_usd"] == pytest.approx(prior_spent, rel=1e-6)

    # Phase 2: resume ONLY Stage 10 extraction + 6 domain experts + supervisory reviewer
    calls_phase2: list[str] = []
    gw2 = _build_mock_gateway_for_pipeline(calls_phase2, fail_financials_once=False)
    with patch("app.modules.ai.orchestrator.pipeline.create_ai_gateway", return_value=gw2), \
         patch("app.modules.evaluation.expert_agent.create_ai_gateway", return_value=gw2), \
         patch("app.modules.evaluation.supervisory.reviewer.create_ai_gateway", return_value=gw2):
        res2 = await recover_failed_extraction_evaluation(
            db=db,
            evaluation_id=eval_id,
            startup_id=startup.id,
            target_stage="financials_support",
            max_budget_usd=0.35,
            checkpoint_path=ckpt_path,
            report_path=report_file,
        )

    assert res2["evaluation_status"] == "COMPLETED"
    assert res2["evaluation_id"] == eval_id
    assert len(res2["reused_checkpoint_stages"]) == 9

    # Crucial check: ONLY extraction_financials_support (NOT the 9 checkpointed stages) ran in extraction!
    ext_calls = [c for c in calls_phase2 if c.startswith("extraction_")]
    assert ext_calls == ["extraction_financials_support:4096"]
    assert len(calls_phase2) == 32  # 1 extraction + 30 domain batches (3 criteria/batch) + 1 supervisory

    # Cumulative ledger preserves prior spend under $0.35
    total_spent = float(res2["cost_observability"]["total_spent_usd"])
    assert total_spent > prior_spent
    assert total_spent < 0.35

    # Per-evaluation telemetry archive written safely in temp telemetry dir
    eval_archive = report_file.parent / "telemetry" / f"eval_{eval_id}.json"
    assert eval_archive.exists()


@pytest.mark.anyio
async def test_extraction_recovery_fails_closed_on_budget_or_id_mismatch(isolated_env):
    """Rejects recovery before dispatch on cumulative budget exhaustion or ID mismatch."""
    db, tmp_path, _, report_file = isolated_env
    startup, _ = _seed_petrevolt_style_startup(db, tmp_path)
    eval_id = "21d60370-d7cf-43d8-9c14-05b0cd5078a2"

    # 1. Seed near-exhausted telemetry ($0.345 spent -> remaining $0.005 insufficient for 7 Sonnet calls)
    report_file.write_text(
        json.dumps(
            {
                "evaluation_status": "EXTRACTION_FAILED",
                "evaluation_id": eval_id,
                "startup_id": str(startup.id),
                "cost_observability": {
                    "evaluation_id": eval_id,
                    "startup_id": str(startup.id),
                    "total_spent_usd": 0.345,
                    "max_budget_usd": 0.35,
                    "operations": [],
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="exceeds ceiling"):
        validate_extraction_recovery_prerequisites(
            db=db,
            evaluation_id=eval_id,
            startup_id_str=str(startup.id),
            target_stage="financials_support",
            report_path=report_file,
        )

    # 2. Evaluation ID mismatch fails closed
    with pytest.raises(ValueError, match="mismatch|not found"):
        validate_extraction_recovery_prerequisites(
            db=db,
            evaluation_id="00000000-0000-0000-0000-000000000000",
            startup_id_str=str(startup.id),
            target_stage="financials_support",
            report_path=report_file,
        )


def test_cli_extraction_recovery_dry_run_and_missing_key_fail_closed(isolated_env):
    """Verifies CLI dry-run audit succeeds and --execute-live fails closed without ANTHROPIC_API_KEY."""
    db, tmp_path, _, report_file = isolated_env
    _seed_petrevolt_style_startup(db, tmp_path, startup_id=uuid.UUID(PETREVOLT_TARGET_STARTUP_ID))
    telemetry_dir = report_file.parent / "telemetry"
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    preserved = (
        PROJECT_ROOT
        / "reports"
        / "telemetry"
        / "eval_21d60370-d7cf-43d8-9c14-05b0cd5078a2_partial_extraction_failed.json"
    )
    (telemetry_dir / preserved.name).write_text(preserved.read_text(encoding="utf-8"), encoding="utf-8")

    script_path = PROJECT_ROOT / "scripts" / "run_one_time_live_eval.py"
    clean_env = dict(os.environ)
    clean_env.pop("ANTHROPIC_API_KEY", None)
    clean_env["AI_PROVIDER"] = "anthropic"

    dry_proc = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--recover-evaluation-id",
            "21d60370-d7cf-43d8-9c14-05b0cd5078a2",
            "--recover-startup-id",
            PETREVOLT_TARGET_STARTUP_ID,
            "--recover-extraction-stage",
            "financials_support",
        ],
        env=clean_env,
        capture_output=True,
        text=True,
    )
    assert dry_proc.returncode == 0, dry_proc.stderr
    assert "EXTRACTION RECOVERY AUDIT (ZERO API CALLS)" in dry_proc.stdout
    assert "CONTINUATION_REPLACEMENT" in dry_proc.stdout
    assert "PRESERVED_PARTIAL_FAILURE" in dry_proc.stdout
    assert "21d60370-d7cf-43d8-9c14-05b0cd5078a2" in dry_proc.stdout
    assert "0.012323" in dry_proc.stdout

    live_no_key = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--execute-live",
            "--recover-evaluation-id",
            "21d60370-d7cf-43d8-9c14-05b0cd5078a2",
            "--recover-startup-id",
            PETREVOLT_TARGET_STARTUP_ID,
            "--recover-extraction-stage",
            "financials_support",
        ],
        env=clean_env,
        capture_output=True,
        text=True,
    )
    assert live_no_key.returncode == 1
    assert "ANTHROPIC_API_KEY is missing or empty" in live_no_key.stderr


@pytest.mark.anyio
async def test_extraction_recovery_continuation_replacement_carries_forward_spend_with_lineage(isolated_env):
    """
    When 21d60370-d7cf-43d8-9c14-05b0cd5078a2 has telemetry without a checkpoint,
    recovery preserves the partial archive untouched as PRESERVED_PARTIAL_FAILURE,
    creates a distinct linked continuation evaluation_id with parent_evaluation_id,
    carries forward $0.012323 into the cumulative $0.35 budget, and reconstructs
    all missing extraction + 6 domain + 1 supervisory calls.
    """
    import hashlib
    import uuid
    from app.modules.ai.orchestrator.pipeline import recover_failed_extraction_evaluation
    from scripts.run_one_time_live_eval import validate_extraction_recovery_prerequisites

    db, tmp_path, upload_dir, report_file = isolated_env
    startup, _ = _seed_petrevolt_style_startup(db, tmp_path, startup_id=uuid.UUID(PETREVOLT_TARGET_STARTUP_ID))
    parent_eval_id = "21d60370-d7cf-43d8-9c14-05b0cd5078a2"

    preserved_src = (
        PROJECT_ROOT
        / "reports"
        / "telemetry"
        / "eval_21d60370-d7cf-43d8-9c14-05b0cd5078a2_partial_extraction_failed.json"
    )
    preserved_text = preserved_src.read_text(encoding="utf-8")
    report_file.write_text(preserved_text, encoding="utf-8")
    preserved_archive = report_file.parent / "telemetry" / preserved_src.name
    preserved_archive.parent.mkdir(parents=True, exist_ok=True)
    preserved_archive.write_text(preserved_text, encoding="utf-8")
    archive_sha_before = hashlib.sha256(preserved_archive.read_bytes()).hexdigest()

    assert not (upload_dir / "extraction_checkpoints").exists()

    prereq = validate_extraction_recovery_prerequisites(
        db=db,
        evaluation_id=parent_eval_id,
        startup_id_str=PETREVOLT_TARGET_STARTUP_ID,
        target_stage="financials_support",
    )
    assert prereq["recovery_mode"] == "CONTINUATION_REPLACEMENT"
    assert prereq["parent_evaluation_id"] == parent_eval_id
    assert prereq["reused_stages"] == []
    assert len(prereq["remaining_stages"]) == 10
    assert prereq["prior_spent_usd"] == pytest.approx(0.012323, abs=1e-6)
    assert prereq["remaining_budget_usd"] == pytest.approx(0.337677, abs=1e-6)

    call_log: list = []
    gw = _build_mock_gateway_for_pipeline(call_log, fail_financials_once=False)
    with patch("app.modules.ai.orchestrator.pipeline.create_ai_gateway", return_value=gw), \
         patch("app.modules.evaluation.expert_agent.create_ai_gateway", return_value=gw), \
         patch("app.modules.evaluation.supervisory.reviewer.create_ai_gateway", return_value=gw):
        res = await recover_failed_extraction_evaluation(
            db=db,
            evaluation_id=parent_eval_id,
            startup_id=startup.id,
            target_stage="financials_support",
            max_budget_usd=0.35,
            report_path=report_file,
        )

    assert res["evaluation_status"] == "COMPLETED"
    assert res["recovery_mode"] == "CONTINUATION_REPLACEMENT"
    assert res["parent_evaluation_id"] == parent_eval_id
    assert res["parent_evaluation_status"] == "PRESERVED_PARTIAL_FAILURE"
    continuation_eval_id = res["evaluation_id"]
    assert continuation_eval_id != parent_eval_id
    assert res["carried_forward_spend_usd"] == pytest.approx(0.012323, abs=1e-6)
    assert res["reused_checkpoint_stages"] == []
    assert len(call_log) == 42  # 11 extraction (8 monolithic + 2 subsegments + 1 financials) + 30 domain batches + 1 supervisory

    total_spent = float(res["cost_observability"]["total_spent_usd"])
    assert total_spent > 0.012323
    assert total_spent < 0.35
    assert hashlib.sha256(preserved_archive.read_bytes()).hexdigest() == archive_sha_before

    cont_telemetry = report_file.parent / "telemetry" / f"eval_{continuation_eval_id}.json"
    assert cont_telemetry.exists()
    cont_payload = json.loads(cont_telemetry.read_text(encoding="utf-8"))
    assert cont_payload["recovery_mode"] == "CONTINUATION_REPLACEMENT"
    assert cont_payload["parent_evaluation_id"] == parent_eval_id

    cont_ckpt = upload_dir / "extraction_checkpoints" / f"{startup.id}_{continuation_eval_id}.json"
    assert cont_ckpt.exists()
    ckpt_payload = json.loads(cont_ckpt.read_text(encoding="utf-8"))
    assert ckpt_payload["parent_evaluation_id"] == parent_eval_id

    eval_graph = upload_dir / "graphs" / f"{continuation_eval_id}.json"
    assert eval_graph.exists()
    graph_json = json.loads(eval_graph.read_text(encoding="utf-8"))
    assert graph_json["report"]["metadata"]["parent_evaluation_id"] == parent_eval_id
    assert graph_json["report"]["metadata"]["parent_evaluation_status"] == "PRESERVED_PARTIAL_FAILURE"
    assert graph_json["report"]["metadata"]["recovery_mode"] == "CONTINUATION_REPLACEMENT"

    startup_meta = upload_dir / "graphs" / f"{startup.id}.metadata.json"
    eval_meta = upload_dir / "graphs" / f"{continuation_eval_id}.metadata.json"
    assert startup_meta.exists() and eval_meta.exists()
    meta_json = json.loads(eval_meta.read_text(encoding="utf-8"))
    assert meta_json["parent_evaluation_id"] == parent_eval_id
    assert meta_json["parent_evaluation_status"] == "PRESERVED_PARTIAL_FAILURE"
    assert meta_json["recovery_mode"] == "CONTINUATION_REPLACEMENT"

