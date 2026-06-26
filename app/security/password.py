"""
Password utilities – policy enforcement, hashing, generation.

Delegates hashing to app.core.security (passlib/bcrypt) to avoid duplication.
"""
from __future__ import annotations

import re
import secrets
import string

from app.core.security import hash_password, verify_password  # re-export


# ---------------------------------------------------------------------------
# Password policy
# ---------------------------------------------------------------------------

class PasswordPolicy:
    """Configurable password strength policy."""

    MIN_LENGTH: int = 8
    REQUIRE_UPPERCASE: bool = True
    REQUIRE_LOWERCASE: bool = True
    REQUIRE_DIGIT: bool = True
    REQUIRE_SPECIAL: bool = True
    SPECIAL_CHARS: str = "!@#$%^&*()-_=+[]{}|;:,.<>?"

    @classmethod
    def validate(cls, password: str) -> list[str]:
        """Return a list of policy violation messages (empty = valid)."""
        errors: list[str] = []

        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters long.")

        if cls.REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter.")

        if cls.REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter.")

        if cls.REQUIRE_DIGIT and not re.search(r"\d", password):
            errors.append("Password must contain at least one digit.")

        if cls.REQUIRE_SPECIAL and not any(c in cls.SPECIAL_CHARS for c in password):
            errors.append(
                f"Password must contain at least one special character ({cls.SPECIAL_CHARS})."
            )

        return errors

    @classmethod
    def is_valid(cls, password: str) -> bool:
        """Return True if password satisfies all policy rules."""
        return len(cls.validate(password)) == 0

    @classmethod
    def is_strong(cls, password: str) -> bool:
        """Alias for is_valid – semantic clarity at call sites."""
        return cls.is_valid(password)


# ---------------------------------------------------------------------------
# Secure random password generation
# ---------------------------------------------------------------------------

_ALPHABET = (
    string.ascii_uppercase
    + string.ascii_lowercase
    + string.digits
    + "!@#$%^&*()"
)


def generate_secure_password(length: int = 16) -> str:
    """Generate a cryptographically secure random password satisfying the policy."""
    while True:
        pwd = "".join(secrets.choice(_ALPHABET) for _ in range(length))
        if PasswordPolicy.is_valid(pwd):
            return pwd


def generate_temp_password() -> str:
    """Generate a temporary password suitable for first-login flows."""
    return generate_secure_password(length=20)


# ---------------------------------------------------------------------------
# Re-export hashing utilities from core
# ---------------------------------------------------------------------------

__all__ = [
    "PasswordPolicy",
    "generate_secure_password",
    "generate_temp_password",
    "hash_password",
    "verify_password",
]
