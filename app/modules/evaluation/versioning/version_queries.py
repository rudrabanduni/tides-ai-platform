from typing import Any, Dict, List, Tuple, Optional
from sqlalchemy.orm import Session

from app.modules.evaluation.versioning.version_models import StartupVersion, VersionSnapshot, DeltaReport
from app.modules.evaluation.versioning.version_engine import VersionEngine
from app.modules.evaluation.versioning.delta_engine import DeltaEngine
from app.modules.evaluation.versioning.version_serializer import VersionSerializer


def create_version(
    startup_id: str,
    db: Session,
    actor: str,
    workflow_id: str = "N/A",
    metadata: Optional[Dict[str, Any]] = None
) -> StartupVersion:
    """Create an immutable version snapshot of the evaluation pipeline state."""
    return VersionEngine.create_version(
        startup_id=startup_id,
        db=db,
        actor=actor,
        workflow_id=workflow_id,
        metadata=metadata
    )


def get_version(startup_id: str, version_number: int) -> Tuple[StartupVersion, VersionSnapshot]:
    """Retrieve a specific version's metadata and complete snapshot data."""
    return VersionEngine.load_version(startup_id, version_number)


def list_versions(startup_id: str) -> List[StartupVersion]:
    """List all version metadata entries for a given startup."""
    return VersionEngine.list_versions(startup_id)


def trace_version_history(startup_id: str) -> List[StartupVersion]:
    """Retrieve the historical sequence of versions for a startup, sorted chronologically."""
    versions = VersionEngine.list_versions(startup_id)
    return sorted(versions, key=lambda v: v.version_number)


def compare_versions(startup_id: str, from_version: int, to_version: int) -> DeltaReport:
    """Compare two historical version snapshots and return a DeltaReport."""
    _, from_snapshot = VersionEngine.load_version(startup_id, from_version)
    _, to_snapshot = VersionEngine.load_version(startup_id, to_version)
    return DeltaEngine.compare_versions(
        startup_id=startup_id,
        from_version=from_version,
        to_version=to_version,
        from_snapshot=from_snapshot,
        to_snapshot=to_snapshot
    )


def generate_delta(startup_id: str, from_version: int, to_version: int) -> DeltaReport:
    """Alias for compare_versions to generate a delta report between two versions."""
    return compare_versions(startup_id, from_version, to_version)


def rollback_version(
    startup_id: str,
    version_number: int,
    db: Session,
    actor: str,
    role: str,
    reason: str
) -> StartupVersion:
    """Roll back the active database state, graph files, and workflows to a historical version."""
    return VersionEngine.rollback_version(
        startup_id=startup_id,
        version_number=version_number,
        db=db,
        actor=actor,
        role=role,
        reason=reason
    )


def export_version(startup_id: str, version_number: int, format: str) -> Any:
    """Export a version snapshot in the requested format (JSON, Markdown, HTML, PDF)."""
    version, snapshot = VersionEngine.load_version(startup_id, version_number)
    return VersionSerializer.export_version(version, snapshot, format)
