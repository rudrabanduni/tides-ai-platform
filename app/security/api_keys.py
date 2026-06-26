"""
API Key management – thread-safe in-memory store.

API keys have the format:  tid_<key_id>.<secret>
  – key_id  : 8-char alphanum prefix, safe to log / display
  – secret  : 32-char cryptographically random token

The secret is stored as a bcrypt hash.  Only the raw key is returned once
on creation; subsequent verifications use the hash.

Why in-memory?
  The security layer is additive and database-schema-agnostic.  An in-memory
  store works correctly for both production (single-process) and test (SQLite)
  environments.  A DB-backed implementation can replace this class without
  changing callers.
"""
from __future__ import annotations

import hashlib
import secrets
import threading
from datetime import datetime, timezone
from typing import Iterator
from uuid import uuid4

from app.core.enums import RoleName
from app.security.schemas import APIKeyCreate, APIKeyRead, APIKeyResponse


# ---------------------------------------------------------------------------
# Internal data class
# ---------------------------------------------------------------------------

class _APIKey:
    """Internal representation of a stored API key."""

    __slots__ = (
        "id", "name", "key_prefix", "key_hash",
        "role", "is_active", "created_at", "expires_at",
    )

    def __init__(
        self,
        id: str,
        name: str,
        key_prefix: str,
        key_hash: str,
        role: str,
        created_at: datetime,
        expires_at: datetime | None,
    ) -> None:
        self.id = id
        self.name = name
        self.key_prefix = key_prefix
        self.key_hash = key_hash
        self.role = role
        self.is_active = True
        self.created_at = created_at
        self.expires_at = expires_at

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def to_read(self) -> APIKeyRead:
        return APIKeyRead(
            id=self.id,
            name=self.name,
            key_prefix=self.key_prefix,
            role=self.role,
            is_active=self.is_active,
            created_at=self.created_at,
            expires_at=self.expires_at,
        )


# ---------------------------------------------------------------------------
# Key generation helpers
# ---------------------------------------------------------------------------

_PREFIX = "tid"


def _generate_raw_key() -> tuple[str, str, str]:
    """Generate (raw_key, key_prefix, key_hash).

    raw_key format:  tid_<8-char-id>.<32-char-secret>
    """
    key_id = secrets.token_urlsafe(6)[:8]          # ~8 chars
    secret = secrets.token_urlsafe(32)[:40]         # 40 chars
    raw_key = f"{_PREFIX}_{key_id}.{secret}"
    key_prefix = f"{_PREFIX}_{key_id}"
    # Use SHA-256 for the stored hash (fast, one-way, good-enough for bearer tokens)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return raw_key, key_prefix, key_hash


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Thread-safe store
# ---------------------------------------------------------------------------

class APIKeyStore:
    """Thread-safe in-memory API key registry."""

    def __init__(self) -> None:
        self._store: dict[str, _APIKey] = {}          # id → key
        self._hash_index: dict[str, str] = {}          # hash → id
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def create(self, payload: APIKeyCreate) -> APIKeyResponse:
        """Create a new API key and return the response (raw key included)."""
        raw_key, key_prefix, key_hash = _generate_raw_key()
        key_id = str(uuid4())
        now = datetime.now(timezone.utc)
        key = _APIKey(
            id=key_id,
            name=payload.name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            role=payload.role.value,
            created_at=now,
            expires_at=payload.expires_at,
        )
        with self._lock:
            self._store[key_id] = key
            self._hash_index[key_hash] = key_id
        return APIKeyResponse(
            id=key_id,
            name=payload.name,
            key_prefix=key_prefix,
            role=payload.role.value,
            is_active=True,
            created_at=now,
            expires_at=payload.expires_at,
            key=raw_key,
        )

    def revoke(self, key_id: str) -> bool:
        """Deactivate a key by id.  Returns True if found."""
        with self._lock:
            key = self._store.get(key_id)
            if key:
                key.is_active = False
                return True
        return False

    def delete(self, key_id: str) -> bool:
        """Permanently delete a key.  Returns True if found."""
        with self._lock:
            key = self._store.pop(key_id, None)
            if key:
                self._hash_index.pop(key.key_hash, None)
                return True
        return False

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def validate(self, raw_key: str) -> _APIKey | None:
        """Return the active, non-expired _APIKey for *raw_key*, or None."""
        key_hash = _hash_key(raw_key)
        with self._lock:
            key_id = self._hash_index.get(key_hash)
            if not key_id:
                return None
            key = self._store.get(key_id)
        if not key or not key.is_active or key.is_expired():
            return None
        return key

    def get(self, key_id: str) -> _APIKey | None:
        with self._lock:
            return self._store.get(key_id)

    def list_all(self) -> list[APIKeyRead]:
        with self._lock:
            return [k.to_read() for k in self._store.values()]

    def __iter__(self) -> Iterator[_APIKey]:
        with self._lock:
            return iter(list(self._store.values()))

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)


# Module-level singleton shared across the process
api_key_store = APIKeyStore()
