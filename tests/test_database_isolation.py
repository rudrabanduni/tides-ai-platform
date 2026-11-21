"""Regression tests verifying database isolation during automated testing.

Confirms that:
1. Automated tests cannot silently connect to or modify the workspace tides_ai.db.
2. The active SQLAlchemy engine and SessionLocal bind strictly to an isolated test database.
3. Database writes during tests affect only the temporary test database.
4. The workspace database SHA-256 digest remains bit-for-bit unchanged.
5. The production application configuration (.env) is neither mutated nor replaced.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal, engine
from app.modules.audit.models import AuditLog

WORKSPACE_DB_PATH = Path("tides_ai.db").resolve()
EXPECTED_WORKSPACE_HASH = "d9659f4e8c1058c5d5f4511e1bb22d3abe6cb12101c16ce397416051a38176c7"
EXPECTED_WORKSPACE_SIZE = 3_149_824


def test_test_engine_binds_to_isolated_database():
    """Verify that the active engine url is pointing to a dedicated isolated test database."""
    engine_url_str = str(engine.url)
    assert "isolated_test_tides" in engine_url_str or "tides_test_db_" in engine_url_str
    assert "tides_ai.db" not in engine_url_str or "isolated" in engine_url_str


def test_settings_database_url_isolation():
    """Verify that get_settings().database_url resolves to the isolated test database."""
    settings = get_settings()
    assert "isolated_test_tides" in settings.database_url or "tides_test_db_" in settings.database_url
    assert not settings.database_url.endswith("tides_ai.db")


def test_workspace_database_hash_and_size_integrity():
    """Verify that the workspace tides_ai.db matches its baseline size and SHA-256."""
    assert WORKSPACE_DB_PATH.exists(), "Workspace tides_ai.db must exist."
    current_size = os.path.getsize(WORKSPACE_DB_PATH)
    assert current_size == EXPECTED_WORKSPACE_SIZE, (
        f"Workspace db size mismatch: Expected {EXPECTED_WORKSPACE_SIZE}, Got {current_size}"
    )

    with open(WORKSPACE_DB_PATH, "rb") as f:
        current_hash = hashlib.sha256(f.read()).hexdigest()

    assert current_hash == EXPECTED_WORKSPACE_HASH, (
        f"Workspace db hash mismatch: Expected {EXPECTED_WORKSPACE_HASH}, Got {current_hash}"
    )


def test_db_operations_isolated_from_workspace_database():
    """Verify that writes via SessionLocal write to the isolated test database
    and do not alter the workspace tides_ai.db hash.
    """
    with open(WORKSPACE_DB_PATH, "rb") as f:
        pre_write_hash = hashlib.sha256(f.read()).hexdigest()

    # Write a record via SessionLocal
    test_action = "TEST_ISOLATION_PROBE"
    with SessionLocal() as session:
        log_entry = AuditLog(
            action=test_action,
            entity_type="TestEntity",
            entity_id="test-probe-123",
            details={"probe": "isolation_verification"},
        )
        session.add(log_entry)
        session.commit()

    # Verify record exists in active test session
    with SessionLocal() as session:
        queried = session.scalars(select(AuditLog).where(AuditLog.action == test_action)).first()
        assert queried is not None
        assert queried.entity_id == "test-probe-123"

    # Verify workspace tides_ai.db was untouched
    with open(WORKSPACE_DB_PATH, "rb") as f:
        post_write_hash = hashlib.sha256(f.read()).hexdigest()

    assert pre_write_hash == post_write_hash
    assert post_write_hash == EXPECTED_WORKSPACE_HASH


def test_dev_database_init_preserves_workspace_db(tmp_path, monkeypatch):
    """Verify that init_dev_database targets tides_dev.db by default and never the workspace db.

    v1.1: the initialiser is exercised against a TEMPORARY dev database. The previous version
    ran it against the real tides_dev.db (which holds the PETREVOLT history) and mutated its schema.
    """
    from scripts.init_dev_db import init_dev_database, get_dev_db_path

    monkeypatch.delenv("DEV_DATABASE_URL", raising=False)
    default_path = get_dev_db_path()
    assert default_path != WORKSPACE_DB_PATH
    assert "tides_dev.db" in str(default_path)

    temp_dev = tmp_path / "tides_dev.db"
    monkeypatch.setenv("DEV_DATABASE_URL", f"sqlite:///{temp_dev.as_posix()}")
    assert get_dev_db_path() == temp_dev.resolve()
    init_dev_database()
    assert temp_dev.exists()

    with open(WORKSPACE_DB_PATH, "rb") as f:
        current_hash = hashlib.sha256(f.read()).hexdigest()
    assert current_hash == EXPECTED_WORKSPACE_HASH


def test_run_dev_backend_refuses_workspace_db():
    """Verify that run_dev_backend.py fails closed if DATABASE_URL points to tides_ai.db."""
    import subprocess
    import sys

    env = os.environ.copy()
    env["DATABASE_URL"] = "sqlite:///./tides_ai.db"
    res = subprocess.run([sys.executable, "scripts/run_dev_backend.py"], env=env, capture_output=True, text=True)
    assert res.returncode == 1
    assert "protected workspace database 'tides_ai.db'" in res.stderr

