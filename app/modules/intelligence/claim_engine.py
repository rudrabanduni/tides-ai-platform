import json
import time
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.enums import DocumentType
from app.modules.documents.models import Document
from app.modules.intelligence.models import (
    KnowledgeFieldRegistry,
    StartupClaim,
    StartupEvidence,
    FieldConflict,
    StartupIntelligenceProfile,
    StartupIntelligenceProfileVersion,
    PipelineStatus
)
from app.modules.intelligence.repository import (
    KnowledgeFieldRegistryRepository,
    StartupClaimRepository,
    StartupEvidenceRepository,
    FieldConflictRepository,
    StartupIntelligenceProfileRepository,
    StartupIntelligenceProfileVersionRepository,
    StartupProcessingStatusRepository
)
from app.modules.intelligence.ai.schemas import DocumentExtraction, ExtractedField
from app.modules.intelligence.events import dispatcher, Event


# --- Confidence Engine ---
class ConfidenceEngine:
    @staticmethod
    def calculate(
        ai_confidence: float,
        doc_type: str,
        has_evidence: bool,
        evidence_snippet: str | None = None
    ) -> tuple[float, str]:
        # Document weights representing source reliability
        doc_weights = {
            "Pitch Deck": 0.85,
            "Business Plan": 0.80,
            "Financial Statement": 0.95,
            "Patent": 0.90,
            "Research Paper": 0.85,
            "Excel Intake": 0.85,
            "Generic Document": 0.70
        }
        doc_weight = doc_weights.get(doc_type, 0.70)

        # Evidence quality multiplier
        evidence_mult = 1.0
        if has_evidence and evidence_snippet:
            snippet_len = len(evidence_snippet)
            if snippet_len > 100:
                evidence_mult = 1.0
            elif snippet_len > 30:
                evidence_mult = 0.9
            else:
                evidence_mult = 0.8
        else:
            evidence_mult = 0.5

        # Formula combining factors
        score = (ai_confidence * 0.4) + (doc_weight * 0.4) + (evidence_mult * 0.2)
        score = min(1.0, max(0.0, score))

        reason = (
            f"Calculated confidence score: {score:.2f} using AI confidence weight (0.4 * {ai_confidence:.2f}), "
            f"document weight (0.4 * {doc_weight:.2f} for {doc_type}) and evidence quality (0.2 * {evidence_mult:.2f})."
        )
        return score, reason


# --- Merge Strategies ---
class BaseMergeStrategy:
    def choose_preferred(self, existing: StartupClaim, new_claim: StartupClaim) -> StartupClaim:
        raise NotImplementedError


class ConfidenceMergeStrategy(BaseMergeStrategy):
    """Prefers the claim with the highest confidence score."""
    def choose_preferred(self, existing: StartupClaim, new_claim: StartupClaim) -> StartupClaim:
        if new_claim.confidence_score > existing.confidence_score:
            return new_claim
        return existing


class RecencyMergeStrategy(BaseMergeStrategy):
    """Prefers the newer claim based on creation timestamp (useful for financial metrics)."""
    def choose_preferred(self, existing: StartupClaim, new_claim: StartupClaim) -> StartupClaim:
        # Default to new_claim if it's newer or same age
        return new_claim


# --- Conflict Engine ---
class ConflictEngine:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.conflicts = FieldConflictRepository(db)
        # Configure merge strategy per field key
        self._strategies = {
            "revenue": RecencyMergeStrategy(),
            "funding_received": RecencyMergeStrategy(),
            "current_revenue": RecencyMergeStrategy(),
            "trl": ConfidenceMergeStrategy()
        }
        self._default_strategy = ConfidenceMergeStrategy()

    def resolve_conflict(
        self,
        profile_id: UUID,
        field_id: UUID,
        field_key: str,
        existing_claims: list[StartupClaim],
        new_claim: StartupClaim
    ) -> None:
        """Compares existing claims with new claim, marks preferred, and logs conflict histories."""
        if not existing_claims:
            new_claim.is_preferred = True
            new_claim.validation_status = "VALIDATED"
            return

        # Find currently preferred claim
        preferred_existing = next((c for c in existing_claims if c.is_preferred), existing_claims[0])

        # Get value for comparison
        val_new = new_claim.value_string or new_claim.value_number or new_claim.value_boolean or new_claim.value_json
        val_existing = preferred_existing.value_string or preferred_existing.value_number or preferred_existing.value_boolean or preferred_existing.value_json

        # Check if values are actually different (conflict detected)
        if val_new != val_existing:
            dispatcher.publish(Event(
                event_name="ConflictDetected",
                payload={
                    "profile_id": str(profile_id),
                    "field_key": field_key,
                    "existing_claim_id": str(preferred_existing.id),
                    "new_claim_id": str(new_claim.id)
                }
            ))

            # Apply merge strategy
            strategy = self._strategies.get(field_key, self._default_strategy)
            winner = strategy.choose_preferred(preferred_existing, new_claim)

            # Record conflict history log
            conflict = FieldConflict(
                profile_id=profile_id,
                field_id=field_id,
                resolved=True,
                resolution_reason=f"Resolved automatically by conflict engine using {type(strategy).__name__}. Preferred value from claim {winner.id}."
            )
            self.conflicts.add(conflict)

            # Set preferred flags
            for claim in existing_claims:
                claim.is_preferred = (claim == winner)
                if claim == winner:
                    claim.validation_status = "VALIDATED"
                elif claim == preferred_existing:
                    claim.validation_status = "CONFLICTING"

            new_claim.is_preferred = (winner == new_claim)
            new_claim.validation_status = "VALIDATED" if (winner == new_claim) else "CONFLICTING"
            new_claim.merge_reason = f"Conflict detected. Winner chosen via {type(strategy).__name__}."
        else:
            # Values are identical, merge them by picking the higher confidence one
            if new_claim.confidence_score > preferred_existing.confidence_score:
                for claim in existing_claims:
                    claim.is_preferred = False
                    claim.validation_status = "SUPERSEDED"
                new_claim.is_preferred = True
                new_claim.validation_status = "VALIDATED"
            else:
                new_claim.is_preferred = False
                new_claim.validation_status = "SUPERSEDED"


# --- Claim & Evidence Engine Service ---
class ClaimEngine:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.registry = KnowledgeFieldRegistryRepository(db)
        self.profiles = StartupIntelligenceProfileRepository(db)
        self.claims = StartupClaimRepository(db)
        self.evidence = StartupEvidenceRepository(db)
        self.profile_versions = StartupIntelligenceProfileVersionRepository(db)
        self.status = StartupProcessingStatusRepository(db)
        self.conflicts = FieldConflictRepository(db)
        self.conflict_engine = ConflictEngine(db)

    def process_extraction(self, startup_id: UUID, extraction: DocumentExtraction, document_id: UUID) -> None:
        """Processes AI extraction result, builds claims and evidence, resolves conflicts, and updates profiles."""
        start_time = time.time()
        # 1. Pipeline Status updates
        status_record = self.status.get_by_startup_pipeline(startup_id, "ai_extraction")
        if status_record:
            self.status.update_progress(status_record.id, "READY_FOR_CLAIMS", 100, PipelineStatus.RUNNING)
            self.db.refresh(status_record)

        # Retrieve or create profile
        profile = self.profiles.get_by_startup(startup_id)
        if not profile:
            profile = StartupIntelligenceProfile(startup_id=startup_id)
            self.profiles.add(profile)
            self.db.flush()

        # Update pipeline stage to CLAIMS_CREATED
        if status_record:
            self.status.update_progress(status_record.id, "CLAIMS_CREATED", 20, PipelineStatus.RUNNING)

        # Retrieve doc type info for confidence calculation
        doc_repo = self.db.query(Document)
        document = doc_repo.filter(Document.id == document_id).first()
        doc_type_str = document.document_type.value if document else "Generic Document"

        # Resolve classification display name
        meta_path = document.file_path + ".meta.json" if document else ""
        import os
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                    doc_type_str = meta.get("classification", doc_type_str)
            except Exception:
                pass

        # Ensure registry is pre-populated with standard keys
        self._ensure_registry_keys()

        # Flat map extracted fields in schemas
        extracted_fields = self._gather_extracted_fields(extraction)

        # Update pipeline stage to EVIDENCE_LINKED
        if status_record:
            self.status.update_progress(status_record.id, "EVIDENCE_LINKED", 40, PipelineStatus.RUNNING)

        # Process each extracted field
        for field_key, ext_field in extracted_fields.items():
            if ext_field is None or ext_field.value is None:
                continue
            registry_entry = self.registry.get_by_key(field_key)
            if not registry_entry:
                continue

            # Calculate final confidence
            has_evidence = bool(ext_field.supporting_evidence)
            final_conf, conf_reason = ConfidenceEngine.calculate(
                ext_field.confidence_score,
                doc_type_str,
                has_evidence,
                ext_field.supporting_evidence
            )

            # Build Claim
            claim = StartupClaim(
                profile_id=profile.id,
                field_id=registry_entry.id,
                confidence_score=final_conf,
                validation_status="PENDING",
                reasoning=ext_field.why_extracted,
                confidence_reason=conf_reason,
                is_preferred=False
            )

            # Set typed values
            val = ext_field.value
            if registry_entry.value_type == "number":
                claim.value_number = float(val) if val is not None else None
            elif registry_entry.value_type == "boolean":
                claim.value_boolean = bool(val) if val is not None else None
            elif registry_entry.value_type == "date":
                # handle date parsing if any
                claim.value_date = val
            elif registry_entry.value_type == "json":
                claim.value_json = val
            else:
                claim.value_string = str(val) if val is not None else None

            self.claims.add(claim)
            self.db.flush()

            dispatcher.publish(Event(
                event_name="ClaimCreated",
                payload={
                    "claim_id": str(claim.id),
                    "profile_id": str(profile.id),
                    "field_key": field_key,
                }
            ))

            # Build Evidence
            evidence = StartupEvidence(
                claim_id=claim.id,
                source_document_id=document_id,
                page_number=ext_field.document_section, # LLM section / page placeholder
                section_name=ext_field.document_section or "General",
                evidence_snippet=ext_field.supporting_evidence or "No direct snippet.",
                confidence_score=final_conf,
                reasoning=f"Why Extracted: {ext_field.why_extracted}\nConfidence Reason: {conf_reason}",
                validation_status="UNVALIDATED"
            )
            self.evidence.add(evidence)
            self.db.flush()

            dispatcher.publish(Event(
                event_name="EvidenceCreated",
                payload={
                    "evidence_id": str(evidence.id),
                    "claim_id": str(claim.id),
                }
            ))

            # Run conflict resolution (merging strategies)
            existing_claims = list(self.claims.get_for_field(profile.id, registry_entry.id))
            # Remove new claim from list for conflict comparison
            existing_claims = [c for c in existing_claims if c.id != claim.id]

            if status_record:
                self.status.update_progress(status_record.id, "MERGING", 60, PipelineStatus.RUNNING)

            self.conflict_engine.resolve_conflict(
                profile.id, registry_entry.id, field_key, existing_claims, claim
            )
            self.db.flush()

        # Update stage to PROFILE_UPDATED
        if status_record:
            self.status.update_progress(status_record.id, "PROFILE_UPDATED", 80, PipelineStatus.RUNNING)

        dispatcher.publish(Event(
            event_name="ProfileUpdated",
            payload={
                "profile_id": str(profile.id),
                "startup_id": str(startup_id),
            }
        ))

        # Create Profile version snapshot if claims changed
        self._create_snapshot_version(profile)

        # Update pipeline status to READY_FOR_EVALUATION
        if status_record:
            self.status.update_progress(status_record.id, "READY_FOR_EVALUATION", 100, PipelineStatus.COMPLETED)
            self.status.mark_completed(status_record.id, int((time.time() - start_time) * 1000))

        self.db.commit()

        dispatcher.publish(Event(
            event_name="MergeCompleted",
            payload={"profile_id": str(profile.id)}
        ))

    def _ensure_registry_keys(self) -> None:
        """Pre-populates the registry with standard fields if not present."""
        registry_keys = {
            "founder_names": ("Founder Names", "string"),
            "leadership_experience": ("Leadership Experience", "string"),
            "domain_expertise": ("Domain Expertise", "string"),
            "commitment_level": ("Commitment Level", "string"),
            "description": ("Product Description", "string"),
            "problem_solved": ("Problem Solved", "string"),
            "solution_value_prop": ("Solution Value Proposition", "string"),
            "customers": ("Customers Details", "string"),
            "business_model": ("Business Model Description", "string"),
            "target_market": ("Target Market", "string"),
            "market_size": ("Market Size Description", "string"),
            "competitors": ("Competitors List", "string"),
            "competition_analysis": ("Competition Analysis", "string"),
            "revenue_model": ("Revenue Model Details", "string"),
            "funding_received": ("Total Funding Received", "number"),
            "current_revenue": ("Current Revenue", "number"),
            "financial_metrics": ("Financial Metrics Summary", "string"),
            "trl_level": ("Technology Readiness Level", "number"),
            "ip_status": ("Intellectual Property Status", "string"),
        }

        for key, (name, val_type) in registry_keys.items():
            if not self.registry.get_by_key(key):
                entry = KnowledgeFieldRegistry(
                    field_key=key,
                    field_name=name,
                    value_type=val_type,
                    is_active=True
                )
                self.registry.add(entry)
        self.db.flush()

    def _gather_extracted_fields(self, ext: DocumentExtraction) -> dict[str, ExtractedField]:
        """Flat maps fields from the DocumentExtraction model to registry keys."""
        return {
            "founder_names": ext.founder.founder_names,
            "leadership_experience": ext.founder.leadership_experience,
            "domain_expertise": ext.founder.domain_expertise,
            "commitment_level": ext.founder.commitment_level,
            "description": ext.product.description,
            "problem_solved": ext.product.problem_solved,
            "solution_value_prop": ext.product.solution_value_prop,
            "customers": ext.product.customers,
            "business_model": ext.product.business_model,
            "target_market": ext.market.target_market,
            "market_size": ext.market.market_size,
            "competitors": ext.market.competitors,
            "competition_analysis": ext.market.competition_analysis,
            "revenue_model": ext.financial.revenue_model,
            "funding_received": ext.financial.funding_received,
            "current_revenue": ext.financial.current_revenue,
            "financial_metrics": ext.financial.financial_metrics,
            "trl_level": ext.technology.trl_level,
            "ip_status": ext.technology.ip_status,
        }

    def _create_snapshot_version(self, profile: StartupIntelligenceProfile) -> None:
        """Generates a JSON snapshot of preferred validated claims and writes a version record."""
        preferred_claims = self.claims.list_preferred_for_profile(profile.id)
        
        snapshot = {}
        for claim in preferred_claims:
            registry_entry = self.registry.get(claim.field_id)
            if not registry_entry:
                continue

            val = claim.value_string or claim.value_number or claim.value_boolean or claim.value_json
            snapshot[registry_entry.field_key] = val

        # Check if snapshot differs from latest version
        latest = self.profile_versions.latest_version(profile.id)
        if not latest or latest.profile_snapshot != snapshot:
            version = self.profile_versions.create_version(
                profile_id=profile.id,
                snapshot=snapshot
            )
            self.db.flush()

            dispatcher.publish(Event(
                event_name="ProfileVersionCreated",
                payload={
                    "version_id": str(version.id),
                    "profile_id": str(profile.id),
                    "version_number": version.version_number
                }
            ))
