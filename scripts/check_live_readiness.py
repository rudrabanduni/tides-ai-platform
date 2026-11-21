"""scripts/check_live_readiness.py - Non-Destructive Live Readiness Checker.

Reads active runtime configuration and pricing catalog to output the live-readiness checklist.
Does NOT make any network calls or validate credentials against remote APIs.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.ai.readiness import get_live_readiness_report


def main() -> None:
    report = get_live_readiness_report()

    print("=" * 72)
    print("  TIDES-AI PLATFORM: DYNAMIC LIVE-READINESS CHECKLIST")
    print("=" * 72)
    print(f"Overall Status: {report['status']}\n")

    print("[1] ACTIVE RUNTIME MODELS & ROUTING:")
    fast = report["models"]["fast_extraction"]
    print(f"  - Extraction (Fast Model):     {fast['model_id']}")
    print(f"    Active: {fast['is_active']} | Deprecated: {fast['is_deprecated']}")
    print(f"    Pricing: ${fast['input_cost_per_m']:.2f} in / ${fast['output_cost_per_m']:.2f} out per MTok")

    reasoning = report["models"]["reasoning_review"]
    print(f"  - Reasoning & Review Model:    {reasoning['model_id']}")
    print(f"    Active: {reasoning['is_active']} | Deprecated: {reasoning['is_deprecated']}")
    print(f"    Pricing: ${reasoning['input_cost_per_m']:.2f} in / ${reasoning['output_cost_per_m']:.2f} out per MTok")

    print(f"  - Gateway Default Model:       {report['models']['gateway_default']}")

    print("\n[2] BUDGET & CURRENCY CONTROLS:")
    b = report["budget"]
    print(f"  - Evaluation Budget Ceiling:   ${b['max_budget_usd']:.2f} USD")
    print(f"  - INR Conversion Rate:         {b['exchange_rate']:.1f} INR/USD")
    print(f"  - Buffered INR Total:          INR {b['buffered_inr']:.2f}")
    print(f"  - Hard Business Ceiling:       INR {b['hard_ceiling_inr']:.2f}")
    print(f"  - Mathematical Guarantee:      {'PASSED (<= INR 70.0)' if b['mathematically_guaranteed'] else 'FAILED'}")

    print("\n[3] RESEARCH PROVIDER:")
    r = report["research"]
    print(f"  - Active Provider:             {r['provider']}")
    print(f"  - Max Queries Per Eval:        {r['max_queries']}")
    print(f"  - Cost Per Credit:             ${r['cost_per_query_usd']:.3f} USD")

    print("\n[4] CREDENTIAL STATUS (NON-LEAKING):")
    c = report["credentials"]
    print(f"  - ANTHROPIC_API_KEY Configured: {'YES' if c['anthropic_key_present'] else 'NO (Safe Offline Mode)'}")
    print(f"  - TAVILY_API_KEY Configured:    {'YES' if c['tavily_key_present'] else 'NO'}")

    print("\n[5] VERIFICATION CHECKS SUMMARY:")
    for check in report["checks"]:
        print(f"  [{check['status']}] {check['name']}")

    print("\n" + "=" * 72)
    if report["status"] == "READY_FOR_CREDENTIALS":
        print("PLATFORM STATUS: All models and budget controls verified.")
        print("Awaiting user approval and ANTHROPIC_API_KEY to conduct first live evaluation.")
    elif report["status"] == "READY_FOR_LIVE_EVALUATION":
        print("PLATFORM STATUS: Ready for live evaluation with operator authorization.")
    print("=" * 72)


if __name__ == "__main__":
    main()
