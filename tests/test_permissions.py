import pytest
from app.core.enums import RoleName
from app.security.permissions import Permission, has_permission, get_role_permissions
from app.security.roles import role_manager


def test_role_hierarchy() -> None:
    # Admin has all lower roles
    assert role_manager.has_role("admin", "admin")
    assert role_manager.has_role("admin", "incubation_manager")
    assert role_manager.has_role("admin", "evaluator")
    assert role_manager.has_role("admin", "reviewer")
    assert role_manager.has_role("admin", "committee_member")
    assert role_manager.has_role("admin", "analyst")
    assert role_manager.has_role("admin", "viewer")

    # Incubation Manager hierarchy
    assert not role_manager.has_role("incubation_manager", "admin")
    assert role_manager.has_role("incubation_manager", "incubation_manager")
    assert role_manager.has_role("incubation_manager", "reviewer")
    assert role_manager.has_role("incubation_manager", "viewer")

    # Committee Member vs Reviewer
    assert not role_manager.has_role("committee_member", "reviewer")
    assert role_manager.has_role("committee_member", "committee_member")
    assert role_manager.has_role("committee_member", "viewer")

    # Viewer cannot satisfy Analyst
    assert not role_manager.has_role("viewer", "analyst")
    assert role_manager.has_role("viewer", "viewer")


def test_permission_mappings() -> None:
    # Admin permissions
    assert has_permission("admin", Permission.STARTUP_CREATE)
    assert has_permission("admin", Permission.STARTUP_DELETE)
    assert has_permission("admin", Permission.SYSTEM_ADMIN)
    assert has_permission("admin", Permission.AUDIT_READ)

    # Incubation Manager permissions
    assert has_permission("incubation_manager", Permission.STARTUP_CREATE)
    assert not has_permission("incubation_manager", Permission.STARTUP_DELETE)
    assert not has_permission("incubation_manager", Permission.SYSTEM_ADMIN)

    # Reviewer permissions
    assert not has_permission("reviewer", Permission.STARTUP_CREATE)
    assert has_permission("reviewer", Permission.STARTUP_UPDATE)
    assert has_permission("reviewer", Permission.DOCUMENT_UPLOAD)
    
    # Committee Member permissions
    assert not has_permission("committee_member", Permission.STARTUP_UPDATE)
    assert has_permission("committee_member", Permission.COMMITTEE_VOTE)

    # Analyst permissions
    assert not has_permission("analyst", Permission.COMMITTEE_VOTE)
    assert has_permission("analyst", Permission.EVALUATION_TRIGGER)
    assert has_permission("analyst", Permission.EVALUATION_RUN)

    # Viewer permissions
    assert not has_permission("viewer", Permission.EVALUATION_TRIGGER)
    assert has_permission("viewer", Permission.STARTUP_READ)
    assert has_permission("viewer", Permission.REPORT_VIEW)


def test_get_role_permissions() -> None:
    admin_perms = get_role_permissions("admin")
    viewer_perms = get_role_permissions("viewer")
    
    assert len(admin_perms) > len(viewer_perms)
    assert Permission.SYSTEM_ADMIN in admin_perms
    assert Permission.SYSTEM_ADMIN not in viewer_perms
