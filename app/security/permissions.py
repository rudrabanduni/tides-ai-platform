"""
Permission enum and role-permission mapping.

Performance target: permission lookup < 1 ms.
All lookups are O(1) dict + set operations over pre-computed frozensets.
"""
from __future__ import annotations

import time
from collections.abc import Callable
from enum import Enum
from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.enums import RoleName
from app.security.roles import role_manager
from app.security.schemas import PermissionCheckResult


# ---------------------------------------------------------------------------
# Permission enum
# ---------------------------------------------------------------------------

class Permission(str, Enum):
    # Startup resources
    STARTUP_CREATE = "startup:create"
    STARTUP_READ = "startup:read"
    STARTUP_UPDATE = "startup:update"
    STARTUP_DELETE = "startup:delete"

    # Document resources
    DOCUMENT_UPLOAD = "document:upload"
    DOCUMENT_READ = "document:read"
    DOCUMENT_DELETE = "document:delete"

    # Evaluation resources
    EVALUATION_TRIGGER = "evaluation:trigger"
    EVALUATION_READ = "evaluation:read"
    EVALUATION_RUN = "evaluation:run"

    # Graph resources
    GRAPH_READ = "graph:read"

    # Report resources
    REPORT_READ = "report:read"
    REPORT_DOWNLOAD = "report:download"
    REPORT_VIEW = "report:view"

    # Portfolio resources
    PORTFOLIO_READ = "portfolio:read"
    PORTFOLIO_VIEW = "portfolio:view"

    # Committee resources
    COMMITTEE_READ = "committee:read"
    COMMITTEE_VIEW = "committee:view"
    COMMITTEE_VOTE = "committee:vote"

    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # API Key management
    API_KEY_CREATE = "api_key:create"
    API_KEY_READ = "api_key:read"
    API_KEY_REVOKE = "api_key:revoke"

    # System
    SYSTEM_READ = "system:read"
    SYSTEM_VIEW = "system:view"
    SYSTEM_ADMIN = "system:admin"
    AUDIT_READ = "audit:read"


# ---------------------------------------------------------------------------
# Role → permission mapping
# ---------------------------------------------------------------------------

_VIEWER_PERMISSIONS: frozenset[Permission] = frozenset({
    Permission.STARTUP_READ,
    Permission.DOCUMENT_READ,
    Permission.EVALUATION_READ,
    Permission.GRAPH_READ,
    Permission.REPORT_READ,
    Permission.REPORT_DOWNLOAD,
    Permission.PORTFOLIO_READ,
    Permission.COMMITTEE_READ,
    Permission.SYSTEM_READ,
    Permission.USER_READ,
    Permission.REPORT_VIEW,
    Permission.PORTFOLIO_VIEW,
    Permission.COMMITTEE_VIEW,
    Permission.SYSTEM_VIEW,
})

_ANALYST_PERMISSIONS: frozenset[Permission] = _VIEWER_PERMISSIONS | frozenset({
    Permission.EVALUATION_TRIGGER,
    Permission.EVALUATION_RUN,
})

_COMMITTEE_PERMISSIONS: frozenset[Permission] = _ANALYST_PERMISSIONS | frozenset({
    Permission.COMMITTEE_VOTE,
})

_REVIEWER_PERMISSIONS: frozenset[Permission] = _COMMITTEE_PERMISSIONS | frozenset({
    Permission.STARTUP_UPDATE,
    Permission.DOCUMENT_UPLOAD,
    Permission.DOCUMENT_DELETE,
})

_INCUBATION_MANAGER_PERMISSIONS: frozenset[Permission] = _REVIEWER_PERMISSIONS | frozenset({
    Permission.STARTUP_CREATE,
})

_ADMIN_PERMISSIONS: frozenset[Permission] = _INCUBATION_MANAGER_PERMISSIONS | frozenset({
    Permission.STARTUP_DELETE,
    Permission.USER_CREATE,
    Permission.USER_UPDATE,
    Permission.USER_DELETE,
    Permission.API_KEY_CREATE,
    Permission.API_KEY_READ,
    Permission.API_KEY_REVOKE,
    Permission.SYSTEM_ADMIN,
    Permission.AUDIT_READ,
})

ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    RoleName.ADMIN.value: _ADMIN_PERMISSIONS,
    RoleName.INCUBATION_MANAGER.value: _INCUBATION_MANAGER_PERMISSIONS,
    RoleName.EVALUATOR.value: _INCUBATION_MANAGER_PERMISSIONS,
    RoleName.REVIEWER.value: _REVIEWER_PERMISSIONS,
    RoleName.COMMITTEE_MEMBER.value: _COMMITTEE_PERMISSIONS,
    RoleName.ANALYST.value: _ANALYST_PERMISSIONS,
    RoleName.VIEWER.value: _VIEWER_PERMISSIONS,
}



# ---------------------------------------------------------------------------
# Core permission check (O(1) set membership)
# ---------------------------------------------------------------------------

def has_permission(role: str, permission: Permission) -> bool:
    """Return True if *role* has *permission*.

    Complexity: O(1) hash-set lookup.
    """
    perms = ROLE_PERMISSIONS.get(role, frozenset())
    return permission in perms


def check_permission_with_metrics(
    role: str, permission: Permission, user_id: str
) -> PermissionCheckResult:
    """Check permission and return a detailed result with latency."""
    t0 = time.perf_counter()
    granted = has_permission(role, permission)
    latency_us = (time.perf_counter() - t0) * 1_000_000.0
    return PermissionCheckResult(
        granted=granted,
        user_id=user_id,
        role=role,
        required_permission=permission.value,
        latency_us=latency_us,
    )


def get_role_permissions(role: str) -> frozenset[Permission]:
    """Return the full permission set for *role*."""
    return ROLE_PERMISSIONS.get(role, frozenset())


# ---------------------------------------------------------------------------
# FastAPI dependency factories
# ---------------------------------------------------------------------------

def _get_auth_context(request):
    """Extract AuthContext from request.state, injected by SecurityMiddleware."""
    ctx = getattr(request.state, "auth", None)
    return ctx


def require_permission(permission: Permission) -> Callable:
    """Factory that returns a FastAPI dependency enforcing *permission*.

    Usage::

        @router.get("/foo", dependencies=[Depends(require_permission(Permission.STARTUP_READ))])
        def foo(): ...
    """
    from fastapi import Request

    def dependency(request: Request) -> None:
        auth = getattr(request.state, "auth", None)
        if auth is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required.",
            )
        if not has_permission(auth.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value} required.",
            )

    return dependency


def require_role(required_role: RoleName) -> Callable:
    """Factory that returns a FastAPI dependency enforcing a minimum role level.

    Usage::

        @router.delete("/foo/{id}", dependencies=[Depends(require_role(RoleName.ADMIN))])
        def delete_foo(): ...
    """
    from fastapi import Request

    def dependency(request: Request) -> None:
        auth = getattr(request.state, "auth", None)
        if auth is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required.",
            )
        if not role_manager.has_role(auth.role, required_role.value):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role.value}' or above required.",
            )

    return dependency
