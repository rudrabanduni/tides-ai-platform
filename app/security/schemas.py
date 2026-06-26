"""
Security layer Pydantic schemas.

All data contracts for JWT tokens, API keys, permissions,
audit entries, and rate-limit metadata live here.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.enums import RoleName


# ---------------------------------------------------------------------------
# JWT / Token schemas
# ---------------------------------------------------------------------------

class TokenClaims(BaseModel):
    """Validated claims extracted from a decoded JWT."""

    subject: str  # user UUID as string
    role: str  # RoleName.value
    jti: str  # JWT-ID – unique per token
    exp: datetime
    iat: datetime


class TokenData(BaseModel):
    """Lightweight auth context carried through request dependencies."""

    user_id: str
    role: str
    token_id: str


class TokenPair(BaseModel):
    """Access + refresh token pair returned on login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    role: str


# ---------------------------------------------------------------------------
# API Key schemas
# ---------------------------------------------------------------------------

class APIKeyCreate(BaseModel):
    """Payload to create a new API key."""

    name: str = Field(min_length=1, max_length=128)
    role: RoleName = RoleName.VIEWER
    expires_at: datetime | None = None


class APIKeyRead(BaseModel):
    """API key metadata – safe to return to client."""

    id: str
    name: str
    key_prefix: str  # first 12 characters of raw key for identification
    role: str
    is_active: bool
    created_at: datetime
    expires_at: datetime | None


class APIKeyResponse(APIKeyRead):
    """Returned only once on creation; contains the full raw key."""

    key: str  # full key – store it now, it won't be shown again


# ---------------------------------------------------------------------------
# Permission schemas
# ---------------------------------------------------------------------------

class PermissionCheckResult(BaseModel):
    """Result of a permission check."""

    granted: bool
    user_id: str
    role: str
    required_permission: str
    latency_us: float  # microseconds


# ---------------------------------------------------------------------------
# Rate-limit schemas
# ---------------------------------------------------------------------------

class RateLimitInfo(BaseModel):
    """Current rate-limit state for an identifier."""

    identifier: str
    limit: int
    remaining: int
    reset_at: datetime
    is_limited: bool


# ---------------------------------------------------------------------------
# Audit schemas
# ---------------------------------------------------------------------------

class SecurityAuditEntry(BaseModel):
    """A structured security audit event."""

    timestamp: datetime
    actor: str  # user_id, api_key_name, or "anonymous"
    action: str  # e.g. "login_success", "permission_denied"
    resource: str  # endpoint or resource path
    ip_address: str
    status: str  # "success" | "failure" | "blocked"
    details: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Auth context schema (passed through request state)
# ---------------------------------------------------------------------------

class AuthContext(BaseModel):
    """Rich auth context attached to request.state.auth."""

    user_id: str
    role: str
    auth_method: str  # "jwt" | "api_key" | "dev_mode"
    api_key_name: str | None = None
    token_id: str | None = None
    ip_address: str | None = None
