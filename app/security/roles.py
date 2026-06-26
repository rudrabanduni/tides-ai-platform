"""
Role hierarchy and effective-permission computation.

Each higher role inherits all permissions of lower roles.
Hierarchy (highest → lowest):
    admin > evaluator > committee_member > viewer
"""
from __future__ import annotations

from app.core.enums import RoleName

# Ordered from most-privileged to least-privileged
_ROLE_HIERARCHY: list[str] = [
    RoleName.ADMIN.value,
    RoleName.INCUBATION_MANAGER.value,
    RoleName.EVALUATOR.value,  # Map legacy/compat role
    RoleName.REVIEWER.value,
    RoleName.COMMITTEE_MEMBER.value,
    RoleName.ANALYST.value,
    RoleName.VIEWER.value,
]

# Pre-computed rank map (lower number = higher privilege)
_ROLE_RANK: dict[str, int] = {role: idx for idx, role in enumerate(_ROLE_HIERARCHY)}



class RoleManager:
    """Deterministic, in-memory role hierarchy manager.

    All methods are O(1) or O(n-roles) to satisfy the < 1 ms budget.
    """

    # ------------------------------------------------------------------
    # Rank queries
    # ------------------------------------------------------------------

    @staticmethod
    def rank(role: str) -> int:
        """Return privilege rank (0 = admin, higher = less privileged).

        Unknown roles are treated as less privileged than viewer.
        """
        return _ROLE_RANK.get(role, len(_ROLE_HIERARCHY))

    @staticmethod
    def has_role(user_role: str, required_role: str) -> bool:
        """Return True if *user_role* satisfies *required_role* or above.

        E.g. admin satisfies evaluator, viewer does not satisfy admin.
        """
        return _ROLE_RANK.get(user_role, 999) <= _ROLE_RANK.get(required_role, 999)

    @staticmethod
    def roles_at_or_above(required_role: str) -> list[str]:
        """Return all roles that satisfy *required_role*."""
        threshold = _ROLE_RANK.get(required_role, 999)
        return [r for r, rank in _ROLE_RANK.items() if rank <= threshold]

    @staticmethod
    def is_known_role(role: str) -> bool:
        """Return True if role is a recognized RoleName value."""
        return role in _ROLE_RANK

    @staticmethod
    def all_roles() -> list[str]:
        """Return all roles ordered highest to lowest privilege."""
        return list(_ROLE_HIERARCHY)

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    @staticmethod
    def display_name(role: str) -> str:
        return role.replace("_", " ").title()


# Module-level singleton
role_manager = RoleManager()
