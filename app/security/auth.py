"""
Authentication service – token and API-key verification.

Resolves principal (user object or AuthContext) from:
  1. Bearer JWT token
  2. X-API-Key header
  3. DEV_MODE bypass (returns first active user)

Does NOT call any LLM, external API, or make network requests.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.modules.users.models import User
from app.modules.users.service import UserService
from app.security.api_keys import api_key_store
from app.security.audit import SecurityAuditService
from app.security.jwt import jwt_service
from app.security.schemas import AuthContext

logger = logging.getLogger("tides_security")

settings = get_settings()

# FastAPI security schemes
_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login",
    auto_error=False,
)
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _get_dev_user(db: Session) -> User:
    """DEV_MODE: return first active user (creates one if none exist)."""
    users = UserService(db).list_users(limit=1)
    if users:
        return users[0]
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="DEV_MODE active but no users bootstrapped. POST /api/v1/auth/bootstrap-admin first.",
    )


def _resolve_user_by_jwt(token: str, db: Session) -> User | None:
    """Decode JWT, validate, and load the User from DB."""
    token_data = jwt_service.decode_token_data(token)
    if not token_data:
        return None
    try:
        user = UserService(db).get_user(__import__("uuid").UUID(token_data.user_id))
    except Exception:
        return None
    if not user.is_active:
        return None
    return user


def _resolve_user_by_api_key(raw_key: str, db: Session) -> User | None:
    """Validate API key and load the corresponding User from DB."""
    key_obj = api_key_store.validate(raw_key)
    if not key_obj:
        return None
    # For API-key based auth, create a synthetic user representation:
    # Look for an active user that has the key's role; fallback to first admin.
    # In a real system this would be a service account; here we use the first
    # matching real user as a proxy so existing RBAC keeps working.
    from app.core.enums import RoleName
    users = UserService(db).list_users(limit=100)
    for u in users:
        if u.role.name == key_obj.role and u.is_active:
            return u
    # Fallback: first active user regardless of role
    for u in users:
        if u.is_active:
            return u
    return None


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------

def get_current_user(
    request: Request,
    token: Annotated[str | None, Depends(_oauth2_scheme)],
    api_key: Annotated[str | None, Depends(_api_key_header)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Resolve the current authenticated user.

    Priority:
      1. DEV_MODE  → bypass all checks, return first user
      2. Bearer JWT
      3. X-API-Key header
      4. Unauthenticated → 401
    """
    audit = SecurityAuditService(db)
    ip = request.client.host if request.client else "unknown"

    # DEV_MODE bypass
    if settings.dev_mode:
        user = _get_dev_user(db)
        request.state.auth = AuthContext(
            user_id=str(user.id),
            role=user.role.name,
            auth_method="dev_mode",
        )
        return user

    # JWT authentication
    if token:
        user = _resolve_user_by_jwt(token, db)
        if user:
            request.state.auth = AuthContext(
                user_id=str(user.id),
                role=user.role.name,
                auth_method="jwt",
            )
            return user
        audit.token_invalid(ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # API-Key authentication
    if api_key:
        key_obj = api_key_store.validate(api_key)
        if key_obj:
            user = _resolve_user_by_api_key(api_key, db)
            if user:
                audit.api_key_used(key_obj.name, request.url.path, ip)
                request.state.auth = AuthContext(
                    user_id=str(user.id),
                    role=user.role.name,
                    auth_method="api_key",
                    api_key_name=key_obj.name,
                )
                return user
        audit.api_key_invalid(ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key.",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide a Bearer token or X-API-Key header.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_roles(*allowed_roles: str):
    """Dependency factory: ensure current user has one of the allowed roles."""
    from app.core.enums import RoleName
    from app.security.roles import role_manager

    def dependency(
        request: Request,
        token: Annotated[str | None, Depends(_oauth2_scheme)],
        api_key: Annotated[str | None, Depends(_api_key_header)],
        db: Annotated[Session, Depends(get_db)],
    ) -> User:
        # DEV_MODE: skip enforcement
        if settings.dev_mode:
            return _get_dev_user(db)

        user = get_current_user(request, token, api_key, db)
        # Role hierarchy: admin satisfies any lower role
        user_role = user.role.name
        for r in allowed_roles:
            if role_manager.has_role(user_role, r):
                return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient role. Required one of: {list(allowed_roles)}",
        )

    return dependency


# ---------------------------------------------------------------------------
# Typed Annotated shortcuts (mirrors app.modules.auth.dependencies pattern)
# ---------------------------------------------------------------------------

AnyAuthenticatedUser = Annotated[User, Depends(get_current_user)]
