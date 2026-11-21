"""Unified cost ledger and budget management system for AI evaluations.

Enforces:
- Hard provider ceiling: $0.35 USD per evaluation (default, with explicit override support).
- Target business cost: ₹50–₹60 INR (with absolute buffered ceiling <= ₹70 INR).
- Pre-call estimation and budget reservation shared across concurrent agent calls.
- Per-operation cost reconciliation, latency tracking, retry tracking, and token telemetry.
"""

from __future__ import annotations

import logging
import math
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.services.ai.exceptions import AIBudgetExhaustedError
from app.services.ai.pricing import PricingCatalog, get_pricing_catalog

logger = logging.getLogger(__name__)


@dataclass
class CostRecord:
    """Detailed record of a single billable or metered AI provider operation."""

    operation_id: str
    evaluation_id: str
    startup_id: str | None
    agent_name: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cached_tokens: int
    cache_write_tokens: int
    cache_write_5m_tokens: int
    cache_write_1h_tokens: int
    cache_write_ttl: str
    actual_cost_usd: float | None
    estimated_cost_usd: float
    final_cost_usd: float
    cost_inr: float
    buffered_cost_inr: float
    external_tools_cost_usd: float
    retry_count: int
    latency_ms: float
    status: str  # SUCCESS, FAILED, RETRY, PARTIAL
    confidence: str  # EXACT_REPORTED, ESTIMATED_FROM_TOKENS, RESERVED
    pricing_version: str
    finish_reason: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ActiveReservation:
    """Represents a temporary budget reservation for an in-flight AI operation."""

    reservation_id: str
    agent_name: str
    estimated_cost_usd: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EvaluationCostLedger:
    """Thread-safe unified cost ledger and budget policy manager for a single evaluation."""

    def __init__(
        self,
        evaluation_id: str,
        startup_id: str | None = None,
        max_budget_usd: float = 0.35,
        exchange_rate: float = 96.0,
        buffer_multiplier: float = 1.18,
        pricing_catalog: PricingCatalog | None = None,
    ) -> None:
        self.evaluation_id = evaluation_id
        self.startup_id = startup_id
        self.max_budget_usd = max_budget_usd
        self.exchange_rate = exchange_rate
        self.buffer_multiplier = buffer_multiplier
        self.pricing_catalog = pricing_catalog or get_pricing_catalog()

        self._lock = threading.RLock()
        self._records: list[CostRecord] = []
        self._operations_by_id: dict[str, CostRecord] = {}
        self._reservations: dict[str, ActiveReservation] = {}
        self._total_spent_usd: float = 0.0
        self._is_exhausted: bool = False
        self._exhaustion_reason: str | None = None

    @property
    def spent_usd(self) -> float:
        """Total reconciled expenditure in USD."""
        with self._lock:
            return round(self._total_spent_usd, 6)

    @property
    def reserved_usd(self) -> float:
        """Total currently reserved in-flight budget in USD."""
        with self._lock:
            return round(sum(r.estimated_cost_usd for r in self._reservations.values()), 6)

    @property
    def remaining_budget_usd(self) -> float:
        """Remaining uncommitted budget in USD."""
        with self._lock:
            committed = self._total_spent_usd + self.reserved_usd
            return max(0.0, round(self.max_budget_usd - committed, 6))

    @property
    def is_exhausted(self) -> bool:
        with self._lock:
            return self._is_exhausted

    @property
    def exhaustion_reason(self) -> str | None:
        with self._lock:
            return self._exhaustion_reason

    def reserve_budget(
        self,
        estimated_cost_usd: float,
        agent_name: str = "unknown",
    ) -> str:
        """Estimates and reserves budget prior to making an AI provider call.

        Thread-safe: Prevents concurrent operations from exceeding the shared ceiling.
        Raises AIBudgetExhaustedError if the planned cost exceeds the remaining budget.
        """
        with self._lock:
            if not math.isfinite(estimated_cost_usd) or estimated_cost_usd < 0.0:
                raise ValueError(f"Invalid non-finite or negative estimated cost: {estimated_cost_usd}")
            if self._is_exhausted:
                raise AIBudgetExhaustedError(
                    f"Budget exhausted for evaluation '{self.evaluation_id}'. "
                    f"Spent: ${self._total_spent_usd:.4f}, Limit: ${self.max_budget_usd:.4f}. "
                    f"Reason: {self._exhaustion_reason or 'Hard ceiling reached'}"
                )

            committed = round(self._total_spent_usd + self.reserved_usd, 6)
            projected = round(committed + estimated_cost_usd, 6)

            if projected > round(self.max_budget_usd, 6):
                self._is_exhausted = True
                self._exhaustion_reason = (
                    f"Planned operation '{agent_name}' requiring ${estimated_cost_usd:.4f} "
                    f"would exceed budget ceiling (${committed:.4f} + ${estimated_cost_usd:.4f} = "
                    f"${projected:.4f} > ${self.max_budget_usd:.4f})."
                )
                logger.warning(
                    f"[BUDGET EXHAUSTED] {self._exhaustion_reason} "
                    f"(Evaluation ID: {self.evaluation_id})"
                )
                raise AIBudgetExhaustedError(self._exhaustion_reason)

            reservation_id = f"res_{uuid.uuid4().hex[:12]}"
            self._reservations[reservation_id] = ActiveReservation(
                reservation_id=reservation_id,
                agent_name=agent_name,
                estimated_cost_usd=round(estimated_cost_usd, 6),
            )
            return reservation_id

    def release_reservation(self, reservation_id: str) -> None:
        """Releases an in-flight reservation (e.g. if an operation was aborted or cancelled)."""
        with self._lock:
            self._reservations.pop(reservation_id, None)

    def has_operation(self, operation_id: str) -> bool:
        """Returns True if an operation with the given ID has already been reconciled."""
        normalized = operation_id.strip() if isinstance(operation_id, str) else ""
        if not normalized:
            return False
        with self._lock:
            return normalized in self._operations_by_id

    def reconcile_operation(
        self,
        reservation_id: str | None,
        agent_name: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0,
        cache_write_tokens: int = 0,
        cache_write_5m_tokens: int = 0,
        cache_write_1h_tokens: int = 0,
        cache_write_ttl: str | None = None,
        actual_cost_usd: float | None = None,
        external_tools_cost_usd: float = 0.0,
        retry_count: int = 0,
        latency_ms: float = 0.0,
        status: str = "SUCCESS",
        confidence: str | None = None,
        finish_reason: str | None = None,
        operation_id: str | None = None,
    ) -> CostRecord:
        """Reconciles an in-flight reservation with actual token usage and reported/calculated cost."""
        with self._lock:
            if actual_cost_usd is not None and (not math.isfinite(actual_cost_usd) or actual_cost_usd < 0.0):
                raise ValueError(f"Invalid non-finite or negative actual_cost_usd: {actual_cost_usd}")
            # 1. Release the reservation
            if reservation_id and reservation_id in self._reservations:
                self._reservations.pop(reservation_id, None)

            # 1b. Idempotency guard: never double-charge a repeated operation_id
            resolved_op_id = operation_id.strip() if isinstance(operation_id, str) and operation_id.strip() else None
            if resolved_op_id and resolved_op_id in self._operations_by_id:
                existing = self._operations_by_id[resolved_op_id]
                logger.info(
                    f"[COST IDEMPOTENT] Duplicate reconciliation ignored for operation_id='{resolved_op_id}' "
                    f"(Agent: {agent_name})"
                )
                return existing

            # 2. Determine final USD cost with explicit TTL pricing
            if input_tokens > 0 or output_tokens > 0 or cached_tokens > 0 or cache_write_tokens > 0:
                calculated_cost = self.pricing_catalog.calculate_cost(
                    model=model,
                    prompt_tokens=input_tokens,
                    completion_tokens=output_tokens,
                    cached_tokens=cached_tokens,
                    cache_write_tokens=cache_write_tokens,
                    cache_write_5m_tokens=cache_write_5m_tokens,
                    cache_write_1h_tokens=cache_write_1h_tokens,
                    cache_write_ttl=cache_write_ttl,
                )
            else:
                calculated_cost = 0.0

            if confidence is not None:
                final_cost_usd = round((actual_cost_usd if actual_cost_usd is not None and actual_cost_usd > 0.0 else calculated_cost) + external_tools_cost_usd, 6)
                resolved_confidence = confidence
            elif actual_cost_usd is not None and actual_cost_usd > 0.0:
                final_cost_usd = round(actual_cost_usd + external_tools_cost_usd, 6)
                resolved_confidence = "EXACT_REPORTED"
            else:
                final_cost_usd = round(calculated_cost + external_tools_cost_usd, 6)
                resolved_confidence = "ESTIMATED_FROM_TOKENS"

            # 3. Currency conversion
            cost_inr, buffered_cost_inr = self.pricing_catalog.convert_to_inr(
                cost_usd=final_cost_usd,
                exchange_rate=self.exchange_rate,
                buffer_multiplier=self.buffer_multiplier,
            )

            op_id = resolved_op_id or f"op_{uuid.uuid4().hex[:12]}"
            record = CostRecord(
                operation_id=op_id,
                evaluation_id=self.evaluation_id,
                startup_id=self.startup_id,
                agent_name=agent_name,
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cached_tokens=cached_tokens,
                cache_write_tokens=cache_write_tokens,
                cache_write_5m_tokens=cache_write_5m_tokens,
                cache_write_1h_tokens=cache_write_1h_tokens,
                cache_write_ttl=cache_write_ttl or "conservative",
                actual_cost_usd=actual_cost_usd,
                estimated_cost_usd=calculated_cost,
                final_cost_usd=final_cost_usd,
                cost_inr=cost_inr,
                buffered_cost_inr=buffered_cost_inr,
                external_tools_cost_usd=external_tools_cost_usd,
                retry_count=retry_count,
                latency_ms=latency_ms,
                status=status,
                confidence=resolved_confidence,
                pricing_version=self.pricing_catalog.version,
                finish_reason=finish_reason,
            )

            self._records.append(record)
            self._operations_by_id[op_id] = record
            self._total_spent_usd = round(self._total_spent_usd + final_cost_usd, 6)

            # 4. Check if expenditure breached ceiling
            if self._total_spent_usd >= round(self.max_budget_usd, 6):
                self._is_exhausted = True
                self._exhaustion_reason = (
                    f"Cumulative evaluation expenditure (${self._total_spent_usd:.4f}) "
                    f"has reached or exceeded the ceiling (${self.max_budget_usd:.4f})."
                )

            logger.info(
                f"[COST RECORD] Agent: {agent_name} | Model: {model} | "
                f"In: {input_tokens} (Cached: {cached_tokens}) | Out: {output_tokens} | "
                f"Cost: ${final_cost_usd:.6f} (~₹{buffered_cost_inr:.2f}) | "
                f"Cumul: ${self._total_spent_usd:.4f} / ${self.max_budget_usd:.4f}"
            )
            return record

    def restore_from_summary(self, summary: dict[str, Any]) -> None:
        """Restores ledger state and historical operation records from a prior run summary.

        Ensures cumulative expenditure, operation history, and remaining budget headroom
        are preserved across process boundaries during evaluation recovery without resetting.
        """
        with self._lock:
            self._records.clear()
            self._operations_by_id.clear()
            self._reservations.clear()

            # Restore historical operation records
            for op in summary.get("operations", []):
                record = CostRecord(
                    operation_id=op.get("operation_id", f"op_{uuid.uuid4().hex[:12]}"),
                    evaluation_id=self.evaluation_id,
                    startup_id=self.startup_id,
                    agent_name=op.get("agent_name", "unknown"),
                    provider="anthropic",
                    model=op.get("model", "unknown"),
                    input_tokens=op.get("input_tokens", 0),
                    output_tokens=op.get("output_tokens", 0),
                    cached_tokens=op.get("cached_tokens", 0),
                    cache_write_tokens=op.get("cache_write_tokens", 0),
                    cache_write_5m_tokens=op.get("cache_write_5m_tokens", 0),
                    cache_write_1h_tokens=op.get("cache_write_1h_tokens", 0),
                    cache_write_ttl=op.get("cache_write_ttl", "none"),
                    actual_cost_usd=op.get("final_cost_usd"),
                    estimated_cost_usd=op.get("final_cost_usd", 0.0),
                    final_cost_usd=op.get("final_cost_usd", 0.0),
                    cost_inr=op.get("final_cost_usd", 0.0) * self.exchange_rate,
                    buffered_cost_inr=op.get("buffered_cost_inr", 0.0),
                    external_tools_cost_usd=0.0,
                    retry_count=0,
                    latency_ms=0.0,
                    status=op.get("status", "SUCCESS"),
                    confidence=op.get("confidence", "EXACT_REPORTED"),
                    pricing_version=summary.get("pricing_version", self.pricing_catalog.version),
                    finish_reason=op.get("finish_reason"),
                )
                self._records.append(record)
                self._operations_by_id[record.operation_id] = record

            # Restore spent amount
            reported_spent = summary.get("total_spent_usd")
            if reported_spent is not None:
                self._total_spent_usd = round(float(reported_spent), 6)
            else:
                self._total_spent_usd = round(sum(r.final_cost_usd for r in self._records), 6)

            # Check if budget was already exhausted
            if self._total_spent_usd >= round(self.max_budget_usd, 6):
                self._is_exhausted = True
                self._exhaustion_reason = f"Prior spend (${self._total_spent_usd:.4f}) meets or exceeds budget ceiling (${self.max_budget_usd:.4f})"
            else:
                self._is_exhausted = bool(summary.get("is_exhausted", False))
                self._exhaustion_reason = summary.get("exhaustion_reason")

            logger.info(
                f"[LEDGER RESTORE] Restored ledger for evaluation '{self.evaluation_id}'. "
                f"Historical ops: {len(self._records)} | Prior spend: ${self._total_spent_usd:.6f} | "
                f"Remaining budget: ${self.remaining_budget_usd:.6f}"
            )

    def get_summary(self) -> dict[str, Any]:
        """Returns comprehensive evaluation-wide cost summary and telemetry."""
        with self._lock:
            total_input_tokens = sum(r.input_tokens for r in self._records)
            total_output_tokens = sum(r.output_tokens for r in self._records)
            total_cached_tokens = sum(r.cached_tokens for r in self._records)
            total_cache_write_tokens = sum(r.cache_write_tokens for r in self._records)
            total_cache_write_5m_tokens = sum(r.cache_write_5m_tokens for r in self._records)
            total_cache_write_1h_tokens = sum(r.cache_write_1h_tokens for r in self._records)
            total_tokens = total_input_tokens + total_output_tokens
            total_latency_ms = sum(r.latency_ms for r in self._records)
            total_retries = sum(r.retry_count for r in self._records)
            total_external_tools = sum(r.external_tools_cost_usd for r in self._records)

            total_cost_usd = round(self._total_spent_usd, 6)
            total_cost_inr, total_buffered_cost_inr = self.pricing_catalog.convert_to_inr(
                cost_usd=total_cost_usd,
                exchange_rate=self.exchange_rate,
                buffer_multiplier=self.buffer_multiplier,
            )

            # Target checks
            is_within_target_inr = 50.0 <= total_buffered_cost_inr <= 60.0
            is_under_max_inr = total_buffered_cost_inr <= 70.0
            is_under_max_usd = total_cost_usd <= self.max_budget_usd

            # Cost confidence assessment
            any_unverified = any(r.confidence == "UNVERIFIED_ESTIMATE" for r in self._records)
            all_exact = bool(self._records) and all(r.confidence == "EXACT_REPORTED" for r in self._records)
            if any_unverified or not self._records:
                overall_confidence = "UNVERIFIED_ESTIMATE" if any_unverified else "NO_OPERATIONS"
            elif all_exact:
                overall_confidence = "EXACT_REPORTED"
            else:
                overall_confidence = "ESTIMATED_FROM_TOKENS"

            return {
                "evaluation_id": self.evaluation_id,
                "startup_id": self.startup_id,
                "total_operations": len(self._records),
                "total_spent_usd": total_cost_usd,
                "cost_confidence": overall_confidence,
                "max_budget_usd": self.max_budget_usd,
                "remaining_budget_usd": self.remaining_budget_usd,
                "reserved_in_flight_usd": self.reserved_usd,
                "total_cost_inr_raw": total_cost_inr,
                "total_cost_inr_buffered": total_buffered_cost_inr,
                "exchange_rate": self.exchange_rate,
                "buffer_multiplier": self.buffer_multiplier,
                "estimated_provider_charge_usd": total_cost_usd,
                "estimated_provider_charge_inr": total_cost_inr,
                "estimated_tax_and_fees_inr": round(total_buffered_cost_inr - total_cost_inr, 4),
                "final_billed_inr": total_buffered_cost_inr,
                "is_exhausted": self._is_exhausted,
                "exhaustion_reason": self._exhaustion_reason,
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "total_cached_tokens": total_cached_tokens,
                "total_cache_write_tokens": total_cache_write_tokens,
                "total_cache_write_5m_tokens": total_cache_write_5m_tokens,
                "total_cache_write_1h_tokens": total_cache_write_1h_tokens,
                "total_tokens": total_tokens,
                "total_retries": total_retries,
                "total_external_tools_usd": total_external_tools,
                "total_latency_ms": round(total_latency_ms, 2),
                "pricing_version": self.pricing_catalog.version,
                "cache_pricing_policy": "conservative_1h",
                "within_target_inr": is_within_target_inr,
                "under_max_inr_ceiling": is_under_max_inr,
                "under_max_usd_ceiling": is_under_max_usd,
                "operations": [
                    {
                        "operation_id": r.operation_id,
                        "agent_name": r.agent_name,
                        "model": r.model,
                        "input_tokens": r.input_tokens,
                        "output_tokens": r.output_tokens,
                        "cached_tokens": r.cached_tokens,
                        "cache_write_tokens": r.cache_write_tokens,
                        "cache_write_5m_tokens": r.cache_write_5m_tokens,
                        "cache_write_1h_tokens": r.cache_write_1h_tokens,
                        "cache_write_ttl": r.cache_write_ttl,
                        "final_cost_usd": r.final_cost_usd,
                        "buffered_cost_inr": r.buffered_cost_inr,
                        "confidence": r.confidence,
                        "status": r.status,
                        "finish_reason": r.finish_reason,
                    }
                    for r in self._records
                ],
            }


class CostLedgerManager:
    """Global thread-safe registry of EvaluationCostLedger instances."""

    _instance: CostLedgerManager | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._ledgers: dict[str, EvaluationCostLedger] = {}
        self._registry_lock = threading.RLock()

    @classmethod
    def get_instance(cls) -> CostLedgerManager:
        with cls._lock:
            if cls._instance is None:
                cls._instance = CostLedgerManager()
            return cls._instance

    def get_or_create_ledger(
        self,
        evaluation_id: str,
        startup_id: str | None = None,
        max_budget_usd: float | None = None,
        exchange_rate: float | None = None,
        buffer_multiplier: float | None = None,
    ) -> EvaluationCostLedger:
        """Retrieves existing evaluation ledger or initializes a new one."""
        with self._registry_lock:
            if evaluation_id not in self._ledgers:
                from app.core.config import get_settings

                settings = get_settings()
                if max_budget_usd is not None:
                    budget = max_budget_usd
                elif (
                    "ai_max_evaluation_budget" in getattr(settings, "model_fields_set", set())
                    and "ai_max_evaluation_budget_usd" not in getattr(settings, "model_fields_set", set())
                ):
                    budget = settings.ai_max_evaluation_budget
                else:
                    budget = getattr(settings, "ai_max_evaluation_budget_usd", 0.35)
                rate = (
                    exchange_rate
                    if exchange_rate is not None
                    else getattr(settings, "ai_inr_exchange_rate", 96.0)
                )
                buf = (
                    buffer_multiplier
                    if buffer_multiplier is not None
                    else getattr(settings, "ai_inr_buffer_multiplier", 1.18)
                )

                self._ledgers[evaluation_id] = EvaluationCostLedger(
                    evaluation_id=evaluation_id,
                    startup_id=startup_id,
                    max_budget_usd=budget,
                    exchange_rate=rate,
                    buffer_multiplier=buf,
                )
            elif max_budget_usd is not None:
                existing = self._ledgers[evaluation_id]
                with existing._lock:
                    if max_budget_usd < existing.max_budget_usd:
                        existing.max_budget_usd = max_budget_usd
            return self._ledgers[evaluation_id]

    def get_ledger(self, evaluation_id: str) -> EvaluationCostLedger | None:
        with self._registry_lock:
            return self._ledgers.get(evaluation_id)

    def clear_ledger(self, evaluation_id: str) -> None:
        with self._registry_lock:
            self._ledgers.pop(evaluation_id, None)

    def clear_all(self) -> None:
        with self._registry_lock:
            self._ledgers.clear()
