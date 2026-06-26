"""
In-memory sliding-window rate limiter.

Performance target: rate-limit check < 2 ms.
Implementation: fixed-window counter with O(1) operations.

Two levels:
  – Global default : 200 req / 60 s per IP
  – Authenticated  : 1000 req / 60 s per user

The limiter stores counters in a thread-safe dict; no external cache required.
"""
from __future__ import annotations

import threading
import time
from collections import deque
from datetime import datetime, timezone

from app.security.schemas import RateLimitInfo


# ---------------------------------------------------------------------------
# Sliding-window bucket
# ---------------------------------------------------------------------------

class _WindowBucket:
    """Sliding-window request tracker for a single identifier."""

    def __init__(self, limit: int, window_seconds: float) -> None:
        self.limit = limit
        self.window = window_seconds
        self._timestamps: deque[float] = deque()

    def record_and_check(self) -> tuple[bool, int]:
        """Record a hit and return (is_limited, remaining).

        Returns True in is_limited when the count is at or above limit.
        """
        now = time.monotonic()
        cutoff = now - self.window

        # Evict old entries
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

        count = len(self._timestamps)

        if count >= self.limit:
            remaining = 0
            return True, remaining

        self._timestamps.append(now)
        remaining = self.limit - len(self._timestamps)
        return False, remaining

    def reset_at(self) -> datetime:
        """When the oldest request in the window will expire."""
        if self._timestamps:
            oldest = self._timestamps[0]
            reset_mono = oldest + self.window
            delta = reset_mono - time.monotonic()
            return datetime.fromtimestamp(
                time.time() + max(delta, 0), tz=timezone.utc
            )
        return datetime.now(timezone.utc)

    @property
    def remaining(self) -> int:
        now = time.monotonic()
        cutoff = now - self.window
        active = sum(1 for ts in self._timestamps if ts >= cutoff)
        return max(0, self.limit - active)


# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------

class RateLimiter:
    """Process-global sliding-window rate limiter.

    Usage::

        limiter = RateLimiter()
        is_limited, info = limiter.check("127.0.0.1")
        if is_limited:
            raise HTTPException(429, ...)
    """

    DEFAULT_LIMIT = 200
    DEFAULT_WINDOW = 60.0  # seconds
    AUTH_LIMIT = 1000
    AUTH_WINDOW = 60.0

    def __init__(self) -> None:
        self._buckets: dict[str, _WindowBucket] = {}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Core check
    # ------------------------------------------------------------------

    def check(
        self,
        identifier: str,
        limit: int | None = None,
        window_seconds: float | None = None,
    ) -> tuple[bool, RateLimitInfo]:
        """Check (and record) a request for *identifier*.

        Args:
            identifier: IP address, user_id, or api_key_name.
            limit: Optional override; defaults to DEFAULT_LIMIT.
            window_seconds: Optional override; defaults to DEFAULT_WINDOW.

        Returns:
            (is_limited, RateLimitInfo)
        """
        effective_limit = limit or self.DEFAULT_LIMIT
        effective_window = window_seconds or self.DEFAULT_WINDOW

        with self._lock:
            bucket = self._buckets.get(identifier)
            if bucket is None:
                bucket = _WindowBucket(effective_limit, effective_window)
                self._buckets[identifier] = bucket

            is_limited, remaining = bucket.record_and_check()
            reset_at = bucket.reset_at()

        info = RateLimitInfo(
            identifier=identifier,
            limit=effective_limit,
            remaining=remaining,
            reset_at=reset_at,
            is_limited=is_limited,
        )
        return is_limited, info

    def get_info(self, identifier: str) -> RateLimitInfo | None:
        """Return current rate-limit status without recording a hit."""
        with self._lock:
            bucket = self._buckets.get(identifier)
        if bucket is None:
            return None
        return RateLimitInfo(
            identifier=identifier,
            limit=bucket.limit,
            remaining=bucket.remaining,
            reset_at=bucket.reset_at(),
            is_limited=bucket.remaining == 0,
        )

    def reset(self, identifier: str) -> None:
        """Clear the bucket for *identifier* (useful in tests)."""
        with self._lock:
            self._buckets.pop(identifier, None)

    def reset_all(self) -> None:
        """Clear all buckets (useful in tests)."""
        with self._lock:
            self._buckets.clear()


# Module-level singleton
rate_limiter = RateLimiter()
