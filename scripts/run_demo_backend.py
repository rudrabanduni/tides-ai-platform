"""run_demo_backend.py - Starts the FastAPI backend for the OFFLINE stakeholder demonstration.

Isolated database (tides_demo.db), isolated uploads (uploads_demo/), MockAIGateway only,
no provider keys in the process environment, live-provider runs disabled in the web app.

Usage:
    .venv\\Scripts\\python.exe scripts\\run_demo_backend.py [--host 127.0.0.1] [--port 8000]
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.init_demo_db import demo_environment, ensure_demo_env, init_demo_database  # noqa: E402

PROTECTED_DB = PROJECT_ROOT / "tides_ai.db"
EXPECTED_PROTECTED_SHA256 = "D9659F4E8C1058C5D5F4511E1BB22D3ABE6CB12101C16CE397416051A38176C7"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()

    if PROTECTED_DB.exists():
        actual = _sha256(PROTECTED_DB)
        status = "UNCHANGED" if actual == EXPECTED_PROTECTED_SHA256 else "HASH MISMATCH - INVESTIGATE"
        print(f"Protected tides_ai.db SHA-256: {actual} ({status})")

    values = ensure_demo_env()
    init_demo_database(reset=False)
    os.environ.update(demo_environment(values))
    from app.core.config import get_settings

    get_settings.cache_clear()
    s = get_settings()
    assert s.ai_provider == "mock" and not s.allow_ui_live_evaluations, "demo must run in mock mode"
    assert "tides_demo.db" in s.database_url, "demo must use tides_demo.db"
    print("=" * 66)
    print(" TIDES-AI OFFLINE STAKEHOLDER DEMONSTRATION BACKEND")
    print(" MOCK DEMONSTRATION - OFFLINE SYNTHETIC RESULTS - NOT A REAL AI EVALUATION")
    print("=" * 66)
    print(f" Database:   {s.database_url}")
    print(f" Uploads:    {s.upload_dir}")
    print(f" Provider:   {s.ai_provider} (live UI evaluations disabled)")
    print(f" API:        http://{args.host}:{args.port}   docs: http://{args.host}:{args.port}/docs")
    print("=" * 66)

    import uvicorn

    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=False, log_level="info")


if __name__ == "__main__":
    main()
