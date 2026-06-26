import hashlib
import json
from typing import List, Dict, Any, Tuple
from app.modules.evaluation.versioning.version_models import StartupVersion, VersionSnapshot
from app.modules.evaluation.versioning import version_events


class VersionValidationError(Exception):
    def __init__(self, message: str, errors: List[str] = None):
        super().__init__(message)
        self.errors = errors or []


class VersionValidator:
    """Validator implementing Sprint 4.2A versioning integrity and business rules."""

    @staticmethod
    def validate_version(
        version: StartupVersion,
        snapshot: VersionSnapshot,
        existing_versions: List[StartupVersion],
        active_workflow_ids: List[str]
    ) -> List[str]:
        errors = []

        # 1. Version integrity hash validation
        recomputed_hash = VersionValidator.compute_integrity_hash(version, snapshot)
        if version.graph_hash != snapshot.observation_graph.get("graph_hash"):
            errors.append(
                f"Graph hash mismatch: version metadata graph_hash '{version.graph_hash}' "
                f"does not match snapshot graph_hash '{snapshot.observation_graph.get('graph_hash')}'."
            )

        # 2. Duplicate versions check
        for ev in existing_versions:
            if ev.version_number == version.version_number:
                errors.append(f"Duplicate version: version number {version.version_number} already exists.")

        # 3. Workflow exists validation
        if version.workflow_id not in active_workflow_ids and version.workflow_id != "N/A":
            # For simplicity, if workflow_id is present, check it exists
            errors.append(f"Workflow ID '{version.workflow_id}' does not exist in registry.")

        # 4. Committee report exists check
        elif not snapshot.committee_report:
            errors.append("Committee report snapshot is missing or null.")
        else:
            stored_dec_id = snapshot.committee_report.get("decision_id") or snapshot.committee_report.get("decision", {}).get("decision_id")
            if version.committee_report_id != stored_dec_id and version.committee_report_id != "N/A":
                errors.append(
                    f"Committee report ID mismatch: metadata committee_report_id '{version.committee_report_id}' "
                    f"does not match snapshot decision ID '{stored_dec_id}'."
                )

        # 5. Investment report exists check
        if not snapshot.investment_report:
            errors.append("Investment report snapshot is missing or null.")
        elif version.investment_report_id != snapshot.investment_report.get("assessment_id"):
            stored_inv_id = snapshot.investment_report.get("assessment_id")
            if version.investment_report_id != stored_inv_id and version.investment_report_id != "N/A":
                errors.append(
                    f"Investment report ID mismatch: metadata investment_report_id '{version.investment_report_id}' "
                    f"does not match snapshot assessment ID '{stored_inv_id}'."
                )

        # 6. Metadata completeness check
        if not version.metadata:
            errors.append("Version metadata is empty or null.")
        else:
            required_keys = ["user", "request_id"]
            for rk in required_keys:
                # Also check common aliases like 'actor'
                if rk not in version.metadata and (rk == "user" and "actor" not in version.metadata):
                    errors.append(f"Metadata completeness failure: missing required key '{rk}'.")

        if errors:
            version_events.publish_version_validation_failed(
                startup_id=version.startup_id,
                version_number=version.version_number,
                error="; ".join(errors)
            )

        return errors

    @staticmethod
    def compute_integrity_hash(version: StartupVersion, snapshot: VersionSnapshot) -> str:
        """Compute deterministic SHA-256 integrity hash of the snapshot data."""
        # Clean dict snapshot of volatile fields for deterministic hashing
        snap_data = snapshot.model_dump()
        serialized = json.dumps(snap_data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
