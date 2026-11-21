"""run_dev_backend.py - Safe Local Development Backend Runner (Mock Mode).

Starts the TIDES-AI FastAPI backend bound to 127.0.0.1:8000 using:
- A dedicated, gitignored development database (tides_dev.db)
- Supported offline mock AI provider (AI_PROVIDER=mock, zero external API calls)
- Guaranteed fail-closed protection: refuses to run against protected tides_ai.db
- Automatic schema & local demo user initialization (analyst@tides.ai / password)

Usage:
    python scripts/run_dev_backend.py [--host 127.0.0.1] [--port 8000] [--reload]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.init_dev_db import init_dev_database, get_dev_db_path
from app.core.config import resolve_sqlite_db_path, PROTECTED_SNAPSHOT_DB_NAME


def run_dev_server() -> None:
    parser = argparse.ArgumentParser(description="TIDES-AI Local Development Server (Mock Mode)")
    parser.add_argument("--host", default="127.0.0.1", help="Binding interface (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for local code iteration")
    args = parser.parse_args()

    workspace_db_path = (PROJECT_ROOT / "tides_ai.db").resolve()
    dev_db_path = get_dev_db_path()

    # Fail-closed guard: NEVER allow connecting to or mutating the workspace database
    existing_db_url = os.environ.get("DATABASE_URL", "")
    if existing_db_url:
        resolved_existing = resolve_sqlite_db_path(existing_db_url, base_dir=PROJECT_ROOT)
        if (
            PROTECTED_SNAPSHOT_DB_NAME in existing_db_url.lower()
            or resolved_existing == workspace_db_path
            or (resolved_existing is not None and resolved_existing.name.lower() == PROTECTED_SNAPSHOT_DB_NAME)
        ):
            sys.stderr.write(
                "\n[FATAL ERROR] DATABASE_URL points to the protected workspace database 'tides_ai.db'.\n"
                "Local development mode requires a dedicated dev database to preserve audit integrity.\n"
                f"Please unset DATABASE_URL or set it to 'sqlite:///{dev_db_path}'.\n\n"
            )
            sys.exit(1)

    # Force isolated development database
    sqlite_url = f"sqlite:///{dev_db_path}"
    os.environ["DATABASE_URL"] = sqlite_url

    # Force mock AI provider (no live Anthropic API calls)
    os.environ["AI_PROVIDER"] = "mock"
    os.environ["AI_ENABLED"] = "true"
    os.environ["APP_ENV"] = "development"
    os.environ.setdefault("RESEARCH_PROVIDER", "mock")

    # Initialize schema & demo user if not already present
    init_dev_database()

    # Reload settings with development environment variables
    from app.core.config import get_settings
    get_settings.cache_clear()
    settings = get_settings()

    print("\n" + "=" * 65)
    print(" TIDES-AI LOCAL DEVELOPMENT SERVER (MOCK MODE)")
    print("=" * 65)
    print(f" Database URL:   {settings.database_url}")
    print(f" AI Provider:    {settings.ai_provider} (AI_ENABLED={settings.ai_enabled})")
    print(f" Bound Host:     http://{args.host}:{args.port}")
    print(f" API Docs:       http://{args.host}:{args.port}/docs")
    print("-" * 65)
    print(" Local Demo Login: analyst@tides.ai / password")
    print(" NOTICE:           These credentials are for LOCAL DEVELOPMENT ONLY.")
    print("                   Do NOT use in staging or production.")
    print("=" * 65 + "\n")

    import uvicorn
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    run_dev_server()
