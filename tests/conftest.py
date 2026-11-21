"""Pytest root configuration and database test isolation.

Ensures all automated tests execute against an isolated temporary SQLite database,
preventing tests or middleware from touching, altering, or polluting the workspace tides_ai.db.
"""

from __future__ import annotations

import atexit
import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest

# 1. Locate workspace database and protected artifacts and compute pre-test baseline hashes
WORKSPACE_DB_PATH = Path("tides_ai.db").resolve()
PROTECTED_ARTIFACTS = [
    WORKSPACE_DB_PATH,
    Path("reports/live_eval_run_report.json").resolve(),
    Path("uploads/graphs/a246f3a5-b797-43fc-9dc3-3e603e3b37b9.json").resolve(),
    # Historical PETREVOLT development database: must be byte-identical after the suite.
    Path("tides_dev.db").resolve(),
    Path("reports/telemetry/eval_1a8036ae-0e37-4fb0-b241-680d2bb62b8d.json").resolve(),
]
_INITIAL_ARTIFACT_HASHES: dict[Path, str] = {}
for _artifact_path in PROTECTED_ARTIFACTS:
    if _artifact_path.exists():
        with open(_artifact_path, "rb") as f:
            _INITIAL_ARTIFACT_HASHES[_artifact_path] = hashlib.sha256(f.read()).hexdigest()
_INITIAL_WORKSPACE_DB_HASH: str | None = _INITIAL_ARTIFACT_HASHES.get(WORKSPACE_DB_PATH)

# 2. Setup isolated temporary directory, test database, upload dir, and report dir
_test_db_dir = tempfile.mkdtemp(prefix="tides_test_db_")
_test_db_path = os.path.join(_test_db_dir, "isolated_test_tides.db")
_test_upload_dir = os.path.join(_test_db_dir, "uploads")
_test_report_path = os.path.join(_test_db_dir, "live_eval_run_report.json")
os.makedirs(os.path.join(_test_upload_dir, "graphs"), exist_ok=True)

# Point environment variables so pydantic-settings & pipeline read isolated paths with highest priority
os.environ["DATABASE_URL"] = f"sqlite:///{_test_db_path}"
os.environ["UPLOAD_DIR"] = _test_upload_dir
os.environ["TIDES_LIVE_EVAL_REPORT_PATH"] = _test_report_path

# Clear cached settings so get_settings() reloads with the isolated DATABASE_URL
from app.core.config import get_settings

get_settings.cache_clear()

# 3. Initialize full schema on the isolated test database
from app.db.base import Base
from app.db.session import engine

Base.metadata.create_all(bind=engine)


def _cleanup_test_dir() -> None:
    try:
        engine.dispose()
    except Exception:
        pass
    if os.path.exists(_test_db_dir):
        shutil.rmtree(_test_db_dir, ignore_errors=True)


atexit.register(_cleanup_test_dir)


@pytest.fixture(scope="session", autouse=True)
def enforce_database_isolation() -> Generator[None, None, None]:
    """Session-scoped fixture verifying test isolation from workspace tides_ai.db."""
    from app.db.session import engine as active_engine

    # Fail immediately if the engine accidentally resolved to the workspace tides_ai.db
    engine_url_str = str(active_engine.url)
    assert "tides_test_db_" in engine_url_str or "isolated_test_tides" in engine_url_str, (
        f"CRITICAL TEST ISOLATION FAILURE: active engine url '{engine_url_str}' "
        "is not pointing to the isolated test database!"
    )

    yield

    # Teardown check: verify workspace database and protected artifact hashes were not touched
    active_engine.dispose()
    for _artifact_path, _initial_hash in _INITIAL_ARTIFACT_HASHES.items():
        if _artifact_path.exists():
            with open(_artifact_path, "rb") as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()
            assert current_hash == _initial_hash, (
                f"CRITICAL TEST ISOLATION FAILURE: Workspace artifact {_artifact_path} was modified during tests!\n"
                f"Expected: {_initial_hash}\n"
                f"Actual:   {current_hash}"
            )


@pytest.fixture(autouse=True)
def isolate_test_environment() -> Generator[None, None, None]:
    """Per-test fixture that preserves environment variables and settings cache,
    preventing individual tests from leaking AI_PROVIDER, DATABASE_URL, or other mutations.
    """
    old_env = dict(os.environ)
    yield
    # Restore environment
    os.environ.clear()
    os.environ.update(old_env)
    from app.core.config import get_settings
    get_settings.cache_clear()
    from sqlalchemy import create_engine
    import app.db.session as session_module
    session_module.settings = get_settings()
    session_module.engine = create_engine(session_module.settings.database_url, pool_pre_ping=True)
    session_module.SessionLocal.configure(bind=session_module.engine)
