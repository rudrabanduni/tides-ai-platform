"""
Security layer initialization.
"""
from __future__ import annotations

from app.security.jwt import jwt_service
from app.security.roles import role_manager
from app.security.permissions import Permission, has_permission, require_permission, require_role
from app.security.api_keys import api_key_store
from app.security.rate_limit import rate_limiter
from app.security.password import PasswordPolicy, hash_password, verify_password
from app.security.audit import security_audit_service
from app.security.auth import get_current_user, require_roles

__all__ = [
    "jwt_service",
    "role_manager",
    "Permission",
    "has_permission",
    "require_permission",
    "require_role",
    "api_key_store",
    "rate_limiter",
    "PasswordPolicy",
    "hash_password",
    "verify_password",
    "security_audit_service",
    "get_current_user",
    "require_roles",
]
