"""test_domain_recovery.py - Unit & integration tests for targeted specialist recovery.

Verifies:
1. Resuming failed evaluation (ID 4dae8d45-5da1-4f6d-b964-95138c333c3f) without re-running extractions.
2. Loading persisted canonical profile and 5 successful domain specialist assessments from graph artifact.
3. Rerunning only the failed specialist (Founder & Team with 2,400 token cap) and supervisory review.
4. Accounting for cumulative prior spend ($0.214803) under $0.35 ceiling without ledger reset.
5. Fail-closed budget enforcement when cumulative reservation would exceed $0.35.
6. Resolution of prompt template metadata loading for the investment domain.
7. Zero live API calls (strictly offline / deterministic mock only).
"""

import io
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Dict
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.modules.evaluation.domain_schemas import (
    DomainAssessmentReport,
    CompactDomainAssessment,
    CompactCriterionResult,
    VerificationStatus,
)
from app.modules.evaluation.domains import (
    FounderTeamExpert,
    ProblemSolutionExpert,
    FinancialsSupportExpert,
    MarketOpportunityExpert,
)
from app.modules.evaluation.prompts.manager import PromptManager
from app.modules.intelligence.models import (
    StartupIntelligenceProfile,
    StartupClaim,
    StartupEvidence,
)
from app.modules.startups.models import StartupApplication
from app.services.ai.cost_ledger import CostLedgerManager, EvaluationCostLedger
from app.services.ai.exceptions import AIBudgetExhaustedError
from app.services.ai.mock import MockAIGateway
from app.services.ai.pricing import get_pricing_catalog
from scripts.run_one_time_live_eval import (
    DOMAIN_OUTPUT_TOKEN_LIMITS,
    print_recovery_dry_run_plan,
    validate_recovery_prerequisites,
    configure_runtime_environment,
)


@pytest.fixture(autouse=True)
def preserve_env_and_settings():
    """Guarantees test_domain_recovery does not leak environment or database settings to other tests."""
    orig_env = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(orig_env)
    from app.core.config import get_settings
    get_settings.cache_clear()
    from sqlalchemy import create_engine
    import app.db.session as session_module
    session_module.settings = get_settings()
    session_module.engine = create_engine(session_module.settings.database_url, pool_pre_ping=True)
    session_module.SessionLocal.configure(bind=session_module.engine)


@pytest.fixture
def isolated_db():
    """Creates a temporary in-memory SQLite database isolated from workspace."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_prompt_template_metadata_loading_all_domains():
    """Verifies that all prompt template domains, including investment, load valid metadata and templates."""
    domains = ["founder", "product", "market", "investment", "risk"]
    for domain in domains:
        prompt_data = PromptManager.load_prompt(domain=domain, version="latest")
        assert prompt_data is not None, f"Prompt data for {domain} was None"
        assert "system_prompt" in prompt_data, f"system_prompt missing for {domain}"
        assert "user_prompt" in prompt_data, f"user_prompt missing for {domain}"
        assert "prompt_version" in prompt_data, f"prompt_version missing for {domain}"
        assert prompt_data["prompt_version"] == "1.0.0"


def test_founder_team_expert_configures_batched_output_tokens():
    """Verifies FounderTeamExpert and DOMAIN_OUTPUT_TOKEN_LIMITS use bounded 900-token criterion batches."""
    ft_expert = FounderTeamExpert()
    assert ft_expert.max_criteria_per_call == 3  # v1.1 default (AI_DOMAIN_BATCH_MAX_CRITERIA)
    assert ft_expert.batch_max_output_tokens == 900
    assert ft_expert.max_output_tokens == 900, (
        f"FounderTeamExpert.max_output_tokens expected 900, got {ft_expert.max_output_tokens}"
    )
    assert DOMAIN_OUTPUT_TOKEN_LIMITS["founder_team"] == 900
    assert DOMAIN_OUTPUT_TOKEN_LIMITS["problem_solution"] == 900
    assert DOMAIN_OUTPUT_TOKEN_LIMITS["financials_support"] == 900


def test_cost_ledger_restore_from_summary_and_cumulative_headroom():
    """Verifies that EvaluationCostLedger restores exact historical spend ($0.2148) and enforces headroom."""
    mgr = CostLedgerManager.get_instance()
    mgr.clear_all()

    eval_id = "4dae8d45-5da1-4f6d-b964-95138c333c3f"
    startup_id = "a246f3a5-b797-43fc-9dc3-3e603e3b37b9"
    ledger = mgr.get_or_create_ledger(
        evaluation_id=eval_id,
        startup_id=startup_id,
        max_budget_usd=0.35,
        exchange_rate=96.0,
        buffer_multiplier=1.18,
    )

    mock_summary = {
        "evaluation_id": eval_id,
        "startup_id": startup_id,
        "total_operations": 17,
        "total_spent_usd": 0.214803,
        "max_budget_usd": 0.35,
        "remaining_budget_usd": 0.135197,
        "operations": [
            {
                "operation_id": f"op_{i}",
                "agent_name": f"agent_{i}",
                "model": "claude-haiku-5-5" if i < 10 else "claude-sonnet-5-5",
                "input_tokens": 5000,
                "output_tokens": 1000,
                "final_cost_usd": 0.001 if i < 10 else 0.029,
                "status": "SUCCESS" if i != 12 else "PARSE_ERROR",
                "finish_reason": "stop" if i != 12 else "length",
            }
            for i in range(17)
        ],
    }

    ledger.restore_from_summary(mock_summary)

    # 1. Assert restored figures
    assert round(ledger.spent_usd, 4) == 0.2148
    assert round(ledger.remaining_budget_usd, 4) == 0.1352
    assert len(ledger._records) == 17
    assert not ledger.is_exhausted

    # 2. Reserve Founder & Team at 2,400 output tokens (~$0.0410)
    res_ft = ledger.reserve_budget(estimated_cost_usd=0.0410, agent_name="domain_founder_team")
    assert res_ft.startswith("res_")
    assert round(ledger.reserved_usd, 4) == 0.0410
    # Remaining uncommitted should be 0.135197 - 0.0410 = ~0.0942
    assert round(ledger.remaining_budget_usd, 4) == 0.0942

    # Simulate FT completion
    ledger.reconcile_operation(
        reservation_id=res_ft,
        agent_name="domain_founder_team",
        provider="anthropic",
        model="claude-sonnet-5-5",
        input_tokens=8447,
        output_tokens=1950,
        actual_cost_usd=0.036394,
        status="SUCCESS",
        finish_reason="stop",
    )
    assert round(ledger.spent_usd, 4) == round(0.214803 + 0.036394, 4)

    # 3. Reserve Supervisory Review at 2,400 output tokens (~$0.0270)
    res_sup = ledger.reserve_budget(estimated_cost_usd=0.0270, agent_name="supervisory_review")
    assert res_sup.startswith("res_")
    assert round(ledger.reserved_usd, 4) == 0.0270
    assert ledger.spent_usd + ledger.reserved_usd <= 0.35

    # Complete supervisory review
    ledger.reconcile_operation(
        reservation_id=res_sup,
        agent_name="supervisory_review",
        provider="anthropic",
        model="claude-sonnet-5-5",
        input_tokens=1400,
        output_tokens=1300,
        actual_cost_usd=0.015800,
        status="SUCCESS",
        finish_reason="stop",
    )
    # Total spent must fit comfortably under $0.35
    assert ledger.spent_usd <= 0.35
    assert ledger.remaining_budget_usd > 0.05


def test_cumulative_budget_fails_closed_when_cap_exceeded():
    """Verifies that any recovery operation that would breach the $0.35 ceiling is blocked before dispatch."""
    mgr = CostLedgerManager.get_instance()
    mgr.clear_all()

    ledger = mgr.get_or_create_ledger(
        evaluation_id="test_fail_closed_eval",
        max_budget_usd=0.35,
    )
    # Restore prior spend of $0.2148
    ledger.restore_from_summary({"total_spent_usd": 0.2148, "operations": []})
    assert round(ledger.remaining_budget_usd, 4) == 0.1352

    # Attempt an excessive reservation of $0.1500 ($0.2148 + $0.1500 = $0.3648 > $0.35)
    with pytest.raises(AIBudgetExhaustedError) as exc_info:
        ledger.reserve_budget(estimated_cost_usd=0.1500, agent_name="excessive_recovery_call")

    assert "would exceed budget ceiling" in str(exc_info.value)
    assert ledger.is_exhausted is True


def _make_mock_domain_report_dict(domain_key: str) -> dict:
    """Constructs a structurally valid canonical domain assessment dictionary with owned criteria."""
    from app.modules.evaluation.domains.registry import get_criteria_for_domain, CRITERIA_DIRECTORY, CANONICAL_DOMAINS
    cids = get_criteria_for_domain(domain_key)
    crit_evals = {}
    crit_list = []
    for cid in cids:
        meta = CRITERIA_DIRECTORY.get(cid, {})
        crit_evals[cid] = {
            "criterion_id": cid,
            "criterion_name": meta.get("name", cid),
            "assessment_narrative": f"Verified in technical pitch deck for {cid}",
            "verification_status": "VERIFIED_DOCUMENTED",
            "confidence_score": 0.9,
            "strengths": [f"Strength for {cid}"],
            "weaknesses": [],
            "risks": [],
            "evidence_ids": ["EV-01"],
            "source_locations": ["Slide 8"],
        }
        crit_list.append({
            "criterion_id": cid,
            "verification_status": "VERIFIED_DOCUMENTED",
            "score": 8.0,
            "evidence_ids": ["EV-01"],
            "rationale": f"Verified {cid}",
        })
    title = CANONICAL_DOMAINS.get(domain_key, {}).get("title", domain_key.replace("_", " ").title())
    return {
        "domain": domain_key,
        "domain_key": domain_key,
        "domain_title": title,
        "summary": f"Valid completed domain summary for {title}.",
        "executive_summary": f"Valid executive summary for {title}.",
        "criteria_evaluated": list(cids),
        "criteria_evaluations": crit_evals,
        "criteria": crit_list,
        "composite_domain_confidence": 0.9,
        "risks": [],
        "observations": [],
        "questions": [],
        "missing_evidence": [],
    }


@pytest.mark.anyio
async def test_recover_failed_domain_evaluation_pipeline(isolated_db, tmp_path):
    """Integration test verifying targeted recovery of a failed domain without re-running extractions or other 5 domains."""
    from app.modules.ai.orchestrator.pipeline import recover_failed_domain_evaluation

    # 1. Populate test startup, profile, claims, evidence in isolated DB
    s_uuid = uuid.uuid4()
    startup = StartupApplication(
        id=s_uuid,
        startup_name="STETHAIM Pvt. Ltd.",
        sector="MedTech",
        stage="Stage 4",
        solution_summary="Acoustic infant respiratory diagnostic platform",
        target_market="India and APAC",
    )
    isolated_db.add(startup)

    profile = StartupIntelligenceProfile(
        id=uuid.uuid4(),
        startup_id=s_uuid,
        startup=startup,
    )
    isolated_db.add(profile)

    field_uuid = uuid.uuid4()
    claim = StartupClaim(
        id=uuid.uuid4(),
        profile_id=profile.id,
        field_id=field_uuid,
        value_string="Dr. Shikha Behera, MBBS, Founder",
        confidence_score=0.9,
    )
    isolated_db.add(claim)

    evidence = StartupEvidence(
        id=uuid.uuid4(),
        claim_id=claim.id,
        source_document_id=uuid.uuid4(),
        page_number=8,
        section_name="Slide 8",
        evidence_snippet="Dr. Shikha Behera clinical background in neonatal respiratory diagnostics",
    )
    isolated_db.add(evidence)
    isolated_db.commit()

    # 2. Build mock graph JSON with 5 successful domains and 1 failed founder_team domain
    graph_domain_reports = {}
    for d in ["problem_solution", "market_opportunity", "commercialisation", "innovation_impact", "financials_support"]:
        graph_domain_reports[d] = _make_mock_domain_report_dict(d)

    # Failed founder_team placeholder
    graph_domain_reports["founder_team"] = {
        "domain": "founder_team",
        "domain_key": "founder_team",
        "domain_title": "Founder & Team",
        "summary": "Founder & Team evaluation incomplete: AI provider response parsing error",
        "status": "PARSE_ERROR",
        "criteria_evaluated": [],
        "criteria_evaluations": {},
        "risks": [],
        "observations": [],
    }

    mock_graph = {
        "graph_id": str(s_uuid),
        "startup_id": str(s_uuid),
        "startup_name": "STETHAIM Pvt. Ltd.",
        "category": "MedTech",
        "domain_reports": graph_domain_reports,
        "claims": {},
        "evidence": {},
    }

    graph_file = tmp_path / f"{s_uuid}.json"
    with open(graph_file, "w", encoding="utf-8") as f:
        json.dump(mock_graph, f)

    report_file = tmp_path / "live_eval_run_report.json"
    mock_run_report = {
        "evaluation_status": "COMPLETED_WITH_PARTIAL_DOMAIN_FAILURES",
        "cost_observability": {
            "evaluation_id": "eval-recovery-test-01",
            "startup_id": str(s_uuid),
            "total_spent_usd": 0.214803,
            "max_budget_usd": 0.35,
            "operations": [],
        },
    }
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(mock_run_report, f)

    # 3. Execute recovery
    result = await recover_failed_domain_evaluation(
        db=isolated_db,
        evaluation_id="eval-recovery-test-01",
        startup_id=s_uuid,
        target_domain="founder_team",
        max_budget_usd=0.35,
        graph_path=graph_file,
        report_path=report_file,
    )

    assert result["evaluation_status"] == "COMPLETED"
    assert result["startup_id"] == str(s_uuid)
    assert "generated_report" in result

    # 4. Verify updated graph file on disk contains all 6 valid domain reports
    with open(graph_file, "r", encoding="utf-8") as f:
        updated_graph = json.load(f)

    assert "founder_team" in updated_graph["domain_reports"]
    ft_rep = updated_graph["domain_reports"]["founder_team"]
    assert "incomplete" not in str(ft_rep.get("summary", "")).lower()


def _seed_recovery_fixture(isolated_db, work_dir: Path) -> tuple[uuid.UUID, Path]:
    """Create isolated startup/profile/claim/evidence records and mock graph JSON in work_dir."""
    s_uuid = uuid.uuid4()
    startup = StartupApplication(
        id=s_uuid,
        startup_name="STETHAIM Pvt. Ltd.",
        sector="MedTech",
        stage="Stage 4",
        solution_summary="Acoustic infant respiratory diagnostic platform",
        target_market="India and APAC",
    )
    isolated_db.add(startup)
    profile = StartupIntelligenceProfile(id=uuid.uuid4(), startup_id=s_uuid, startup=startup)
    isolated_db.add(profile)
    claim = StartupClaim(
        id=uuid.uuid4(),
        profile_id=profile.id,
        field_id=uuid.uuid4(),
        value_string="Dr. Shikha Behera, MBBS, Founder",
        confidence_score=0.9,
    )
    isolated_db.add(claim)
    isolated_db.add(
        StartupEvidence(
            id=uuid.uuid4(),
            claim_id=claim.id,
            source_document_id=uuid.uuid4(),
            page_number=8,
            section_name="Slide 8",
            evidence_snippet="Dr. Shikha Behera clinical background in neonatal respiratory diagnostics",
        )
    )
    isolated_db.commit()

    graph_domain_reports = {}
    for d in ["problem_solution", "market_opportunity", "commercialisation", "innovation_impact", "financials_support"]:
        graph_domain_reports[d] = _make_mock_domain_report_dict(d)
    graph_domain_reports["founder_team"] = {
        "domain": "founder_team",
        "domain_key": "founder_team",
        "domain_title": "Founder & Team",
        "summary": "Founder & Team evaluation incomplete: AI provider response parsing error",
        "status": "PARSE_ERROR",
        "criteria_evaluated": [],
        "criteria_evaluations": {},
        "risks": [],
        "observations": [],
    }

    graph_file = work_dir / f"{s_uuid}.json"
    graph_file.write_text(
        json.dumps(
            {
                "graph_id": str(s_uuid),
                "startup_id": str(s_uuid),
                "startup_name": "STETHAIM Pvt. Ltd.",
                "category": "MedTech",
                "domain_reports": graph_domain_reports,
                "claims": {},
                "evidence": {},
            }
        ),
        encoding="utf-8",
    )
    return s_uuid, graph_file


@pytest.mark.anyio
async def test_recovery_preserves_workspace_telemetry_sha256(isolated_db, tmp_path, monkeypatch):
    """Regression test: targeted recovery tests route telemetry into temp storage and keep workspace telemetry SHA-256 unchanged."""
    import hashlib
    from app.modules.ai.orchestrator.pipeline import recover_failed_domain_evaluation

    repo_root = Path(__file__).resolve().parent.parent
    workspace_telemetry = repo_root / "reports" / "live_eval_run_report.json"
    pre_sha = hashlib.sha256(workspace_telemetry.read_bytes()).hexdigest() if workspace_telemetry.exists() else None

    s_uuid, graph_file = _seed_recovery_fixture(isolated_db, tmp_path)
    env_report_file = tmp_path / "env_isolated_live_eval_report.json"
    env_report_file.write_text(
        json.dumps(
            {
                "evaluation_status": "COMPLETED_WITH_PARTIAL_DOMAIN_FAILURES",
                "cost_observability": {
                    "evaluation_id": "eval-recovery-sha-test",
                    "startup_id": str(s_uuid),
                    "total_spent_usd": 0.214803,
                    "max_budget_usd": 0.35,
                    "operations": [],
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("TIDES_LIVE_EVAL_REPORT_PATH", str(env_report_file))

    result = await recover_failed_domain_evaluation(
        db=isolated_db,
        evaluation_id="eval-recovery-sha-test",
        startup_id=s_uuid,
        target_domain="founder_team",
        max_budget_usd=0.35,
        graph_path=graph_file,
        report_path=None,
    )
    assert result["evaluation_status"] == "COMPLETED"
    written = json.loads(env_report_file.read_text(encoding="utf-8"))
    assert written["recovery_run"] is True
    assert written["cost_observability"]["evaluation_id"] == "eval-recovery-sha-test"

    post_sha = hashlib.sha256(workspace_telemetry.read_bytes()).hexdigest() if workspace_telemetry.exists() else None
    assert post_sha == pre_sha, (
        f"Workspace telemetry reports/live_eval_run_report.json was mutated! "
        f"Before={pre_sha}, After={post_sha}"
    )


def test_recovery_dry_run_plan_telemetry(capsys):
    """Verifies that print_recovery_dry_run_plan prints the exact required recovery telemetry and budget estimates."""
    print_recovery_dry_run_plan(
        evaluation_id="4dae8d45-5da1-4f6d-b964-95138c333c3f",
        startup_id="a246f3a5-b797-43fc-9dc3-3e603e3b37b9",
        target_domain="founder_team",
    )
    captured = capsys.readouterr().out

    assert "TARGETED DOMAIN RECOVERY AUDIT" in captured
    assert "Targeted recovery, not full extraction" in captured
    assert "Document Extraction Calls: 0 (SKIPPED)" in captured
    assert "4dae8d45-5da1-4f6d-b964-95138c333c3f" in captured
    assert "a246f3a5-b797-43fc-9dc3-3e603e3b37b9" in captured
    assert "$0.2148 USD" in captured
    assert "$0.35 USD" in captured
    assert "$0.1352 USD" in captured
    assert "900 tokens/batch" in captured
    assert "$0.0410 USD" in captured
    assert "$0.0270 USD" in captured
    assert "$0.0680 USD" in captured
    assert "$0.2828 USD" in captured
    assert "$0.0672 USD under $0.35 ceiling" in captured


def test_isolated_process_mapper_initialization_succeeds():
    """Verifies in an isolated clean Python process that recovery mapper compilation succeeds
    without 'InvalidRequestError: expression 'User' failed to locate a name ('User')'.
    """
    code = (
        "import sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, str(Path('.').resolve()))\n"
        "from scripts.run_one_time_live_eval import configure_runtime_environment\n"
        "configure_runtime_environment(Path('tides_dev.db'))\n"
        "from app.db.session import SessionLocal\n"
        "from app.modules.startups.models import StartupApplication\n"
        "db = SessionLocal()\n"
        "s = db.query(StartupApplication).first()\n"
        "assert s is not None\n"
        "print('MAPPER_INIT_SUCCESS')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parent.parent),
    )
    assert result.returncode == 0, f"Mapper initialization failed: {result.stderr}"
    assert "MAPPER_INIT_SUCCESS" in result.stdout
    assert "InvalidRequestError" not in result.stderr


def test_validate_recovery_prerequisites_with_live_artifacts(monkeypatch):
    """Verifies that validate_recovery_prerequisites verifies STETHAIM artifacts on disk cleanly."""
    from app.core.config import get_settings

    monkeypatch.setenv("UPLOAD_DIR", str(Path("uploads").resolve()))
    get_settings.cache_clear()
    configure_runtime_environment(Path("tides_dev.db"))
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        rec_meta = validate_recovery_prerequisites(
            db=db,
            evaluation_id="4dae8d45-5da1-4f6d-b964-95138c333c3f",
            startup_id_str="a246f3a5-b797-43fc-9dc3-3e603e3b37b9",
            target_domain="founder_team",
        )
        assert rec_meta["startup"].startup_name == "STETHAIM Pvt. Ltd."
        assert rec_meta["claims_count"] == 77
        assert rec_meta["prior_spent_usd"] in (0.214803, 0.269917)
        assert round(rec_meta["remaining_budget_usd"], 4) in (0.1352, 0.0801)
        assert rec_meta["cumulative_projected_usd"] <= 0.35
    finally:
        db.close()


def test_validate_recovery_prerequisites_fails_on_id_mismatch(monkeypatch):
    """Verifies that validate_recovery_prerequisites fails closed on mismatched IDs or wrong startup."""
    from app.core.config import get_settings

    monkeypatch.setenv("UPLOAD_DIR", str(Path("uploads").resolve()))
    get_settings.cache_clear()
    configure_runtime_environment(Path("tides_dev.db"))
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        # 1. Unknown / mismatched evaluation ID
        with pytest.raises(ValueError) as exc1:
            validate_recovery_prerequisites(
                db=db,
                evaluation_id="00000000-0000-0000-0000-000000000000",
                startup_id_str="a246f3a5-b797-43fc-9dc3-3e603e3b37b9",
                target_domain="founder_team",
            )
        assert "mismatch" in str(exc1.value).lower() or "not found" in str(exc1.value).lower()

        # 2. CleanPower Systems ID passed for recovery (wrong startup name)
        with pytest.raises(ValueError) as exc2:
            validate_recovery_prerequisites(
                db=db,
                evaluation_id="4dae8d45-5da1-4f6d-b964-95138c333c3f",
                startup_id_str="9b8174247d774a1fa927a432b12564eb",
                target_domain="founder_team",
            )
        assert "mismatch" in str(exc2.value).lower()

        # 3. Nonexistent startup UUID
        with pytest.raises(ValueError) as exc3:
            validate_recovery_prerequisites(
                db=db,
                evaluation_id="4dae8d45-5da1-4f6d-b964-95138c333c3f",
                startup_id_str="ffffffff-ffff-ffff-ffff-ffffffffffff",
                target_domain="founder_team",
            )
        assert "not found" in str(exc3.value).lower()
    finally:
        db.close()


def test_recovery_launcher_banner_metadata_consistency():
    """Verifies that launcher banners in PS1 and Python script consistently display
    STETHAIM targeted recovery metadata and 0 extraction calls.
    """
    ps1_path = Path(__file__).resolve().parent.parent / "scripts" / "run_live_eval.ps1"
    ps1_content = ps1_path.read_text(encoding="utf-8")

    assert "Target: STETHAIM Pvt. Ltd. (Neumo Rex)" in ps1_content
    assert "Mode: Targeted recovery, not full extraction" in ps1_content
    assert "Document Extraction Calls: 0 (SKIPPED)" in ps1_content
    assert "$RecoverEvaluationId" in ps1_content

    py_path = Path(__file__).resolve().parent.parent / "scripts" / "run_one_time_live_eval.py"
    py_content = py_path.read_text(encoding="utf-8")

    assert "Target:                    STETHAIM Pvt. Ltd. (Neumo Rex)" in py_content
    assert "Mode:                      Targeted recovery, not full extraction" in py_content
    assert "Document Extraction Calls: 0 (SKIPPED)" in py_content
