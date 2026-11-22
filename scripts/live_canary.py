"""live_canary.py - Two tiny paid calls that prove the live Claude path works before any evaluation.

Run automatically by scripts/start_live.ps1. Needs ANTHROPIC_API_KEY in the process environment
(never pass it on the command line). Cost: well under $0.01 in total (hard ledger cap $0.02).

For each model (Haiku 5.5 for extraction, Sonnet 5.5 for the specialists) it sends one short JSON
request with the structured-output thinking setting and checks: request accepted, finish_reason
"stop", output well below max_tokens, valid JSON, exactly one ledger row. If the provider rejects
the thinking setting, it retries ONCE with the "low_effort" fallback for that model.

Writes the working setting to logs/live_canary.json; prints AI_STRUCTURED_THINKING_MODE=<value>.
Exit code 0 = live path verified, 1 = not usable (nothing else is started).
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pydantic import BaseModel, Field  # noqa: E402

from scripts.live_instance import ensure_live_env, live_environment  # noqa: E402


class CanaryAnswer(BaseModel):
    company: str = Field(..., description="Company name from the text")
    sector: str = Field(..., description="Sector from the text")
    stage: str = Field(..., description="Stage from the text")


SYSTEM = "You extract facts from startup application text. Answer only with the requested JSON."
USER = "Application text: 'Company: Canary Labs Pvt Ltd. Sector: CleanTech. Stage: Seed.' Return company, sector and stage."


def _one_call(model: str, mode: str) -> dict:
    os.environ["AI_STRUCTURED_THINKING_MODE"] = mode
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.services.ai.cost_ledger import CostLedgerManager
    from app.services.ai.litellm import LiteLLMGateway, resolve_structured_output_thinking_kwargs
    from app.services.ai.schemas import AICompletionRequest

    eval_id = f"canary-{uuid.uuid4().hex[:8]}"
    ledger = CostLedgerManager.get_instance().get_or_create_ledger(evaluation_id=eval_id, max_budget_usd=0.02)
    gw = LiteLLMGateway(model=model, timeout=60, max_retries=0, api_key=os.environ.get("ANTHROPIC_API_KEY"))
    req = AICompletionRequest(
        system_prompt=SYSTEM,
        user_prompt=USER,
        model=model,
        evaluation_id=eval_id,
        agent_name=f"live_canary_{model}",
        operation_type="extraction",
        max_output_tokens=200,
        metadata={"operation_id": f"op_canary_{uuid.uuid4().hex[:8]}"},
    )
    result: dict = {"model": model, "mode": mode, "thinking_kwargs": resolve_structured_output_thinking_kwargs(model, mode)}
    try:
        res = gw.complete_json(req, CanaryAnswer)
        ops = ledger.get_summary()["operations"]
        result.update({
            "ok": True,
            "answer": res.data.model_dump(),
            "output_tokens": res.metadata.output_tokens,
            "input_tokens": res.metadata.input_tokens,
            "cost_usd": res.metadata.cost_usd,
            "finish_reason": ops[-1].get("finish_reason") if ops else None,
            "ledger_rows": len(ops),
        })
        result["ok"] = bool(
            result["finish_reason"] in ("stop", "end_turn")
            and (res.metadata.output_tokens or 0) < 150
            and result["ledger_rows"] == 1
            and res.data.company.lower().startswith("canary")
        )
    except Exception as exc:  # report only the error class and a short, key-free message
        msg = str(exc)
        key = os.environ.get("ANTHROPIC_API_KEY") or ""
        if key:
            msg = msg.replace(key, "[redacted]")
        result.update({"ok": False, "error": f"{type(exc).__name__}: {msg[:300]}",
                       "spent_usd": ledger.spent_usd})
    return result


def main() -> int:
    if not (os.environ.get("ANTHROPIC_API_KEY") or "").strip():
        print("CANARY FAILED: ANTHROPIC_API_KEY is not set in this process.")
        return 1
    values = ensure_live_env()
    env = live_environment(values)
    for k, v in env.items():
        if k != "AI_STRUCTURED_THINKING_MODE":
            os.environ[k] = v

    chosen: dict[str, str] = {}
    report = {"at": datetime.now(timezone.utc).isoformat(), "calls": []}
    for family, model in (("haiku", env["AI_FAST_MODEL"]), ("sonnet", env["AI_REASONING_MODEL"])):
        r = _one_call(model, "off")
        report["calls"].append(r)
        if not r["ok"] and "error" in r and ("thinking" in r["error"].lower() or "400" in r["error"]):
            r2 = _one_call(model, "low_effort")
            report["calls"].append(r2)
            r = r2
        if not r["ok"]:
            report["result"] = "FAILED"
            _write(report)
            print(f"CANARY FAILED for {model}: {r.get('error') or r}")
            return 1
        chosen[family] = r["mode"]

    mode = "off" if set(chosen.values()) == {"off"} else ",".join(f"{k}={v}" for k, v in chosen.items())
    report.update({"result": "PASSED", "structured_thinking_mode": mode,
                   "total_cost_usd": round(sum(c.get("cost_usd") or 0 for c in report["calls"]), 6)})
    _write(report)
    for c in report["calls"]:
        print(f"  {c['model']:<18} mode={c['mode']:<10} ok={c['ok']} out_tokens={c.get('output_tokens')} "
              f"finish={c.get('finish_reason')} cost=${c.get('cost_usd') or 0:.6f}")
    print(f"CANARY PASSED (total ${report['total_cost_usd']:.6f})")
    print(f"AI_STRUCTURED_THINKING_MODE={mode}")
    return 0


def _write(report: dict) -> None:
    out = PROJECT_ROOT / "logs" / "live_canary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
