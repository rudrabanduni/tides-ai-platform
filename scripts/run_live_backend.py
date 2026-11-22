"""run_live_backend.py - Starts the FastAPI backend for LIVE (paid Claude) evaluations.

Started by scripts/start_live.ps1, which supplies ANTHROPIC_API_KEY through a hidden prompt.
Uses tides_live.db + uploads_live/ only. Budget ceiling: $0.60 per evaluation.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.live_instance import ensure_live_env, init_live_database, live_environment  # noqa: E402

EXPECTED_PROTECTED_SHA256 = "D9659F4E8C1058C5D5F4511E1BB22D3ABE6CB12101C16CE397416051A38176C7"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()

    if not (os.environ.get("ANTHROPIC_API_KEY") or "").strip():
        sys.stderr.write("FATAL: ANTHROPIC_API_KEY missing. Start live mode with scripts\\start_live.ps1.\n")
        sys.exit(1)

    protected = PROJECT_ROOT / "tides_ai.db"
    if protected.exists():
        digest = hashlib.sha256(protected.read_bytes()).hexdigest().upper()
        print(f"Protected tides_ai.db: {'UNCHANGED' if digest == EXPECTED_PROTECTED_SHA256 else 'HASH MISMATCH'}")

    values = ensure_live_env()
    init_live_database()
    os.environ.update(live_environment(values))
    from app.core.config import get_settings

    get_settings.cache_clear()
    s = get_settings()
    assert s.ai_provider == "anthropic" and s.allow_ui_live_evaluations
    assert "tides_live.db" in s.database_url
    print("=" * 66)
    print(" TIDES-AI LIVE EVALUATION BACKEND  (paid Claude API calls)")
    print("=" * 66)
    print(f" Database:   {s.database_url}")
    print(f" Models:     extraction {s.ai_fast_model} | specialists & review {s.ai_reasoning_model}")
    print(f" Budget:     ${s.ai_max_evaluation_budget_usd:.2f} per evaluation (hard ceiling)")
    print(f" Thinking:   {s.ai_structured_thinking_mode}")
    print(f" API:        http://{args.host}:{args.port}")
    print("=" * 66)

    import uvicorn

    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=False, log_level="info")


if __name__ == "__main__":
    main()
