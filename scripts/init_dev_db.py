"""init_dev_db.py - Dedicated Development Database Initializer.

Initializes schema and creates local demo credentials on a dedicated gitignored
database (default: tides_dev.db), completely isolated from the protected workspace
database (tides_ai.db) and test databases.

Usage:
    python scripts/init_dev_db.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def get_dev_db_path() -> Path:
    """Resolve the dedicated development database path."""
    custom_url = os.environ.get("DEV_DATABASE_URL")
    if custom_url and custom_url.startswith("sqlite:///"):
        path_str = custom_url.replace("sqlite:///", "")
        return Path(path_str).resolve()
    return (PROJECT_ROOT / "tides_dev.db").resolve()


def init_dev_database(
    admin_name: str = "Local Demo Analyst",
    admin_email: str = "analyst@tides.ai",
    admin_password: str = "password",
) -> Path:
    """Initialize schema and seed demo user on the dedicated development database."""
    dev_db_path = get_dev_db_path()
    workspace_db_path = (PROJECT_ROOT / "tides_ai.db").resolve()

    # Safety Guard: Never initialize against the workspace database
    if dev_db_path == workspace_db_path or dev_db_path.name.lower() == "tides_ai.db":
        raise RuntimeError(
            "FATAL: Attempted to initialize protected workspace database 'tides_ai.db'. "
            "Local development requires a dedicated database (e.g. 'tides_dev.db')."
        )

    # Set DATABASE_URL before importing app modules
    sqlite_url = f"sqlite:///{dev_db_path}"
    os.environ["DATABASE_URL"] = sqlite_url

    from app.core.config import get_settings
    get_settings.cache_clear()

    # Create tables
    from app.db.base import Base
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(sqlite_url, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with SessionLocal() as db:
        from app.modules.users.service import UserService
        user_service = UserService(db)
        user_service.ensure_default_roles()

        existing_user = user_service.users.get_by_email(admin_email)
        if not existing_user:
            user_service.bootstrap_admin(
                name=admin_name,
                email=admin_email,
                password=admin_password,
            )
            created = True
        else:
            created = False

    print("=" * 65)
    print("TIDES-AI: LOCAL DEVELOPMENT DATABASE INITIALIZED")
    print(f"Database File: {dev_db_path}")
    print(f"Status:        {'Created tables and demo user' if created else 'Tables verified, user exists'}")
    print("-" * 65)
    print(f"Demo Email:    {admin_email}")
    print(f"Demo Password: {admin_password}")
    print("NOTICE:        These credentials are for LOCAL DEVELOPMENT ONLY.")
    print("               Do not use these credentials in staging or production.")
    print("=" * 65)

    return dev_db_path


if __name__ == "__main__":
    init_dev_database()
