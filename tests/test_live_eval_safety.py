"""tests/test_live_eval_safety.py - Deterministic Safety & Budget Verification for Live Evaluation.

Zero live API calls.
Tests:
1. Empty or missing Anthropic API key fails closed when live evaluation is requested.
2. Dry-run mode without --execute-live initiates zero API calls and returns status 0.
3. Mock provider cannot silently substitute when live execution is authorized.
4. Pre-request budget reservation rejects operations exceeding the $0.35 USD limit before dispatch.
5. Retries cannot bypass ledger reservation; max_retries=0 eliminates automatic retries.
6. Pipeline gracefully halts on AIBudgetExhaustedError and marks status PARTIAL_BUDGET_EXHAUSTED.
7. Mathematical proof that $0.35 USD @ 96.0 INR/USD and 1.18x buffer is strictly <= INR 39.65.
8. Workspace tides_ai.db SHA-256 hash remains bit-for-bit unchanged.
"""

import hashlib
import io
import os
import subprocess
import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from app.core.config import get_settings
from app.services.ai.cost_ledger import CostLedgerManager, EvaluationCostLedger
from app.services.ai.exceptions import AIBudgetExhaustedError
from app.services.ai.gateway import create_ai_gateway
from app.services.ai.litellm import LiteLLMGateway
from app.services.ai.schemas import AICompletionRequest
from scripts.run_one_time_live_eval import (
    AUTHORIZED_REUSE_STARTUP_ID,
    BUDGET_CEILING_USD,
    BUFFERED_CEILING_INR,
    INR_BUFFER_MULTIPLIER,
    INR_EXCHANGE_RATE,
    SYNTHETIC_FIXTURE_PATH,
    check_environment,
    format_telemetry_table,
    get_live_run_config,
    validate_reuse_prerequisites,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_DB = PROJECT_ROOT / "tides_ai.db"
EXPECTED_WORKSPACE_DB_HASH = "d9659f4e8c1058c5d5f4511e1bb22d3abe6cb12101c16ce397416051a38176c7"


class DummyModel(BaseModel):
    summary: str = "Test response"


class TestLiveEvalSafetyGuards:
    """Deterministic offline safety test suite."""

    def test_empty_or_missing_api_key_fails_closed(self):
        """Verifies check_environment fails closed if ANTHROPIC_API_KEY is empty, None, or whitespace."""
        # Missing key
        valid, msg = check_environment(execute_live=True, api_key=None)
        assert not valid
        assert "missing or empty" in msg.lower()

        # Empty string
        valid, msg = check_environment(execute_live=True, api_key="")
        assert not valid
        assert "missing or empty" in msg.lower()

        # Whitespace
        valid, msg = check_environment(execute_live=True, api_key="   \t\n  ")
        assert not valid
        assert "missing or empty" in msg.lower()

    def test_mock_provider_rejected_when_live_execution_requested(self):
        """Verifies that if live execution is authorized, AI_PROVIDER=mock is refused."""
        with patch.dict(os.environ, {"AI_PROVIDER": "mock"}):
            valid, msg = check_environment(execute_live=True, api_key="sk-ant-test-dummy-key")
            assert not valid
            assert "mock" in msg.lower()
            assert "refusing" in msg.lower()

    def test_dry_run_mode_permits_execution_without_live_calls(self):
        """Verifies that check_environment in dry-run mode returns DRY_RUN_MODE without requiring keys."""
        valid, msg = check_environment(execute_live=False, api_key=None)
        assert valid
        assert msg == "DRY_RUN_MODE"

    def test_mathematical_budget_guarantee_within_inr_50_limit(self):
        """Verifies that the $0.35 USD provider ceiling converted at ₹96/USD with 1.18x buffer is ~₹39.65 (<= ₹50.00)."""
        assert BUDGET_CEILING_USD == 0.35
        assert INR_EXCHANGE_RATE == 96.0
        assert INR_BUFFER_MULTIPLIER == 1.18

        raw_inr = BUDGET_CEILING_USD * INR_EXCHANGE_RATE  # 33.60
        buffered_inr = round(raw_inr * INR_BUFFER_MULTIPLIER, 2)  # 39.65

        assert buffered_inr == BUFFERED_CEILING_INR
        assert buffered_inr == 39.65
        assert buffered_inr <= 50.00, f"Buffered ceiling {buffered_inr} exceeds hard INR 50.00 target!"
        assert (50.00 - buffered_inr) >= 10.00, "Must maintain safety reserve below ₹50.00"

    def test_pre_call_budget_reservation_rejects_exceeding_requests(self):
        """Verifies that pre-request budget reservation rejects requests that exceed $0.35 USD ceiling."""
        eval_id = f"eval_budget_guard_{uuid.uuid4().hex[:8]}"
        ledger = EvaluationCostLedger(
            evaluation_id=eval_id,
            max_budget_usd=0.35,
            exchange_rate=96.0,
            buffer_multiplier=1.18,
        )

        # 1. Operation within budget succeeds
        res_id1 = ledger.reserve_budget(estimated_cost_usd=0.20, agent_name="market_opportunity")
        assert res_id1.startswith("res_")
        assert ledger.reserved_usd == 0.20
        assert ledger.remaining_budget_usd == 0.15

        # 2. Planned operation that would breach $0.35 ceiling is rejected before dispatch
        with pytest.raises(AIBudgetExhaustedError) as exc_info:
            ledger.reserve_budget(estimated_cost_usd=0.20, agent_name="supervisory_review")
        assert "would exceed budget ceiling" in str(exc_info.value)
        assert ledger.is_exhausted

        # 3. Subsequent calls fail immediately
        with pytest.raises(AIBudgetExhaustedError):
            ledger.reserve_budget(estimated_cost_usd=0.01, agent_name="targeted_recheck")

    def test_litellm_gateway_enforces_budget_reservation_prior_to_dispatch(self):
        """Verifies LiteLLMGateway calls reserve_budget and halts before dispatching to remote API if exhausted."""
        eval_id = f"eval_gateway_guard_{uuid.uuid4().hex[:8]}"
        cost_mgr = CostLedgerManager.get_instance()
        ledger = cost_mgr.get_or_create_ledger(
            evaluation_id=eval_id,
            max_budget_usd=0.35,
            exchange_rate=96.0,
            buffer_multiplier=1.18,
        )

        gateway = LiteLLMGateway(
            model="claude-sonnet-5-5",
            api_key="dummy-key-for-test",
            max_retries=0,
        )

        # Pre-exhaust the ledger
        ledger.reserve_budget(estimated_cost_usd=0.33, agent_name="prior_op")

        req = AICompletionRequest(
            system_prompt="Test system prompt",
            user_prompt="Test user prompt",
            evaluation_id=eval_id,
            agent_name="founder_team",
            max_output_tokens=3000,
        )

        with patch("litellm.completion") as mock_completion:
            with pytest.raises(AIBudgetExhaustedError):
                gateway.complete_json(req, DummyModel)

            # Ensure litellm.completion was NEVER called
            mock_completion.assert_not_called()

    def test_retries_require_explicit_budget_reservation(self):
        """Verifies that transient retries cannot bypass ledger budget reservation."""
        eval_id = f"eval_retry_guard_{uuid.uuid4().hex[:8]}"
        cost_mgr = CostLedgerManager.get_instance()
        ledger = cost_mgr.get_or_create_ledger(
            evaluation_id=eval_id,
            max_budget_usd=0.35,
            exchange_rate=96.0,
            buffer_multiplier=1.18,
        )

        # Allow 1 retry in gateway, but leave only enough budget for initial reservation, not retry
        gateway = LiteLLMGateway(
            model="claude-sonnet-5-5",
            api_key="dummy-key-for-test",
            max_retries=1,
        )

        # Consume budget so only 1 call's worth remains
        ledger.reserve_budget(estimated_cost_usd=0.31, agent_name="exhaustion_prep")

        req = AICompletionRequest(
            system_prompt="Short prompt",
            user_prompt="Short user prompt",
            evaluation_id=eval_id,
            agent_name="recheck_agent",
            max_output_tokens=2000,
        )

        # Simulate a transient 500 error on attempt 0 while concurrent work consumes the remaining
        # headroom: the retry must reserve budget before dispatch and therefore fail closed.
        def _fail_and_consume(*args, **kwargs):
            in_flight = round(ledger.reserved_usd - 0.31, 6)  # this call's own reservation
            ledger.reconcile_operation(
                reservation_id=None,
                agent_name="concurrent_consumer",
                provider="test",
                model="claude-sonnet-5-5",
                input_tokens=0,
                output_tokens=0,
                actual_cost_usd=round(ledger.remaining_budget_usd + 0.5 * in_flight, 6),
                confidence="EXACT_REPORTED",
            )
            raise Exception("500 Server Error")

        with patch("litellm.completion", side_effect=_fail_and_consume) as mocked:
            with pytest.raises(AIBudgetExhaustedError):
                gateway.complete_json(req, DummyModel)
        # Exactly one paid dispatch happened; the retry never reached the provider.
        assert mocked.call_count == 1
        # The failed attempt is accounted for explicitly in the ledger (zero tokens, no silent drop).
        statuses = [op["status"] for op in ledger.get_summary()["operations"]]
        assert statuses.count("TRANSIENT_ERROR") == 1

    def test_zero_retries_setting_eliminates_automatic_redispatch(self):
        """Verifies that when AI_MAX_RETRIES is set to 0, max_attempts is exactly 1."""
        gateway = LiteLLMGateway(
            model="claude-sonnet-5-5",
            api_key="dummy-key-for-test",
            max_retries=0,
        )
        assert gateway._max_retries == 0

        calls = []
        def mock_dispatch(*args, **kwargs):
            calls.append(1)
            raise Exception("500 Internal Error")

        req = AICompletionRequest(
            system_prompt="Prompt",
            user_prompt="Prompt",
            agent_name="test_agent",
        )

        with patch("litellm.completion", side_effect=mock_dispatch):
            with pytest.raises(Exception):
                gateway.complete_json(req, DummyModel)

        # Must have been invoked exactly ONCE (zero retries)
        assert len(calls) == 1

    def test_cost_confidence_marked_unverified_when_usage_missing(self):
        """Verifies that if provider does not report token usage, cost confidence is UNVERIFIED_ESTIMATE."""
        eval_id = f"eval_confidence_test_{uuid.uuid4().hex[:8]}"
        ledger = EvaluationCostLedger(
            evaluation_id=eval_id,
            max_budget_usd=0.35,
        )

        # Record with UNVERIFIED_ESTIMATE confidence
        ledger.reconcile_operation(
            reservation_id=None,
            agent_name="Extraction",
            provider="anthropic",
            model="claude-haiku-5-5",
            input_tokens=1000,
            output_tokens=200,
            confidence="UNVERIFIED_ESTIMATE",
        )

        summary = ledger.get_summary()
        assert summary["cost_confidence"] == "UNVERIFIED_ESTIMATE"

    def test_telemetry_table_formatting(self):
        """Verifies that format_telemetry_table outputs a formatted table with budget compliance."""
        sample_summary = {
            "evaluation_id": "eval-telemetry-001",
            "startup_id": "startup-cleanpower-001",
            "is_exhausted": False,
            "cost_confidence": "EXACT_REPORTED",
            "total_operations": 2,
            "total_input_tokens": 12500,
            "total_output_tokens": 3400,
            "total_cached_tokens": 8000,
            "total_spent_usd": 0.0845,
            "total_cost_inr_buffered": 9.56,
            "remaining_budget_usd": 0.3355,
            "under_max_usd_ceiling": True,
            "operations": [
                {
                    "agent_name": "document_extraction",
                    "model": "claude-haiku-5-5",
                    "input_tokens": 4500,
                    "output_tokens": 1200,
                    "cached_tokens": 0,
                    "final_cost_usd": 0.0010,
                    "buffered_cost_inr": 0.11,
                    "status": "SUCCESS",
                },
                {
                    "agent_name": "domain_problem_solution",
                    "model": "claude-sonnet-5-5",
                    "input_tokens": 8000,
                    "output_tokens": 2200,
                    "cached_tokens": 8000,
                    "final_cost_usd": 0.0835,
                    "buffered_cost_inr": 9.45,
                    "status": "SUCCESS",
                },
            ],
        }

        table = format_telemetry_table(sample_summary)
        assert "TIDES-AI PLATFORM: ONE-TIME LIVE EVALUATION TELEMETRY AUDIT" in table
        assert "document_extraction" in table
        assert "domain_problem_solution" in table
        assert "PASSED (WITHIN INR 50 BUDGET)" in table

    @pytest.mark.anyio
    async def test_pipeline_halts_and_returns_partial_status_on_budget_exhaustion(self):
        """Verifies that if budget ceiling is reached during pipeline evaluation, status is PARTIAL_BUDGET_EXHAUSTED."""
        from app.modules.ai.orchestrator.pipeline import _evaluate_and_generate_report, StageTracer
        from app.modules.startups.models import StartupApplication
        from app.modules.intelligence.models import StartupIntelligenceProfile

        eval_id = f"eval_pipeline_exhaust_{uuid.uuid4().hex[:8]}"
        cost_mgr = CostLedgerManager.get_instance()
        ledger = cost_mgr.get_or_create_ledger(
            evaluation_id=eval_id,
            max_budget_usd=0.35,
        )

        startup = StartupApplication(
            id=uuid.uuid4(),
            startup_name="CleanPower Systems",
            sector="CleanTech",
            stage="Seed",
        )
        profile = StartupIntelligenceProfile(
            id=uuid.uuid4(),
            startup_id=startup.id,
        )

        tracers = {
            "Domain Expert Evaluation": StageTracer("Domain Expert Evaluation"),
            "Knowledge Graph Construction": StageTracer("Knowledge Graph Construction"),
        }

        # Mock ProblemSolutionExpert to simulate budget exhaustion
        with patch("app.modules.evaluation.domains.ProblemSolutionExpert.evaluate", side_effect=AIBudgetExhaustedError("Hard ceiling of $0.35 exceeded")):
            result = await _evaluate_and_generate_report(
                startup=startup,
                profile=profile,
                claims=[],
                evidence=[],
                actor_id=None,
                db=MagicMock(),
                tracers=tracers,
                eval_start_time=MagicMock(),
                evaluation_id=eval_id,
            )

        assert result["evaluation_status"] == "PARTIAL_BUDGET_EXHAUSTED"
        assert "Hard ceiling of $0.35 exceeded" in result["exhaustion_reason"]
        assert "cost_observability" in result
        assert tracers["Domain Expert Evaluation"].status == "EXHAUSTED"

    def test_cli_dry_run_exits_cleanly(self):
        """Verifies running scripts/run_one_time_live_eval.py via subprocess without flags returns 0."""
        python_exe = sys.executable
        script_path = PROJECT_ROOT / "scripts" / "run_one_time_live_eval.py"

        result = subprocess.run(
            [python_exe, str(script_path)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "DRY RUN / PREPARATION ONLY" in result.stdout
        assert "Provider Cost Ceiling:     $0.35 USD" in result.stdout
        assert "Buffered Cost Ceiling:     INR 39.65" in result.stdout
        assert "Problem & Solution (PS, 3 batches):   <= 900 tokens/batch" in result.stdout
        assert "Financials & Support (FI, 5 batches): <= 900 tokens/batch" in result.stdout
        assert "Market Opportunity (MO, 2 batches):   <= 900 tokens/batch" in result.stdout
        assert "Worst-Case Evaluation:     $0.2960 USD" in result.stdout
        assert "Supervisory Reviewer:                 2,400 tokens" in result.stdout
        assert "Gateway Token Forwarding:  FORWARDED (litellm.completion max_tokens parameter)" in result.stdout
        assert "Output Token Caps:     ENFORCED" in result.stdout

    def test_cli_execute_live_without_key_fails_closed(self):
        """Verifies running scripts/run_one_time_live_eval.py --execute-live without key returns exit code 1."""
        python_exe = sys.executable
        script_path = PROJECT_ROOT / "scripts" / "run_one_time_live_eval.py"

        # Explicitly empty ANTHROPIC_API_KEY
        env = os.environ.copy()
        env.pop("ANTHROPIC_API_KEY", None)

        result = subprocess.run(
            [python_exe, str(script_path), "--execute-live"],
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 1
        assert "FATAL: ANTHROPIC_API_KEY is missing or empty" in result.stderr

    def test_reuse_mode_refuses_unauthorized_startup_id(self):
        """Verifies validate_reuse_prerequisites fails closed if requested ID does not match CleanPower Systems."""
        db_mock = MagicMock()
        # Random unauthorized ID
        with pytest.raises(ValueError) as exc:
            validate_reuse_prerequisites(db_mock, "11111111222233334444555566667777")
        assert "authorization failed" in str(exc.value).lower()
        assert AUTHORIZED_REUSE_STARTUP_ID in str(exc.value)

        # Invalid UUID string
        with pytest.raises(ValueError) as exc:
            validate_reuse_prerequisites(db_mock, "not-a-valid-uuid")
        assert "authorization failed" in str(exc.value).lower()

    def test_reuse_mode_refuses_missing_startup_or_wrong_name(self):
        """Verifies validate_reuse_prerequisites fails closed if startup missing or not CleanPower Systems."""
        db_mock = MagicMock()
        # Case 1: Startup not found
        db_mock.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError) as exc:
            validate_reuse_prerequisites(db_mock, AUTHORIZED_REUSE_STARTUP_ID)
        assert "not found in database" in str(exc.value).lower()

        # Case 2: Startup found but wrong name
        bad_startup = MagicMock(startup_name="ScamEnergy Corp", id=uuid.UUID(hex=AUTHORIZED_REUSE_STARTUP_ID))
        db_mock.query.return_value.filter.return_value.first.return_value = bad_startup
        with pytest.raises(ValueError) as exc:
            validate_reuse_prerequisites(db_mock, AUTHORIZED_REUSE_STARTUP_ID)
        assert "startup name mismatch" in str(exc.value).lower()

    def test_reuse_mode_refuses_missing_profile_or_insufficient_claims(self):
        """Verifies validate_reuse_prerequisites fails closed if profile missing or <50 claims."""
        db_mock = MagicMock()
        target_uuid = uuid.UUID(hex=AUTHORIZED_REUSE_STARTUP_ID)
        valid_startup = MagicMock(startup_name="CleanPower Systems", id=target_uuid)
        db_mock.query.return_value.filter.return_value.first.return_value = valid_startup

        with patch("app.modules.intelligence.repository.StartupIntelligenceProfileRepository.get_by_startup", return_value=None):
            with pytest.raises(ValueError) as exc:
                validate_reuse_prerequisites(db_mock, AUTHORIZED_REUSE_STARTUP_ID)
            assert "profile missing" in str(exc.value).lower()

        # Profile exists but has insufficient claims
        mock_profile = MagicMock(id=uuid.uuid4())
        with patch("app.modules.intelligence.repository.StartupIntelligenceProfileRepository.get_by_startup", return_value=mock_profile), \
             patch("app.modules.intelligence.repository.StartupClaimRepository.list_for_profile", return_value=[MagicMock()] * 10):
            with pytest.raises(ValueError) as exc:
                validate_reuse_prerequisites(db_mock, AUTHORIZED_REUSE_STARTUP_ID)
            assert "insufficient claims" in str(exc.value).lower()

    @pytest.mark.anyio
    async def test_reuse_mode_skips_extraction_and_starts_fresh_ledger(self, tmp_path):
        """Verifies evaluate_existing_startup_with_canonical_claims loads 59 claims,
        skips extraction API calls, initializes a fresh budget ledger, and leaves DB records unchanged."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.db.base import Base
        from app.modules.startups.models import StartupApplication
        from app.modules.intelligence.models import StartupIntelligenceProfile, StartupClaim
        from app.modules.ai.orchestrator.pipeline import evaluate_existing_startup_with_canonical_claims

        db_path = tmp_path / "test_reuse_isolated.db"
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)

        target_uuid = uuid.UUID(hex=AUTHORIZED_REUSE_STARTUP_ID)
        with Session() as db:
            startup = StartupApplication(
                id=target_uuid,
                startup_name="CleanPower Systems",
                sector="CleanTech",
                stage="Seed",
            )
            db.add(startup)
            profile = StartupIntelligenceProfile(
                id=uuid.uuid4(),
                startup_id=target_uuid,
            )
            db.add(profile)
            for i in range(59):
                claim = StartupClaim(
                    id=uuid.uuid4(),
                    profile_id=profile.id,
                    field_id=uuid.uuid4(),
                    value_string=f"Canonical claim {i}",
                    confidence_score=0.85,
                    validation_status="VALIDATED",
                )
                db.add(claim)
            db.commit()

            claims_before = db.query(StartupClaim).filter(StartupClaim.profile_id == profile.id).count()
            assert claims_before == 59

            mock_eval_result = {
                "evaluation_status": "COMPLETED",
                "startup_id": str(target_uuid),
                "assessment_identifier": "report-reused-01",
            }

            with patch("app.modules.ai.orchestrator.pipeline._evaluate_and_generate_report", return_value=mock_eval_result) as mock_eval, \
                 patch("app.modules.ai.orchestrator.pipeline.create_ai_gateway") as mock_gateway:

                result = await evaluate_existing_startup_with_canonical_claims(
                    db=db,
                    startup_id=target_uuid,
                    max_budget_usd=0.35,
                )

            assert result["evaluation_status"] == "COMPLETED"
            assert mock_gateway.call_count == 0, "Document extraction gateway MUST NOT be called in reuse mode!"
            assert mock_eval.call_count == 1

            # Verify arguments passed to _evaluate_and_generate_report
            call_kwargs = mock_eval.call_args.kwargs
            passed_startup = call_kwargs["startup"]
            passed_profile = call_kwargs["profile"]
            passed_claims = call_kwargs["claims"]
            assert passed_startup.id == target_uuid
            assert passed_profile.id == profile.id
            assert len(passed_claims) == 59

            # Database unchanged
            claims_after = db.query(StartupClaim).filter(StartupClaim.profile_id == profile.id).count()
            assert claims_after == 59

            # Fresh ledger created with full budget ceiling
            cost_manager = CostLedgerManager.get_instance()
            eval_id = call_kwargs["evaluation_id"]
            ledger = cost_manager.get_ledger(eval_id)
            assert ledger is not None
            assert ledger.spent_usd == 0.0
            assert ledger.max_budget_usd == 0.35

    def test_cli_dry_run_with_reuse_existing_extraction_flag(self):
        """Verifies CLI dry run with --reuse-existing-extraction prints reuse plan and exits 0."""
        python_exe = sys.executable
        script_path = PROJECT_ROOT / "scripts" / "run_one_time_live_eval.py"

        result = subprocess.run(
            [python_exe, str(script_path), "--reuse-existing-extraction"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "REUSE EXISTING EXTRACTION" in result.stdout
        assert AUTHORIZED_REUSE_STARTUP_ID in result.stdout
        assert "Fast Extraction Model:     SKIPPED (0 Haiku API calls)" in result.stdout

    def test_cli_reuse_mode_fails_closed_before_paid_calls_on_unauthorized_id(self):
        """Verifies CLI fails closed if an unauthorized startup ID is passed with --reuse-startup-id."""
        python_exe = sys.executable
        script_path = PROJECT_ROOT / "scripts" / "run_one_time_live_eval.py"

        env = os.environ.copy()
        env["ANTHROPIC_API_KEY"] = "sk-ant-test-dummy-key"

        result = subprocess.run(
            [python_exe, str(script_path), "--execute-live", "--reuse-startup-id", "00000000000000000000000000000000"],
            capture_output=True,
            text=True,
            env=env,
        )

        # Process should fail and log error, not execute
        assert "FAILED_ERROR" in result.stdout or "Reuse authorization failed" in result.stdout or result.returncode != 0

    def test_synthetic_cleanpower_fixture_integrity(self):
        """Verifies the CleanPower Systems PDF fixture exists, is non-empty, and parses valid text."""
        assert SYNTHETIC_FIXTURE_PATH.exists()
        assert SYNTHETIC_FIXTURE_PATH.stat().st_size > 0

        from app.modules.intelligence.parsers import ParserManager
        parsed = ParserManager.parse_file(str(SYNTHETIC_FIXTURE_PATH), "application/pdf")
        text = parsed["normalized_text"]
        assert "CleanPower Systems" in text
        assert "Dr. Arjun Sharma" in text
        assert "Priya Mehta" in text

    def test_all_six_canonical_domain_experts_configure_bounded_batched_output_tokens(self):
        """Verifies all 6 canonical domain experts execute bounded criterion batches:
        - max_criteria_per_call == 3 (PS:5, MO:4, FT:5, BC:5, II:4, FI:7 -> 30 batches total)
        - batch_max_output_tokens == 900 across all 6 specialists
        - every dispatched gateway call enforces max_output_tokens <= 900 and evaluates 81 criteria total
        """
        from app.modules.evaluation.domains import (
            ProblemSolutionExpert,
            MarketOpportunityExpert,
            FounderTeamExpert,
            CommercialisationExpert,
            InnovationImpactExpert,
            FinancialsSupportExpert,
        )
        from app.modules.evaluation.domain_schemas import BatchCriterionResult, DomainCriterionBatchOutput
        from app.services.ai.schemas import AICompletionMetadata, AICompletionResult

        experts = {
            "problem_solution": ProblemSolutionExpert(),
            "market_opportunity": MarketOpportunityExpert(),
            "founder_team": FounderTeamExpert(),
            "commercialisation": CommercialisationExpert(),
            "innovation_impact": InnovationImpactExpert(),
            "financials_support": FinancialsSupportExpert(),
        }

        expected_batches = {
            "problem_solution": 5,
            "market_opportunity": 4,
            "founder_team": 5,
            "commercialisation": 5,
            "innovation_impact": 4,
            "financials_support": 7,
        }

        for dkey, exp in experts.items():
            assert exp.max_criteria_per_call == 3
            assert exp.batch_max_output_tokens == 900
            assert exp.max_output_tokens <= 900

        captured_requests = []
        mock_gateway = MagicMock()

        def mock_complete_json(req, response_model):
            captured_requests.append((req, response_model))
            meta = req.metadata or {}
            out = DomainCriterionBatchOutput(
                domain=meta["domain"],
                batch_index=int(meta["batch_index"]),
                criteria=[
                    BatchCriterionResult(
                        criterion_id=cid,
                        verification_status="SELF_REPORTED_ONLY",
                        score=6.5,
                        evidence_ids=[],
                        rationale="Recorded from startup disclosure.",
                    )
                    for cid in meta["batch_criterion_ids"]
                ],
            )
            return AICompletionResult(
                data=out,
                metadata=AICompletionMetadata(
                    provider="anthropic",
                    model="claude-sonnet-5-5",
                    latency_ms=10.0,
                    cost_usd=0.005,
                ),
            )

        mock_gateway.complete_json = mock_complete_json

        total_criteria = 0
        for dkey, exp in experts.items():
            exp.gateway = mock_gateway
            rep = exp.evaluate(
                profile=MagicMock(startup_id="mock-01", startup_name="CleanPower Systems"),
                claims=[],
                evidence=[],
                conflicts=[],
                metadata={"evaluation_id": f"test-eval-id-{dkey}"},
            )
            total_criteria += len(rep.criteria_evaluations)
            assert rep.composite_domain_confidence > 0.0

        assert len(captured_requests) == sum(expected_batches.values()) == 30
        assert total_criteria == 81
        for req, rmodel in captured_requests:
            assert rmodel == DomainCriterionBatchOutput
            assert req.max_output_tokens <= 900
            assert 1 <= len(req.metadata["batch_criterion_ids"]) <= 5

    def test_all_six_canonical_domains_retain_all_87_canonical_criteria(self):
        """Verifies all 6 domains retain their registered LaunchIndex criteria (81 across 6 domains, 87 across full framework)."""
        from app.modules.evaluation.domains import (
            ProblemSolutionExpert,
            MarketOpportunityExpert,
            FounderTeamExpert,
            CommercialisationExpert,
            InnovationImpactExpert,
            FinancialsSupportExpert,
        )
        from app.modules.evaluation.domains.registry import CRITERIA_DIRECTORY, get_criteria_for_domain

        experts = [
            ProblemSolutionExpert(),
            MarketOpportunityExpert(),
            FounderTeamExpert(),
            CommercialisationExpert(),
            InnovationImpactExpert(),
            FinancialsSupportExpert(),
        ]
        all_domain_criteria = []
        for exp in experts:
            owned = exp.get_owned_criteria()
            assert len(owned) > 0, f"Domain {exp.domain_key} has 0 criteria!"
            all_domain_criteria.extend(owned)

        # 81 criteria owned across the 6 canonical evaluation domains
        assert len(all_domain_criteria) == 81, f"Expected 81 domain criteria, got {len(all_domain_criteria)}"
        assert len(set(all_domain_criteria)) == 81, "Duplicate criteria detected across domains!"

        # 6 criteria owned by intake & completeness (CM-01 through CM-06)
        intake_criteria = get_criteria_for_domain("intake_completeness")
        assert len(intake_criteria) == 6

        # Total 87 canonical criteria registered across the LaunchIndex framework
        assert len(CRITERIA_DIRECTORY) == 87, f"Expected 87 total canonical criteria, got {len(CRITERIA_DIRECTORY)}"

    def test_supervisory_reviewer_configures_2400_max_output_tokens(self):
        """Verifies that SupervisoryReviewer configures ai_request.max_output_tokens=2400."""
        from app.modules.evaluation.supervisory.reviewer import SupervisoryReviewer
        from app.modules.evaluation.domain_schemas import DomainAssessmentReport, ConfidenceHierarchy

        reviewer = SupervisoryReviewer()
        captured_requests = []
        mock_gateway = MagicMock()
        def mock_complete_json(*args, **kwargs):
            req = kwargs.get("request") or (args[0] if args else None)
            captured_requests.append(req)
            from app.modules.evaluation.domain_schemas import SupervisoryReviewOutput
            res = MagicMock()
            res.data = SupervisoryReviewOutput(
                executive_summary="Diligence synthesis complete.",
                recommendation_rationale="Solid business case.",
                overall_recommendation="CONDITIONAL",
            )
            return res

        mock_gateway.complete_json = mock_complete_json
        reviewer.gateway = mock_gateway

        # Minimal dummy domain report
        dummy_report = DomainAssessmentReport(
            domain="problem_solution",
            domain_key="problem_solution",
            domain_title="Problem & Solution",
            evaluation_id="test-eval-id",
            startup_id="test-startup",
            criteria_evaluated=[],
            criteria_evaluations={},
            summary="Pass",
            executive_summary="Pass",
            executive_conclusion="Pass",
            reasoning="Grounded",
            investment_implication="Proceed",
            observations=[],
            risks=[],
            questions=[],
            missing_evidence=[],
            confidence=ConfidenceHierarchy(finding_confidence=0.8, evidence_confidence=0.8, reasoning_confidence=0.8, overall_domain_confidence=0.8),
            prompt_name="test",
            prompt_version="1.0",
            prompt_hash="hash",
            agent_version="1.0",
        )

        reviewer.review(
            domain_reports={"problem_solution": dummy_report},
            domain_experts={},
            profile=MagicMock(startup_id="test-startup", startup_name="CleanPower Systems", sector="CleanTech", stage="Seed"),
            claims=[],
            evidence=[],
            metadata={"evaluation_id": "test-eval-id"},
        )

        assert len(captured_requests) == 1
        assert captured_requests[0].max_output_tokens == 2400

    def test_litellm_gateway_forwards_max_tokens_to_completion(self):
        """Verifies LiteLLMGateway actually passes max_tokens to litellm.completion."""
        from app.services.ai.litellm import LiteLLMGateway
        from litellm import Choices, Message, ModelResponse, Usage
        from pydantic import BaseModel

        class SimpleModel(BaseModel):
            text: str

        gateway = LiteLLMGateway(model="claude-sonnet-5-5", api_key="test-key", max_retries=0)
        req = AICompletionRequest(
            system_prompt="sys",
            user_prompt="usr",
            agent_name="test_agent",
            max_output_tokens=1800,
        )

        mock_resp = ModelResponse()
        mock_resp.model = "claude-sonnet-5-5"
        choice = Choices()
        msg = Message()
        msg.content = '{"text": "hello"}'
        choice.message = msg
        choice.finish_reason = "stop"
        mock_resp.choices = [choice]
        usage = Usage()
        usage.prompt_tokens = 100
        usage.completion_tokens = 10
        usage.total_tokens = 110
        mock_resp.usage = usage

        passed_kwargs = {}
        def mock_completion(*args, **kwargs):
            nonlocal passed_kwargs
            passed_kwargs = kwargs
            return mock_resp

        with patch("litellm.completion", side_effect=mock_completion):
            gateway.complete_json(req, SimpleModel)

        assert passed_kwargs.get("max_tokens") == 1800, "LiteLLMGateway failed to forward max_tokens to litellm.completion!"

    def test_budget_reservation_and_worst_case_evaluation_under_ceiling(self):
        """Mathematically verifies that 6 sequential domain calls (PS=2400, FI=2400, MO/FT/BC/II=1800)
        and 1 supervisory review call (2400 tokens max) fit safely under the $0.35 ceiling."""
        from app.services.ai.pricing import get_pricing_catalog

        pricing = get_pricing_catalog("2026-10-live-v1")
        sonnet_p = pricing.get_pricing("claude-sonnet-5-5")
        assert sonnet_p.input_cost_per_m == 2.0
        assert sonnet_p.output_cost_per_m == 10.0

        # Max planned reservation per domain category (8500 in)
        res_domain_1800 = pricing.estimate_max_cost("claude-sonnet-5-5", 8500, 1800)
        res_domain_2400 = pricing.estimate_max_cost("claude-sonnet-5-5", 8500, 2400)
        # Max planned reservation for review (1500 in, 2400 out)
        res_review = pricing.estimate_max_cost("claude-sonnet-5-5", 1500, 2400)

        # Worst-case actual execution cost across the entire evaluation
        worst_cost_1800 = pricing.calculate_cost("claude-sonnet-5-5", 8500, 1800)  # 0.035
        worst_cost_2400 = pricing.calculate_cost("claude-sonnet-5-5", 8500, 2400)  # 0.041
        worst_review_cost = pricing.calculate_cost("claude-sonnet-5-5", 1500, 2400)  # 0.027
        worst_total_cost = round(4 * worst_cost_1800 + 2 * worst_cost_2400 + worst_review_cost, 6)

        assert worst_total_cost == 0.249000
        assert worst_total_cost <= 0.350000, f"Worst-case cost ${worst_total_cost} exceeds $0.35 ceiling!"

        # Converted INR cost with 1.18x buffer
        raw_inr, buf_inr = pricing.convert_to_inr(worst_total_cost, exchange_rate=96.0, buffer_multiplier=1.18)
        assert buf_inr <= 39.65, f"Buffered INR {buf_inr} exceeds ₹39.65 ceiling!"

        # Sequential reservation feasibility check:
        # After 6 domains execute at worst-case, remaining budget must still cover res_review
        worst_domains_spent = round(4 * worst_cost_1800 + 2 * worst_cost_2400, 6)
        remaining_after_domains = round(0.350000 - worst_domains_spent, 6)
        assert remaining_after_domains >= res_review, (
            f"Remaining budget ${remaining_after_domains} is not enough for supervisory reservation ${res_review}!"
        )

    def test_workspace_database_hash_unchanged(self):
        """Absolute safety guard: workspace tides_ai.db MUST NOT be modified or touched."""
        assert WORKSPACE_DB.exists(), "Workspace tides_ai.db not found!"
        current_hash = hashlib.sha256(WORKSPACE_DB.read_bytes()).hexdigest()
        assert current_hash == EXPECTED_WORKSPACE_DB_HASH, (
            f"FATAL: Workspace database SHA-256 altered!\n"
            f"Expected: {EXPECTED_WORKSPACE_DB_HASH}\n"
            f"Actual:   {current_hash}"
        )
