"""progress.py - Context-scoped evaluation progress reporting.

The evaluation pipeline calls `report_progress(...)` at real stage transitions. When an
evaluation run is executing (see `app.modules.applications.runner`), a reporter bound to that
run persists every event to the `evaluation_runs` row, so the UI shows progress read from the
database instead of a simulated progress bar. Outside a run (tests, CLI) the call is a no-op.
"""

from __future__ import annotations

import contextvars
import logging
from typing import Any, Callable, Protocol

logger = logging.getLogger(__name__)


class ProgressReporter(Protocol):
    def __call__(self, stage: str, status: str, detail: dict[str, Any] | None = None) -> None: ...


_current_reporter: contextvars.ContextVar[Callable[..., None] | None] = contextvars.ContextVar(
    "tides_progress_reporter", default=None
)


def bind_progress_reporter(reporter: Callable[..., None] | None) -> contextvars.Token:
    return _current_reporter.set(reporter)


def reset_progress_reporter(token: contextvars.Token) -> None:
    _current_reporter.reset(token)


def report_progress(stage: str, status: str, detail: dict[str, Any] | None = None) -> None:
    """Emit a progress event. Never raises: progress reporting must not break an evaluation."""
    reporter = _current_reporter.get()
    if reporter is None:
        return
    try:
        reporter(stage, status, detail or {})
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Progress reporter failed for stage %s/%s: %s", stage, status, type(exc).__name__)
