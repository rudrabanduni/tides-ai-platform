"""Regression tests for database isolation guards, CLI target selection,
strict $0.35 budget enforcement, and fail-closed production gateway readiness.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import hashlib
import math
import os
import subprocess
import sys
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from litellm.utils import Choices, Message, ModelResponse, Usage
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import PROJECT_ROOT, Settings, get_settings, validate_database_configuration
from app.db.base import Base
from app.core.enums import DocumentProcessingStatus, DocumentType, StartupStatus
from app.modules.ai.orchestrator.pipeline import coordinate_evaluation_pipeline
from app.modules.documents.models import Document
from app.modules.startup_profiles.models import AIAssessmentRecord
from app.modules.startups.models import StartupApplication
from app.services.ai.cost_ledger import CostLedgerManager, EvaluationCostLedger
from app.services.ai.exceptions import AIBudgetExhaustedError, AIProviderError, AIResponseParseError
from app.services.ai.gateway import create_ai_gateway
from app.services.ai.litellm import LiteLLMGateway, evaluation_cost
from app.services.ai.schemas import AICompletionRequest
from scripts.init_dev_db import init_dev_database
from scripts.run_one_time_live_eval import (
    AUTHORIZED_REUSE_STARTUP_ID,
    HISTORICAL_STETHAIM_STARTUP_ID,
    PETREVOLT_TARGET_STARTUP_ID,
    validate_target_startup_prerequisites,
)


class _DummyOutput(BaseModel):
    message: str
    score: int


def _python_exe() -> str:
    return sys.executable


@pytest.fixture
def db_session(tmp_path: Path):
    db_file = tmp_path / "isolated_unit.db"
    engine = create_engine(f"sqlite:///{db_file}", pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with Session() as session:
        yield session
    engine.dispose()


class TestDatabaseAndConfigGuards:
    def test_env_templates_are_safe_and_isolated(self) -> None:
        env_example = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
        assert "DATABASE_URL=sqlite:///./tides_dev.db" in env_example
        assert "DATABASE_URL=sqlite:///./tides_ai.db" not in env_example
        assert "AI_PROVIDER=mock" in env_example

        prod_template = PROJECT_ROOT / ".env.production.example"
        assert prod_template.exists()
        prod_text = prod_template.read_text(encoding="utf-8")
        assert "APP_ENV=production" in prod_text
        assert "AI_ENABLED=true" in prod_text
        assert "AI_PROVIDER=anthropic" in prod_text
        assert "RESEARCH_PROVIDER=disabled" in prod_text
        assert "AI_MAX_EVALUATION_BUDGET_USD=0.35" in prod_text
        assert "AI_MAX_RETRIES=0" in prod_text
        assert "tides_dev.db" not in prod_text
        assert "tides_ai.db" not in prod_text
        for line in prod_text.splitlines():
            if line.startswith(("ANTHROPIC_API_KEY=", "TAVILY_API_KEY=")):
                assert line.split("=", 1)[1].strip() == ""

    def test_runtime_config_refuses_protected_snapshot_tides_ai_db(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for url in (
            "sqlite:///./tides_ai.db",
            "sqlite:///tides_ai.db",
            f"sqlite:///{(PROJECT_ROOT / 'tides_ai.db').resolve()}",
        ):
            monkeypatch.setenv("APP_ENV", "development")
            monkeypatch.setenv("DATABASE_URL", url)
            get_settings.cache_clear()
            with pytest.raises(RuntimeError, match="tides_ai\\.db"):
                Settings(_env_file=None)

    def test_production_mode_requires_explicit_non_sqlite_database_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.delenv("DATABASE_URL", raising=False)
        get_settings.cache_clear()
        with pytest.raises(RuntimeError, match="explicitly configured DATABASE_URL"):
            Settings(_env_file=None)

        for bad_url in ("sqlite:///./tides_dev.db", "sqlite:///./tides_ai.db", "sqlite:///tmp/local.db"):
            monkeypatch.setenv("DATABASE_URL", bad_url)
            with pytest.raises(RuntimeError):
                Settings(_env_file=None)

        monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://prod_user:strong_pw@db.internal:5432/tides_prod")
        # v1.1: production also refuses the default / weak JWT signing secret
        monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
        with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
            Settings(_env_file=None)
        monkeypatch.setenv("JWT_SECRET_KEY", "short")
        with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
            Settings(_env_file=None)
        monkeypatch.setenv("JWT_SECRET_KEY", "x" * 48)
        prod_settings = Settings(_env_file=None)
        assert prod_settings.app_env == "production"
        assert prod_settings.database_url.startswith("postgresql+psycopg://")
        validate_database_configuration(prod_settings)

    def test_init_dev_db_refuses_protected_snapshot(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DEV_DATABASE_URL", "sqlite:///./tides_ai.db")
        with pytest.raises(RuntimeError, match="tides_ai\\.db"):
            init_dev_database()

    def test_create_app_enforces_database_policy(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from app.api.main import create_app

        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("DATABASE_URL", "sqlite:///./tides_dev.db")
        get_settings.cache_clear()
        with pytest.raises(RuntimeError, match="APP_ENV=production"):
            create_app()


class TestTargetStartupSelectionAndPipeline:
    def test_validate_target_startup_prerequisites_paths(self, db_session, tmp_path: Path) -> None:
        deck_file = tmp_path / "petrevolt_deck.pdf"
        deck_file.write_bytes(b"%PDF-1.4\n%Valid mock test bytes\n")

        target_uuid = uuid.UUID(PETREVOLT_TARGET_STARTUP_ID)
        startup = StartupApplication(
            id=target_uuid,
            startup_name="PETREVOLT ENERGY SOLUTIONS PVT LTD",
            sector="CleanTech / Energy Storage",
            stage="Seed",
            current_status=StartupStatus.UNDER_REVIEW,
        )
        db_session.add(startup)
        db_session.flush()

        # Zero documents fails closed
        with pytest.raises(ValueError, match="no registered source documents"):
            validate_target_startup_prerequisites(db_session, PETREVOLT_TARGET_STARTUP_ID, expect_petrevolt=True)

        # Register valid document
        doc = Document(
            startup_id=startup.id,
            document_type=DocumentType.PITCH_DECK,
            original_filename="petrevolt_deck.pdf",
            stored_filename="petrevolt_deck.pdf",
            file_path=str(deck_file),
            content_type="application/pdf",
            file_size=deck_file.stat().st_size,
            parsed_text="Solid-state sodium-ion batteries from PET plastic waste.",
            processing_status=DocumentProcessingStatus.PARSED,
        )
        db_session.add(doc)
        db_session.flush()

        resolved_startup, docs_info = validate_target_startup_prerequisites(
            db_session, PETREVOLT_TARGET_STARTUP_ID, expect_petrevolt=True
        )
        assert resolved_startup.id == target_uuid
        assert len(docs_info) == 1
        assert docs_info[0]["sha256"] == hashlib.sha256(deck_file.read_bytes()).hexdigest()

        # Invalid UUID / nonexistent ID / CleanPower / STETHAIM fail closed
        with pytest.raises(ValueError, match="Invalid target startup UUID"):
            validate_target_startup_prerequisites(db_session, "not-a-uuid")
        with pytest.raises(ValueError, match="not found"):
            validate_target_startup_prerequisites(db_session, str(uuid.uuid4()))
        with pytest.raises(ValueError, match="CleanPower"):
            validate_target_startup_prerequisites(db_session, AUTHORIZED_REUSE_STARTUP_ID)
        with pytest.raises(ValueError, match="STETHAIM"):
            validate_target_startup_prerequisites(db_session, HISTORICAL_STETHAIM_STARTUP_ID)
        with pytest.raises(ValueError, match="--petrevolt target mismatch"):
            validate_target_startup_prerequisites(db_session, str(uuid.uuid4()), expect_petrevolt=True)

        # Missing file on disk fails closed
        deck_file.unlink()
        with pytest.raises(FileNotFoundError, match="missing on disk"):
            validate_target_startup_prerequisites(db_session, PETREVOLT_TARGET_STARTUP_ID)

        # Empty 0-byte file fails closed
        deck_file.write_bytes(b"")
        with pytest.raises(ValueError, match="empty"):
            validate_target_startup_prerequisites(db_session, PETREVOLT_TARGET_STARTUP_ID)

    def test_cli_dry_run_petrevolt_and_conflict_rejection(self) -> None:
        if not (PROJECT_ROOT / "tides_dev.db").exists():
            pytest.skip("tides_dev.db not present in workspace")

        ok = subprocess.run(
            [_python_exe(), "scripts/run_one_time_live_eval.py", "--petrevolt"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        assert ok.returncode == 0, ok.stderr
        assert "1b5de317-6e56-4dcb-ada9-28ab9adf8c0c" in ok.stdout
        assert "PETREVOLT ENERGY SOLUTIONS PVT LTD" in ok.stdout
        assert "DRY RUN / PREPARATION ONLY" in ok.stdout

        conflict = subprocess.run(
            [_python_exe(), "scripts/run_one_time_live_eval.py", "--petrevolt", "--stethaim-pilot"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        assert conflict.returncode == 1
        assert "Cannot combine" in conflict.stderr

        mismatch = subprocess.run(
            [
                _python_exe(),
                "scripts/run_one_time_live_eval.py",
                "--petrevolt",
                "--startup-id",
                str(uuid.uuid4()),
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )
        assert mismatch.returncode == 1
        assert "conflicts" in mismatch.stderr

    def test_coordinate_pipeline_existing_startup_preserves_id_and_history(self, db_session, tmp_path: Path) -> None:
        CostLedgerManager.get_instance().clear_all()
        deck = tmp_path / "petrevolt_mock.pdf"
        deck.write_bytes(b"%PDF-1.4\nPETREVOLT solid-state sodium-ion battery\n")

        target_uuid = uuid.uuid4()
        startup = StartupApplication(
            id=target_uuid,
            startup_name="PETREVOLT ENERGY SOLUTIONS PVT LTD",
            sector="CleanTech / Energy Storage",
            stage="Seed",
            current_status=StartupStatus.UNDER_REVIEW,
        )
        db_session.add(startup)
        db_session.flush()
        db_session.add(
            Document(
                startup_id=startup.id,
                document_type=DocumentType.PITCH_DECK,
                original_filename="petrevolt_mock.pdf",
                stored_filename="petrevolt_mock.pdf",
                file_path=str(deck),
                content_type="application/pdf",
                file_size=deck.stat().st_size,
                parsed_text="PETREVOLT solid-state sodium-ion battery from waste PET plastic.",
                processing_status=DocumentProcessingStatus.PARSED,
            )
        )
        db_session.commit()

        with patch.object(get_settings(), "upload_dir", str(tmp_path)), \
             patch.object(get_settings(), "ai_provider", "mock"), \
             patch.object(get_settings(), "ai_enabled", True):
            res1 = asyncio.run(
                coordinate_evaluation_pipeline(
                    db=db_session,
                    startup_name="PETREVOLT ENERGY SOLUTIONS PVT LTD",
                    sector="CleanTech / Energy Storage",
                    stage="Seed",
                    files=[],
                    existing_startup_id=target_uuid,
                    max_budget_usd=0.35,
                )
            )
            res2 = asyncio.run(
                coordinate_evaluation_pipeline(
                    db=db_session,
                    startup_name="PETREVOLT ENERGY SOLUTIONS PVT LTD",
                    sector="CleanTech / Energy Storage",
                    stage="Seed",
                    files=[],
                    existing_startup_id=target_uuid,
                    max_budget_usd=0.35,
                )
            )

        assert res1["startup_id"] == str(target_uuid)
        assert res2["startup_id"] == str(target_uuid)
        assert res1["evaluation_id"] != res2["evaluation_id"]
        assert res1["ai_provider"] == "mock"
        assert res1["cost_observability"]["max_budget_usd"] == 0.35
        assert res2["cost_observability"]["max_budget_usd"] == 0.35
        assert res1["cost_observability"]["total_spent_usd"] <= 0.35

        assessments = (
            db_session.query(AIAssessmentRecord)
            .filter(AIAssessmentRecord.startup_id == target_uuid)
            .all()
        )
        assert len(assessments) == 2
        assert (tmp_path / "graphs" / f"{res1['evaluation_id']}.json").exists()
        assert (tmp_path / "graphs" / f"{res2['evaluation_id']}.json").exists()


class TestStrictBudgetAndFailClosedGateway:
    def test_ten_budget_control_scenarios_at_035_ceiling(self, monkeypatch: pytest.MonkeyPatch) -> None:
        CostLedgerManager.get_instance().clear_all()
        evaluation_cost.set(0.0)
        gateway = LiteLLMGateway(api_key="test-key", max_retries=0)
        monkeypatch.setenv("AI_MAX_EVALUATION_BUDGET_USD", "0.35")
        get_settings.cache_clear()

        # 1. Within $0.35 budget succeeds & reconciles
        eval_ok = f"eval-ok-{uuid.uuid4().hex[:8]}"
        ledger_ok = CostLedgerManager.get_instance().get_or_create_ledger(eval_ok, max_budget_usd=0.35)
        ok_resp = ModelResponse(
            id="resp-ok",
            choices=[Choices(message=Message(content=_DummyOutput(message="ok", score=9).model_dump_json()))],
            created=100,
            model="claude-haiku-5-5",
            usage=Usage(prompt_tokens=1_000, completion_tokens=200, total_tokens=1_200),
        )
        req_small = AICompletionRequest(
            agent_name="SmallOp",
            evaluation_id=eval_ok,
            system_prompt="sys",
            user_prompt="usr",
            estimated_input_tokens=1_000,
            max_output_tokens=200,
            metadata={"operation_id": "op_unique_1"},
        )
        with patch("litellm.completion", return_value=ok_resp):
            res_ok = gateway.complete_json(req_small, _DummyOutput)
        assert res_ok.metadata.cost_usd > 0
        assert ledger_ok.spent_usd <= 0.35
        assert ledger_ok.reserved_usd == 0.0

        # 2. Exceeding $0.35 ceiling pre-call blocks before dispatch
        req_huge = AICompletionRequest(
            agent_name="HugeOp",
            evaluation_id=eval_ok,
            system_prompt="sys",
            user_prompt="usr",
            estimated_input_tokens=150_000,
            max_output_tokens=20_000,
        )
        with patch("litellm.completion") as mock_call:
            with pytest.raises(AIBudgetExhaustedError):
                gateway.complete_json(req_huge, _DummyOutput)
            mock_call.assert_not_called()
        assert ledger_ok.reserved_usd == 0.0

        # 3. Exact exhaustion & 4. Insufficient remaining budget
        ledger_exact = EvaluationCostLedger("eval-exact-035", max_budget_usd=0.35)
        res_id = ledger_exact.reserve_budget(0.32, "StageA")
        ledger_exact.reconcile_operation(res_id, "StageA", "anthropic", "claude-sonnet-5-5", 1000, 500, actual_cost_usd=0.32)
        with pytest.raises(AIBudgetExhaustedError):
            ledger_exact.reserve_budget(0.05, "InsufficientRemaining")
        ledger_exact._is_exhausted = False
        r_fit = ledger_exact.reserve_budget(0.03, "ExactFit")
        ledger_exact.reconcile_operation(r_fit, "ExactFit", "anthropic", "claude-sonnet-5-5", 500, 100, actual_cost_usd=0.03)
        assert ledger_exact.spent_usd == 0.35
        assert ledger_exact.is_exhausted is True
        with pytest.raises(AIBudgetExhaustedError):
            ledger_exact.reserve_budget(0.0001, "PastExactLimit")

        # 5. Concurrent multi-thread reservations respect $0.35 limit
        conc_ledger = EvaluationCostLedger("eval-conc-035", max_budget_usd=0.35)
        def _reserve(i: int) -> bool:
            try:
                conc_ledger.reserve_budget(0.05, f"Worker-{i}")
                return True
            except AIBudgetExhaustedError:
                return False

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            outcomes = list(pool.map(_reserve, range(8)))
        assert sum(outcomes) == 7
        assert conc_ledger.reserved_usd == 0.35

        # 6. Timeout releases reservation
        eval_to = f"eval-to-{uuid.uuid4().hex[:8]}"
        ledger_to = CostLedgerManager.get_instance().get_or_create_ledger(eval_to, max_budget_usd=0.35)
        req_to = AICompletionRequest(
            agent_name="TimeoutOp", evaluation_id=eval_to, system_prompt="s", user_prompt="u",
            estimated_input_tokens=200, max_output_tokens=100,
        )
        with patch("litellm.completion", side_effect=TimeoutError("timed out")):
            with pytest.raises(AIProviderError):
                gateway.complete_json(req_to, _DummyOutput)
        assert ledger_to.reserved_usd == 0.0
        assert ledger_to.spent_usd == 0.0

        # 7. Invalid / malformed usage fails closed and releases reservation
        bad_usage_resp = ModelResponse(
            id="resp-bad-usage",
            choices=[Choices(message=Message(content=_DummyOutput(message="ok", score=1).model_dump_json()))],
            created=101,
            model="claude-haiku-5-5",
            usage=Usage(prompt_tokens=-5, completion_tokens=10, total_tokens=5),
        )
        with patch("litellm.completion", return_value=bad_usage_resp):
            with pytest.raises(AIResponseParseError):
                gateway.complete_json(req_to, _DummyOutput)
        assert ledger_to.reserved_usd == 0.0

        # 8. Recovery incremental accounting & 9. Duplicate operation_id deduplication
        rec_ledger = EvaluationCostLedger("eval-rec-035", max_budget_usd=0.35)
        rec_ledger.restore_from_summary(
            {
                "total_spent_usd": 0.28,
                "operations": [
                    {
                        "operation_id": "op_saved_1",
                        "agent_name": "Prior",
                        "model": "claude-sonnet-5-5",
                        "input_tokens": 2000,
                        "output_tokens": 500,
                        "final_cost_usd": 0.28,
                        "buffered_cost_inr": 31.72,
                    }
                ],
            }
        )
        # Replay duplicate operation_id doesn't double-charge
        r_dup = rec_ledger.reserve_budget(0.05, "Prior")
        rec_ledger.reconcile_operation(r_dup, "Prior", "anthropic", "claude-sonnet-5-5", 2000, 500, actual_cost_usd=0.05, operation_id="op_saved_1")
        assert rec_ledger.spent_usd == 0.28
        # Incremental recovery op succeeding within remaining $0.07
        r_inc = rec_ledger.reserve_budget(0.06, "RecoveryFT")
        rec_ledger.reconcile_operation(r_inc, "RecoveryFT", "anthropic", "claude-sonnet-5-5", 2000, 500, actual_cost_usd=0.04, operation_id="op_rec_ft")
        assert rec_ledger.spent_usd == 0.32
        assert rec_ledger.reserved_usd == 0.0

        # 10. Non-finite cost rejected fail-closed
        with pytest.raises(ValueError):
            rec_ledger.reserve_budget(math.nan, "NaNOp")

    def test_production_gateway_fails_closed_without_key_or_with_mock(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        prod_mock_settings = Settings.model_construct(
            app_env="production",
            ai_enabled=True,
            ai_provider="mock",
            litellm_model="claude-sonnet-5-5",
            ai_request_timeout_seconds=120,
            ai_max_retries=0,
            anthropic_api_key=None,
        )
        with pytest.raises(AIProviderError, match="disabled in production"):
            create_ai_gateway(settings=prod_mock_settings)

        anthropic_no_key = Settings.model_construct(
            app_env="production",
            ai_enabled=True,
            ai_provider="anthropic",
            litellm_model="claude-sonnet-5-5",
            ai_request_timeout_seconds=120,
            ai_max_retries=0,
            anthropic_api_key="",
        )
        with pytest.raises(AIProviderError, match="ANTHROPIC_API_KEY"):
            create_ai_gateway(settings=anthropic_no_key)
