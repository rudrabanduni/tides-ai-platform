"""
Security audit service.

Wraps the existing AuditService to log security-specific events
(login attempts, permission denials, API-key usage, rate-limit events).

Falls back to in-memory ring-buffer logging when no DB session is available
(useful in unit tests that don't use SQLite).
"""
from __future__ import annotations

import logging
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.security.schemas import SecurityAuditEntry

logger = logging.getLogger("tides_security")

# In-memory ring-buffer for when no DB is available (tests / dev)
_RING_SIZE = 500
_ring: deque[SecurityAuditEntry] = deque(maxlen=_RING_SIZE)
_ring_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Security audit actions (string constants)
# ---------------------------------------------------------------------------

class SecurityAction:
    LOGIN_SUCCESS = "security.login_success"
    LOGIN_FAILURE = "security.login_failure"
    LOGOUT = "security.logout"
    TOKEN_INVALID = "security.token_invalid"
    PERMISSION_DENIED = "security.permission_denied"
    PERMISSION_GRANTED = "security.permission_granted"
    API_KEY_CREATED = "security.api_key_created"
    API_KEY_REVOKED = "security.api_key_revoked"
    API_KEY_USED = "security.api_key_used"
    API_KEY_INVALID = "security.api_key_invalid"
    RATE_LIMIT_HIT = "security.rate_limit_exceeded"
    PASSWORD_CHANGED = "security.password_changed"
    USER_CREATED = "security.user_created"
    USER_DEACTIVATED = "security.user_deactivated"


# ---------------------------------------------------------------------------
# Core audit function
# ---------------------------------------------------------------------------

def _build_entry(
    actor: str,
    action: str,
    resource: str,
    ip_address: str,
    status: str,
    details: dict[str, Any] | None = None,
) -> SecurityAuditEntry:
    return SecurityAuditEntry(
        timestamp=datetime.now(timezone.utc),
        actor=actor,
        action=action,
        resource=resource,
        ip_address=ip_address,
        status=status,
        details=details or {},
    )


def _persist_entry(entry: SecurityAuditEntry, db=None) -> None:
    """Persist to DB (if session provided) and always write to ring + logger."""
    with _ring_lock:
        _ring.append(entry)

    logger.info(
        "SECURITY_AUDIT | actor=%s action=%s resource=%s status=%s ip=%s",
        entry.actor,
        entry.action,
        entry.resource,
        entry.status,
        entry.ip_address,
    )

    if db is not None:
        try:
            from app.modules.audit.models import AuditLog

            log = AuditLog(
                actor_id=None,
                entity_type="security",
                entity_id=entry.resource,
                action=entry.action,
                details={
                    "actor": entry.actor,
                    "status": entry.status,
                    "ip_address": entry.ip_address,
                    **entry.details,
                },
            )
            db.add(log)
            db.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("SecurityAudit: DB persist failed: %s", exc)


# ---------------------------------------------------------------------------
# Public security audit service
# ---------------------------------------------------------------------------

class SecurityAuditService:
    """Structured security event logger."""

    def __init__(self, db=None) -> None:
        self.db = db

    def log(
        self,
        actor: str,
        action: str,
        resource: str,
        ip_address: str = "unknown",
        status: str = "success",
        details: dict[str, Any] | None = None,
    ) -> None:
        entry = _build_entry(actor, action, resource, ip_address, status, details)
        _persist_entry(entry, self.db)

    # Convenience methods ---------------------------------------------------

    def login_success(self, user_id: str, ip: str) -> None:
        self.log(user_id, SecurityAction.LOGIN_SUCCESS, "/auth/login", ip, "success")

    def login_failure(self, email: str, ip: str, reason: str = "") -> None:
        self.log(
            email or "anonymous",
            SecurityAction.LOGIN_FAILURE,
            "/auth/login",
            ip,
            "failure",
            {"reason": reason},
        )

    def token_invalid(self, ip: str, reason: str = "") -> None:
        self.log("anonymous", SecurityAction.TOKEN_INVALID, "/auth", ip, "failure", {"reason": reason})

    def permission_denied(self, user_id: str, permission: str, resource: str, ip: str) -> None:
        self.log(
            user_id,
            SecurityAction.PERMISSION_DENIED,
            resource,
            ip,
            "failure",
            {"required_permission": permission},
        )

    def api_key_used(self, key_name: str, resource: str, ip: str) -> None:
        self.log(key_name, SecurityAction.API_KEY_USED, resource, ip, "success")

    def api_key_invalid(self, ip: str) -> None:
        self.log("anonymous", SecurityAction.API_KEY_INVALID, "/api", ip, "failure")

    def rate_limit_hit(self, identifier: str, resource: str, ip: str) -> None:
        self.log(identifier, SecurityAction.RATE_LIMIT_HIT, resource, ip, "blocked")

    def api_key_created(self, actor_id: str, key_name: str) -> None:
        self.log(actor_id, SecurityAction.API_KEY_CREATED, "/security/api-keys", "internal", "success",
                 {"key_name": key_name})

    def api_key_revoked(self, actor_id: str, key_id: str) -> None:
        self.log(actor_id, SecurityAction.API_KEY_REVOKED, f"/security/api-keys/{key_id}", "internal", "success")

    def logout(self, user_id: str, ip: str) -> None:
        self.log(user_id, SecurityAction.LOGOUT, "/auth/logout", ip, "success")

    def token_refresh(self, user_id: str, ip: str) -> None:
        self.log(user_id, "security.token_refresh", "/auth/refresh", ip, "success")

    def evaluation_execution(self, user_id: str, startup_id: str, ip: str) -> None:
        self.log(user_id, "security.evaluation_execution", f"/startups/{startup_id}/evaluate", ip, "success")

    def committee_decision(self, user_id: str, startup_id: str, decision: str, ip: str) -> None:
        self.log(user_id, "security.committee_decision", f"/committee/decision/{startup_id}", ip, "success", {"decision": decision})

    def portfolio_access(self, user_id: str, ip: str) -> None:
        self.log(user_id, "security.portfolio_access", "/portfolio", ip, "success")

    def document_upload(self, user_id: str, document_name: str, ip: str) -> None:
        self.log(user_id, "security.document_upload", f"/documents/upload/{document_name}", ip, "success")

    def startup_deletion(self, user_id: str, startup_id: str, ip: str) -> None:
        self.log(user_id, "security.startup_deletion", f"/startups/{startup_id}", ip, "success")

    def system_access(self, user_id: str, resource: str, ip: str) -> None:
        self.log(user_id, "security.system_access", resource, ip, "success")


# ---------------------------------------------------------------------------
# Ring-buffer accessors (for testing and /security/audit endpoint)
# ---------------------------------------------------------------------------

def get_recent_events(limit: int = 50) -> list[SecurityAuditEntry]:
    """Return the most recent security audit events from the ring buffer."""
    with _ring_lock:
        events = list(_ring)
    return events[-limit:]


def clear_audit_ring() -> None:
    """Clear the in-memory ring buffer (test helper)."""
    with _ring_lock:
        _ring.clear()


# Module-level singleton
security_audit_service = SecurityAuditService()

