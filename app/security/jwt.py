"""
JWT service – wraps app.core.security with role claims, refresh tokens, blacklist, and performance tracking.

Performance target: create + decode operations < 5 ms each.
"""
from __future__ import annotations

import time
import uuid
import threading
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import get_settings
from app.security.schemas import TokenClaims, TokenData


class JWTService:
    """Thin, fast wrapper around python-jose with role embedding and refresh token support."""

    def __init__(self) -> None:
        settings = get_settings()
        self._secret = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        self._expire_minutes = settings.access_token_expire_minutes
        self._refresh_expire_days = 7
        self._blacklist: set[str] = set()
        self._blacklist_lock = threading.RLock()

    # ------------------------------------------------------------------
    # Token creation
    # ------------------------------------------------------------------

    def create_access_token(
        self,
        subject: str,
        role: str,
        extra_claims: dict[str, Any] | None = None,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a signed JWT access token embedding role + jti claims."""
        now = datetime.now(timezone.utc)
        expire = now + (expires_delta or timedelta(minutes=self._expire_minutes))
        payload: dict[str, Any] = {
            "sub": subject,
            "role": role,
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": expire,
            "type": "access",
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def create_refresh_token(
        self,
        subject: str,
        role: str,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a signed JWT refresh token."""
        now = datetime.now(timezone.utc)
        expire = now + (expires_delta or timedelta(days=self._refresh_expire_days))
        payload: dict[str, Any] = {
            "sub": subject,
            "role": role,
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": expire,
            "type": "refresh",
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    # ------------------------------------------------------------------
    # Token decoding
    # ------------------------------------------------------------------

    def decode_token(self, token: str) -> TokenClaims | None:
        """Decode and validate a JWT, returning structured claims.

        Includes clock skew handling (leeway=30s) and blacklist validation.
        """
        try:
            # Clock skew handling using leeway parameter
            raw = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
                options={"leeway": 30},
            )
        except JWTError:
            return None

        subject = raw.get("sub")
        role = raw.get("role", "viewer")
        jti = raw.get("jti", "")
        exp_raw = raw.get("exp")
        iat_raw = raw.get("iat")

        if not subject or not isinstance(subject, str):
            return None
        if not exp_raw:
            return None

        # Check blacklist
        if jti and self.is_revoked(jti):
            return None

        try:
            exp_dt = (
                datetime.fromtimestamp(exp_raw, tz=timezone.utc)
                if isinstance(exp_raw, (int, float))
                else exp_raw
            )
            iat_dt = (
                datetime.fromtimestamp(iat_raw, tz=timezone.utc)
                if isinstance(iat_raw, (int, float))
                else (iat_raw or datetime.now(timezone.utc))
            )
        except Exception:
            return None

        return TokenClaims(
            subject=subject,
            role=role,
            jti=jti,
            exp=exp_dt,
            iat=iat_dt,
        )

    def decode_token_data(self, token: str) -> TokenData | None:
        """Lightweight decode – returns TokenData for DI use."""
        claims = self.decode_token(token)
        if not claims:
            return None
        return TokenData(
            user_id=claims.subject,
            role=claims.role,
            token_id=claims.jti,
        )

    # ------------------------------------------------------------------
    # Revocation & Blacklist
    # ------------------------------------------------------------------

    def revoke_token(self, jti: str) -> None:
        """Revoke a token by adding its JTI to the blacklist."""
        if jti:
            with self._blacklist_lock:
                self._blacklist.add(jti)

    def is_revoked(self, jti: str) -> bool:
        """Check if a token's JTI is blacklisted."""
        with self._blacklist_lock:
            return jti in self._blacklist

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def is_valid(self, token: str) -> bool:
        """Return True if the token decodes without error."""
        return self.decode_token(token) is not None

    def get_remaining_ttl(self, token: str) -> float:
        """Return remaining seconds until expiry; 0 if expired/invalid."""
        claims = self.decode_token(token)
        if not claims:
            return 0.0
        remaining = (claims.exp - datetime.now(timezone.utc)).total_seconds()
        return max(0.0, remaining)

    # ------------------------------------------------------------------
    # Performance measurement helper
    # ------------------------------------------------------------------

    @staticmethod
    def measure_ms(fn, *args, **kwargs):
        """Run fn(*args, **kwargs) and return (result, duration_ms)."""
        t0 = time.perf_counter()
        result = fn(*args, **kwargs)
        return result, (time.perf_counter() - t0) * 1000.0


# Module-level singleton
jwt_service = JWTService()
