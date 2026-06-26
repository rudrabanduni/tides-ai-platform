"""
Security middleware collection.
"""
from __future__ import annotations

import time
import uuid
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import get_settings
from app.security.auth import _resolve_user_by_jwt, _resolve_user_by_api_key, _get_dev_user
from app.security.api_keys import api_key_store
from app.security.rate_limit import rate_limiter
from app.security.audit import security_audit_service
from app.security.schemas import AuthContext

logger = logging.getLogger("tides_security")
settings = get_settings()


class RequestIdentityMiddleware(BaseHTTPMiddleware):
    """Ensure every request has a unique request ID in request.state and headers."""

    async def dispatch(self, request: Request, call_next) -> Response:
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = req_id
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject standard security response headers (HSTS, CSP, X-Frame-Options, etc.)."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response


class AuthContextMiddleware(BaseHTTPMiddleware):
    """Authenticate requests via JWT or API Key and attach AuthContext to request.state.auth."""

    async def dispatch(self, request: Request, call_next) -> Response:
        from app.db.session import SessionLocal

        request.state.auth = None

        # DEV_MODE bypass
        if settings.dev_mode:
            with SessionLocal() as db:
                try:
                    user = _get_dev_user(db)
                    request.state.auth = AuthContext(
                        user_id=str(user.id),
                        role=user.role.name,
                        auth_method="dev_mode",
                        ip_address=request.client.host if request.client else "unknown",
                    )
                except Exception:
                    pass

        else:
            # 1. Bearer JWT
            auth_header = request.headers.get("Authorization")
            token = None
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]

            if token:
                with SessionLocal() as db:
                    user = _resolve_user_by_jwt(token, db)
                    if user:
                        request.state.auth = AuthContext(
                            user_id=str(user.id),
                            role=user.role.name,
                            auth_method="jwt",
                            ip_address=request.client.host if request.client else "unknown",
                        )

            # 2. X-API-Key
            if not request.state.auth:
                api_key = request.headers.get("X-API-Key")
                if api_key:
                    key_obj = api_key_store.validate(api_key)
                    if key_obj:
                        with SessionLocal() as db:
                            user = _resolve_user_by_api_key(api_key, db)
                            if user:
                                request.state.auth = AuthContext(
                                    user_id=str(user.id),
                                    role=user.role.name,
                                    auth_method="api_key",
                                    api_key_name=key_obj.name,
                                    ip_address=request.client.host if request.client else "unknown",
                                )

        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce rate limits per-IP, per-User, or per-API Key."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Determine client identity
        ip = request.client.host if request.client else "unknown"
        identifier = ip
        limit = rate_limiter.DEFAULT_LIMIT
        window = rate_limiter.DEFAULT_WINDOW

        auth: AuthContext | None = getattr(request.state, "auth", None)
        if auth:
            if auth.auth_method == "api_key":
                identifier = f"key:{auth.api_key_name}"
                limit = rate_limiter.AUTH_LIMIT
                window = rate_limiter.AUTH_WINDOW
            elif auth.auth_method == "jwt":
                identifier = f"user:{auth.user_id}"
                limit = rate_limiter.AUTH_LIMIT
                window = rate_limiter.AUTH_WINDOW

        is_limited, info = rate_limiter.check(identifier, limit=limit, window_seconds=window)

        if is_limited:
            # Audit the rate limit event
            security_audit_service.rate_limit_hit(identifier, request.url.path, ip)
            reset_secs = int(max((info.reset_at - info.reset_at.now(info.reset_at.tzinfo)).total_seconds(), 1.0))
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={"Retry-After": str(reset_secs)},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(info.limit)
        response.headers["X-RateLimit-Remaining"] = str(info.remaining)
        response.headers["X-RateLimit-Reset"] = info.reset_at.isoformat()
        return response


class AuditMiddleware(BaseHTTPMiddleware):
    """Automatically logs security-sensitive actions and errors to the Audit Service."""

    async def dispatch(self, request: Request, call_next) -> Response:
        ip = request.client.host if request.client else "unknown"
        auth: AuthContext | None = getattr(request.state, "auth", None)
        actor = "anonymous"
        if auth:
            actor = auth.user_id if auth.auth_method != "api_key" else f"key:{auth.api_key_name}"

        # Determine if this is a mutation or system-sensitive action
        path = request.url.path
        method = request.method

        response = await call_next(request)

        # Log failures for security actions (e.g. 401, 403)
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            security_audit_service.log(actor, "security.token_invalid", path, ip, "failure")
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            security_audit_service.log(actor, "security.permission_denied", path, ip, "failure")
        elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            # Already logged in RateLimitMiddleware, no-op
            pass
        elif method in ("POST", "PUT", "DELETE", "PATCH"):
            # Audit mutation success/failure
            status_str = "success" if response.status_code < 400 else "failure"
            
            # Specific mappings for the audit logs required by the sprint
            if "startups" in path and method == "DELETE":
                security_audit_service.startup_deletion(actor, path.split("/")[-1], ip)
            elif "documents" in path and method == "POST":
                security_audit_service.document_upload(actor, "document", ip)
            elif "evaluate" in path or "assessment" in path:
                security_audit_service.evaluation_execution(actor, "evaluation", ip)
            elif "committee" in path:
                security_audit_service.committee_decision(actor, "committee", "decision", ip)
            elif "portfolio" in path:
                security_audit_service.portfolio_access(actor, ip)
            else:
                security_audit_service.log(actor, f"audit.mutation.{method.lower()}", path, ip, status_str)

        return response
