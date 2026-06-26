import os
import json
import time
import uuid
from uuid import UUID
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from app.modules.evaluation.versioning.version_models import StartupVersion, VersionSnapshot
from app.modules.evaluation.versioning import version_events
from app.modules.evaluation.versioning.version_validator import VersionValidator, VersionValidationError
from app.modules.intelligence.models import (
    StartupIntelligenceProfile, StartupClaim, StartupEvidence, FieldConflict
)
from app.modules.workflow.workflow_models import Workflow, WorkflowHistoryEntry
from app.modules.workflow.workflow_queries import register_workflow, register_history_entry, get_workflow
from app.security.audit import security_audit_service


class VersionEngine:
    """Core orchestration engine for immutable Startup Versioning and rollback."""

    @staticmethod
    def _get_versions_dir(startup_id: str) -> str:
        versions_dir = os.path.join("uploads", "versions", startup_id)
        os.makedirs(versions_dir, exist_ok=True)
        return versions_dir

    @staticmethod
    def _get_version_path(startup_id: str, version_number: int) -> str:
        return os.path.join(VersionEngine._get_versions_dir(startup_id), f"version_{version_number}.json")

    @staticmethod
    def _get_index_path(startup_id: str) -> str:
        return os.path.join(VersionEngine._get_versions_dir(startup_id), "index.json")

    @staticmethod
    def compute_version_hash(version: StartupVersion, snapshot: VersionSnapshot) -> str:
        return VersionValidator.compute_integrity_hash(version, snapshot)

    @staticmethod
    def persist_snapshot(startup_id: str, version_number: int, version: StartupVersion, snapshot: VersionSnapshot) -> None:
        """Saves the version details and full snapshot data as an immutable JSON file, and updates the index."""
        # 1. Save full snapshot file
        filepath = VersionEngine._get_version_path(startup_id, version_number)
        payload = {
            "version": version.model_dump(),
            "snapshot": snapshot.model_dump()
        }
        
        # Serialize with sorted keys for determinism
        serialized = json.dumps(payload, default=str, sort_keys=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(serialized)

        # 2. Update index file
        index_path = VersionEngine._get_index_path(startup_id)
        existing_versions = []
        if os.path.exists(index_path):
            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    existing_versions = [StartupVersion(**item) for item in data]
            except Exception:
                pass

        # Check for duplicates first
        if not any(v.version_number == version_number for v in existing_versions):
            existing_versions.append(version)
            existing_versions.sort(key=lambda x: x.version_number)
            
            # Serialize index
            index_serialized = json.dumps([v.model_dump() for v in existing_versions], default=str, sort_keys=True)
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(index_serialized)

    @staticmethod
    def list_versions(startup_id: str) -> List[StartupVersion]:
        """Lists metadata versions for a startup from the fast index file (under 20ms lookup target)."""
        index_path = VersionEngine._get_index_path(startup_id)
        if not os.path.exists(index_path):
            return []
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [StartupVersion(**item) for item in data]
        except Exception:
            return []

    @staticmethod
    def load_version(startup_id: str, version_number: int) -> Tuple[StartupVersion, VersionSnapshot]:
        """Loads version metadata and snapshot payload for the target version number."""
        filepath = VersionEngine._get_version_path(startup_id, version_number)
        if not os.path.exists(filepath):
            raise VersionValidationError(f"Version number {version_number} does not exist for startup '{startup_id}'.")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.loads(f.read())

        version = StartupVersion(**data["version"])
        snapshot = VersionSnapshot(**data["snapshot"])

        # Publish loaded event
        version_events.publish_version_loaded(startup_id, version_number, version.version_id)
        return version, snapshot

    @staticmethod
    def create_version(
        startup_id: str,
        db: Session,
        actor: str,
        workflow_id: str = "N/A",
        metadata: Optional[Dict[str, Any]] = None
    ) -> StartupVersion:
        """Gathers active states, builds the snapshot, computes hash, validates, and persists it."""
        # 1. Fetch startup intelligence profile from database
        profile = db.query(StartupIntelligenceProfile).filter(StartupIntelligenceProfile.startup_id == UUID(startup_id)).first()
        if not profile:
            # Fallback check
            profile = db.query(StartupIntelligenceProfile).filter(StartupIntelligenceProfile.startup_id == startup_id).first()
            if not profile:
                raise VersionValidationError(f"Startup Intelligence Profile not found for startup '{startup_id}'.")

        claims = db.query(StartupClaim).filter(StartupClaim.profile_id == profile.id).all()
        evidence = db.query(StartupEvidence).join(StartupClaim).filter(StartupClaim.profile_id == profile.id).all()
        conflicts = db.query(FieldConflict).filter(FieldConflict.profile_id == profile.id).all()

        # Map DB entities to Pydantic/dict structures
        claims_data = []
        for c in claims:
            claims_data.append({
                "id": str(c.id), "profile_id": str(c.profile_id), "field_id": str(c.field_id),
                "value_string": c.value_string, "value_number": c.value_number, "value_boolean": c.value_boolean,
                "value_date": c.value_date.isoformat() if c.value_date else None, "value_json": c.value_json,
                "confidence_score": c.confidence_score, "validation_status": c.validation_status,
                "reasoning": c.reasoning, "confidence_reason": c.confidence_reason, "merge_reason": c.merge_reason,
                "is_preferred": c.is_preferred, "created_at": c.created_at, "updated_at": c.updated_at
            })

        evidence_data = []
        for ev in evidence:
            evidence_data.append({
                "id": str(ev.id), "claim_id": str(ev.claim_id), "source_document_id": str(ev.source_document_id) if ev.source_document_id else None,
                "page_number": ev.page_number, "section_name": ev.section_name, "evidence_snippet": ev.evidence_snippet,
                "confidence_score": ev.confidence_score, "reasoning": ev.reasoning, "validation_status": ev.validation_status,
                "created_at": ev.created_at
            })

        conflicts_data = []
        for conf in conflicts:
            conflicts_data.append({
                "id": str(conf.id), "profile_id": str(conf.profile_id), "field_id": str(conf.field_id),
                "resolved": conf.resolved, "resolution_reason": conf.resolution_reason,
                "resolved_by": str(conf.resolved_by) if conf.resolved_by else None, "created_at": conf.created_at
            })

        # 2. Fetch Active Observation Graph
        from app.api.dependencies import EvaluationService
        from app.modules.evaluation.graph.graph_serializer import to_json as graph_to_json
        eval_service = EvaluationService(db)
        try:
            graph = eval_service.get_graph(startup_id)
            graph_data = json.loads(graph_to_json(graph))
        except Exception:
            # Reconstruct or generate a blank graph payload
            graph_data = {
                "startup_id": startup_id, "graph_id": startup_id,
                "graph_hash": "empty_graph_hash", "observations": {}
            }

        # 3. Fetch Active Workflow State
        workflow_data = None
        if workflow_id != "N/A":
            wf = get_workflow(workflow_id)
            if wf:
                workflow_data = wf.model_dump()
        else:
            # Check list of workflows to find one for startup_id
            from app.modules.workflow.workflow_queries import list_workflows
            for w in list_workflows():
                if w.startup_id == startup_id:
                    workflow_id = w.workflow_id
                    workflow_data = w.model_dump()
                    break

        # 4. Fetch Portfolio Entry Snapshot
        portfolio_snapshot = None
        portfolio_snapshot_id = "N/A"
        try:
            portfolio_path = os.path.join("uploads", "graphs", "portfolio.json")
            if os.path.exists(portfolio_path):
                with open(portfolio_path, "r", encoding="utf-8") as f:
                    p_data = json.load(f)
                    for entry in p_data.get("entries", []):
                        if entry.get("startup_id") == startup_id:
                            portfolio_snapshot = entry
                            portfolio_snapshot_id = f"PORT-{startup_id}"
                            break
        except Exception:
            pass

        # Extract nested structures from observation graph
        comm_report = graph_data.get("committee_report") or graph_data.get("committee_decision")
        exec_report = graph_data.get("executive_assessment")
        inv_report = graph_data.get("investment_assessment")
        expert_asm = list(graph_data.get("assessments", {}).values())
        risks = list(graph_data.get("risks", {}).values())
        questions = list(graph_data.get("questions", {}).values())

        # Determine version number
        existing = VersionEngine.list_versions(startup_id)
        next_ver = 1
        if existing:
            next_ver = max(v.version_number for v in existing) + 1

        version_id = f"VER-{startup_id}-{next_ver}"
        meta = metadata or {}
        if "user" not in meta and "actor" not in meta:
            meta["user"] = actor
        if "request_id" not in meta:
            meta["request_id"] = f"REQ-{str(uuid.uuid4())[:8].upper()}"

        # Re-map references
        comm_id = (comm_report.get("decision_id") or comm_report.get("decision", {}).get("decision_id")) if comm_report else "N/A"
        exec_id = exec_report.get("assessment_id") if exec_report else "N/A"
        inv_id = inv_report.get("assessment_id") if inv_report else "N/A"

        # Build structures
        version = StartupVersion(
            version_id=version_id,
            startup_id=startup_id,
            startup_name=graph_data.get("startup_name") or "Unknown Startup",
            version_number=next_ver,
            created_at=datetime.utcnow(),
            created_by=actor,
            graph_hash=graph_data.get("graph_hash") or "N/A",
            workflow_id=workflow_id,
            committee_report_id=comm_id or "N/A",
            executive_report_id=exec_id or "N/A",
            investment_report_id=inv_id or "N/A",
            portfolio_snapshot_id=portfolio_snapshot_id or "N/A",
            metadata=meta
        )

        snapshot = VersionSnapshot(
            startup_profile={
                "id": str(profile.id),
                "startup_id": str(profile.startup_id),
                "created_at": profile.created_at,
                "updated_at": profile.updated_at
            },
            observation_graph=graph_data,
            claims=claims_data,
            evidence=evidence_data,
            expert_assessments=expert_asm,
            risks=risks,
            questions=questions,
            conflicts=conflicts_data,
            committee_report=comm_report,
            executive_report=exec_report,
            investment_report=inv_report,
            workflow_state=workflow_data,
            portfolio_snapshot=portfolio_snapshot
        )

        # Validate version
        from app.modules.workflow.workflow_queries import list_workflows
        wf_ids = [w.workflow_id for w in list_workflows()]
        errors = VersionValidator.validate_version(version, snapshot, existing, wf_ids)
        if errors:
            raise VersionValidationError(f"Version validation failed: {'; '.join(errors)}", errors=errors)

        # Persist version
        VersionEngine.persist_snapshot(startup_id, next_ver, version, snapshot)

        # Log security audit entry
        security_audit_service.log(
            actor=actor,
            action="version.create",
            resource=f"/version/{version_id}",
            status="success",
            details={
                "startup": version.startup_name,
                "version_id": version_id,
                "graph_hash": version.graph_hash,
                "workflow_id": workflow_id,
                "request_id": meta.get("request_id")
            }
        )

        # Publish event
        version_events.publish_version_created(startup_id, next_ver, version_id)

        return version

    @staticmethod
    def validate_version(startup_id: str, version_number: int) -> List[str]:
        version, snapshot = VersionEngine.load_version(startup_id, version_number)
        existing = [v for v in VersionEngine.list_versions(startup_id) if v.version_number != version_number]
        from app.modules.workflow.workflow_queries import list_workflows
        wf_ids = [w.workflow_id for w in list_workflows()]
        return VersionValidator.validate_version(version, snapshot, existing, wf_ids)

    @staticmethod
    def rollback_version(
        startup_id: str,
        version_number: int,
        db: Session,
        actor: str,
        role: str,
        reason: str
    ) -> StartupVersion:
        """Rollback active startup states (profile claims, graph file, workflow status) to a target snapshot."""
        # 1. Validate target exists
        filepath = VersionEngine._get_version_path(startup_id, version_number)
        if not os.path.exists(filepath):
            raise VersionValidationError(f"Rollback failed: target version number {version_number} does not exist.")

        # Publish started event
        version_events.publish_rollback_started(startup_id, version_number)

        # Load version data
        version, snapshot = VersionEngine.load_version(startup_id, version_number)

        # 2. Database Transaction: Restore startup profile data
        profile = db.query(StartupIntelligenceProfile).filter(StartupIntelligenceProfile.startup_id == UUID(startup_id)).first()
        if not profile:
            profile = db.query(StartupIntelligenceProfile).filter(StartupIntelligenceProfile.startup_id == startup_id).first()
            if not profile:
                raise VersionValidationError(f"Rollback failed: Startup Intelligence Profile not found.")

        # Delete existing entries
        claim_ids = [c.id for c in db.query(StartupClaim.id).filter(StartupClaim.profile_id == profile.id).all()]
        if claim_ids:
            db.query(StartupEvidence).filter(StartupEvidence.claim_id.in_(claim_ids)).delete(synchronize_session=False)
        db.query(StartupClaim).filter(StartupClaim.profile_id == profile.id).delete(synchronize_session=False)
        db.query(FieldConflict).filter(FieldConflict.profile_id == profile.id).delete(synchronize_session=False)
        db.commit()
        db.expunge_all()

        # Re-fetch profile to associate it with the session
        profile = db.query(StartupIntelligenceProfile).filter(StartupIntelligenceProfile.id == profile.id).first()

        # Re-insert snapshot claims and evidence
        claim_id_map = {}
        for c in snapshot.claims:
            new_claim = StartupClaim(
                id=UUID(c["id"]) if isinstance(c["id"], str) else c["id"],
                profile_id=profile.id,
                field_id=UUID(c["field_id"]) if isinstance(c["field_id"], str) else c["field_id"],
                value_string=c["value_string"],
                value_number=c["value_number"],
                value_boolean=c["value_boolean"],
                value_date=datetime.fromisoformat(c["value_date"]) if c["value_date"] else None,
                value_json=c["value_json"],
                confidence_score=c["confidence_score"],
                validation_status=c["validation_status"],
                reasoning=c["reasoning"],
                confidence_reason=c["confidence_reason"],
                merge_reason=c["merge_reason"],
                is_preferred=c["is_preferred"]
            )
            db.add(new_claim)
            claim_id_map[str(c["id"])] = new_claim

        for ev in snapshot.evidence:
            new_evidence = StartupEvidence(
                id=UUID(ev["id"]) if isinstance(ev["id"], str) else ev["id"],
                claim_id=UUID(ev["claim_id"]) if isinstance(ev["claim_id"], str) else ev["claim_id"],
                source_document_id=UUID(ev["source_document_id"]) if ev["source_document_id"] else None,
                page_number=ev["page_number"],
                section_name=ev["section_name"],
                evidence_snippet=ev["evidence_snippet"],
                confidence_score=ev["confidence_score"],
                reasoning=ev["reasoning"],
                validation_status=ev["validation_status"]
            )
            db.add(new_evidence)

        for conf in snapshot.conflicts:
            new_conflict = FieldConflict(
                id=UUID(conf["id"]) if isinstance(conf["id"], str) else conf["id"],
                profile_id=profile.id,
                field_id=UUID(conf["field_id"]) if isinstance(conf["field_id"], str) else conf["field_id"],
                resolved=conf["resolved"],
                resolution_reason=conf["resolution_reason"],
                resolved_by=UUID(conf["resolved_by"]) if conf["resolved_by"] else None
            )
            db.add(new_conflict)

        db.commit()

        # 3. Overwrite Active Observation Graph File
        from app.api.dependencies import EvaluationService
        eval_service = EvaluationService(db)
        # Deserialize from snapshot representation
        from app.modules.evaluation.graph.graph_serializer import from_json as graph_from_json
        restored_graph = graph_from_json(json.dumps(snapshot.observation_graph))
        eval_service.save_graph(restored_graph)

        # 4. Restore Workflow state
        if snapshot.workflow_state:
            restored_wf = Workflow(**snapshot.workflow_state)
            
            # Record rollback transition detail
            transition_id = f"RB-REST-{str(uuid.uuid4())[:8].upper()}"
            restored_wf.previous_state = restored_wf.current_state
            restored_wf.last_modified_by = actor
            restored_wf.updated_at = datetime.utcnow()
            
            register_workflow(restored_wf)
            
            history_entry = WorkflowHistoryEntry(
                transition_id=transition_id,
                actor=actor,
                role=role,
                previous_state=restored_wf.previous_state,
                new_state=restored_wf.current_state,
                timestamp=datetime.utcnow(),
                reason=f"ROLLBACK to version V{version_number}: {reason}",
                audit_reference=f"audit:{transition_id}"
            )
            register_history_entry(restored_wf.workflow_id, history_entry)

        # Log security audit rollback entry
        security_audit_service.log(
            actor=actor,
            action="version.rollback",
            resource=f"/version/rollback/{version.version_id}",
            status="success",
            details={
                "startup_id": startup_id,
                "version_number": version_number,
                "version_id": version.version_id,
                "reason": reason
            }
        )

        # Publish completed event
        version_events.publish_rollback_completed(startup_id, version_number)

        return version
