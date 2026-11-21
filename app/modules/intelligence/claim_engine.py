import json
import re
import time
from datetime import datetime

from app.modules.intelligence.evidence_locator import locate_passage
from uuid import UUID, uuid4
from typing import Any, Dict, List, Optional
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
from app.services.ai.real_pipeline import make_extracted_string
from app.modules.intelligence.ai.schemas import DocumentExtraction, ExtractedField, ExtractedString
from app.modules.ai.orchestrator.startup_profile_extraction import StartupProfileExtraction
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
            "trl": ConfidenceMergeStrategy(),
            "ps_09_current_trl": ConfidenceMergeStrategy(),
            "bc_09_current_revenue": RecencyMergeStrategy(),
            "fi_08_funding_raised": RecencyMergeStrategy(),
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

            # Parse page number if digits exist in document_section, otherwise default to None
            parsed_pg_num = None
            if ext_field.document_section:
                digits = "".join(filter(str.isdigit, str(ext_field.document_section)))
                if digits:
                    parsed_pg_num = int(digits)

            # Build Evidence
            evidence = StartupEvidence(
                claim_id=claim.id,
                source_document_id=document_id,
                page_number=parsed_pg_num,
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

    def process_canonical_profile(
        self,
        startup_id: UUID,
        profile_data: StartupProfileExtraction,
        document_id: UUID,
        evaluation_id: str | None = None
    ) -> None:
        """Processes 87-criteria canonical StartupProfileExtraction, builds claims and evidence,
        resolves conflicts, updates legacy compatible keys, and snapshots profile.
        """
        start_time = time.time()
        status_record = self.status.get_by_startup_pipeline(startup_id, "ai_extraction")
        if status_record:
            self.status.update_progress(status_record.id, "READY_FOR_CLAIMS", 100, PipelineStatus.RUNNING)
            self.db.refresh(status_record)

        profile = self.profiles.get_by_startup(startup_id)
        if not profile:
            profile = StartupIntelligenceProfile(startup_id=startup_id)
            self.profiles.add(profile)
            self.db.flush()

        if status_record:
            self.status.update_progress(status_record.id, "CLAIMS_CREATED", 20, PipelineStatus.RUNNING)

        doc_repo = self.db.query(Document)
        document = doc_repo.filter(Document.id == document_id).first()
        doc_type_str = document.document_type.value if document else "Pitch Deck"

        self._ensure_registry_keys()
        canonical_items = self._gather_canonical_profile_fields(profile_data)
        # Documents of THIS startup only, used to ground every extracted value in real text.
        grounding_docs = [
            d for d in self.db.query(Document).filter(Document.startup_id == startup_id).all()
            if (d.parsed_text or "").strip()
        ]
        if document is not None and document not in grounding_docs and (document.parsed_text or "").strip():
            grounding_docs.insert(0, document)

        if status_record:
            self.status.update_progress(status_record.id, "EVIDENCE_LINKED", 40, PipelineStatus.RUNNING)

        for field_key, item in canonical_items.items():
            if item is None or item["value"] is None:
                continue
            registry_entry = self.registry.get_by_key(field_key)
            if not registry_entry:
                continue

            val = item["value"]
            why_ext = item.get("why_extracted") or "Canonical 87-criteria extraction"
            sec_name = item.get("document_section") or "Pitch Deck"
            base_conf = float(item.get("confidence_score", 0.9))
            # Evidence grounding: keep a snippet ONLY when the value is found in a submitted
            # document. The previous behaviour stored "Disclosed in pitch deck: <value>", i.e. the
            # claim was its own evidence, which overstated documentary support.
            snippet = None
            grounded_doc_id = document_id
            located_page = None
            for gdoc in grounding_docs:
                passage, page_no = locate_passage(gdoc.parsed_text or "", val)
                if passage:
                    snippet, grounded_doc_id, located_page = passage, gdoc.id, page_no
                    break
            if located_page:
                sec_name = f"Page {located_page}"

            final_conf, conf_reason = ConfidenceEngine.calculate(
                base_conf,
                doc_type_str,
                has_evidence=bool(snippet),
                evidence_snippet=snippet
            )

            claim = StartupClaim(
                profile_id=profile.id,
                field_id=registry_entry.id,
                confidence_score=final_conf,
                validation_status="PENDING",
                reasoning=why_ext,
                confidence_reason=conf_reason,
                is_preferred=False
            )

            if registry_entry.value_type == "number":
                try:
                    if isinstance(val, (int, float)):
                        claim.value_number = float(val)
                    else:
                        num_match = re.search(r"[-+]?\d*\.?\d+", str(val).replace(",", ""))
                        claim.value_number = float(num_match.group(0)) if num_match else None
                except Exception:
                    claim.value_number = None
            elif registry_entry.value_type == "boolean":
                claim.value_boolean = bool(val)
            elif registry_entry.value_type == "date":
                claim.value_date = val if isinstance(val, datetime) else None
            elif registry_entry.value_type == "json":
                claim.value_json = val
            else:
                claim.value_string = str(val)[:1000]

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

            parsed_pg_num = None
            digits = "".join(filter(str.isdigit, str(sec_name)))
            if digits:
                try:
                    parsed_pg_num = int(digits)
                except ValueError:
                    parsed_pg_num = None

            evidence = StartupEvidence(
                claim_id=claim.id,
                source_document_id=grounded_doc_id,
                page_number=located_page if located_page else (parsed_pg_num if snippet else None),
                section_name=sec_name,
                evidence_snippet=snippet,
                confidence_score=final_conf,
                reasoning=f"Why Extracted: {why_ext}\nConfidence Reason: {conf_reason}",
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

            existing_claims = list(self.claims.get_for_field(profile.id, registry_entry.id))
            existing_claims = [c for c in existing_claims if c.id != claim.id]

            if status_record:
                self.status.update_progress(status_record.id, "MERGING", 60, PipelineStatus.RUNNING)

            self.conflict_engine.resolve_conflict(
                profile.id, registry_entry.id, field_key, existing_claims, claim
            )
            self.db.flush()

        if status_record:
            self.status.update_progress(status_record.id, "PROFILE_UPDATED", 80, PipelineStatus.RUNNING)

        dispatcher.publish(Event(
            event_name="ProfileUpdated",
            payload={
                "profile_id": str(profile.id),
                "startup_id": str(startup_id),
            }
        ))

        self._create_snapshot_version(profile)

        if status_record:
            self.status.update_progress(status_record.id, "READY_FOR_EVALUATION", 100, PipelineStatus.COMPLETED)
            self.status.mark_completed(status_record.id, int((time.time() - start_time) * 1000))

        self.db.commit()

        dispatcher.publish(Event(
            event_name="MergeCompleted",
            payload={"profile_id": str(profile.id)}
        ))

    def _ensure_registry_keys(self) -> None:
        """Pre-populates the registry with standard legacy fields and all 87 canonical criteria."""
        registry_keys = {
            # --- Legacy Compatibility Keys ---
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
            "patents": ("Patents Status", "string"),
            "ownership_declarations": ("Ownership Declarations", "string"),
            "licensing_agreements": ("Licensing Agreements", "string"),
            "differentiation_claims": ("Differentiation Claims", "string"),
            "moat_claims": ("Moat Claims", "string"),
            "technical_risk_claims": ("Technical Risk Claims", "string"),
            "market_risk_claims": ("Market Risk Claims", "string"),
            "financial_runway_risks": ("Financial Runway Risks", "string"),
            "execution_risk_claims": ("Execution Risk Claims", "string"),

            # --- Canonical Criteria: Cover & Metadata (CM-01 to CM-06) ---
            "cm_01_company_name": ("Startup Name", "string"),
            "cm_02_tagline": ("Tagline", "string"),
            "cm_03_sector": ("Sector / Industry Vertical", "string"),
            "cm_04_stage": ("Current Stage", "string"),
            "cm_05_geography": ("Geography / Location", "string"),
            "cm_06_application_date": ("Application Date", "string"),

            # --- Canonical Criteria: Domain 1 Problem & Solution (PS-01 to PS-13) ---
            "ps_01_problem_statement": ("Core Problem Statement", "string"),
            "ps_02_who_is_affected": ("Who is Affected", "string"),
            "ps_03_current_workarounds": ("Current Workarounds", "string"),
            "ps_04_evidence_of_problem": ("Evidence of the Problem", "string"),
            "ps_05_why_problem_persists": ("Why the Problem Persists", "string"),
            "ps_06_solution_description": ("Solution Description", "string"),
            "ps_07_key_features_benefits": ("Three Key Features & Benefits", "json"),
            "ps_08_unique_value_proposition": ("Unique Value Proposition", "string"),
            "ps_09_current_trl": ("Current Technology Readiness Level", "number"),
            "ps_09_trl_justification": ("TRL Justification", "string"),
            "ps_10_demo_prototype_link": ("Demo / Prototype Link", "string"),
            "ps_11_prototype_stage": ("Prototype Stage", "string"),
            "ps_12_technical_architecture": ("Technical Architecture", "string"),
            "ps_13_technical_validation_results": ("Technical Validation & Results", "string"),

            # --- Canonical Criteria: Domain 2 Market Opportunity (MO-01 to MO-10) ---
            "mo_01_tam": ("Total Addressable Market (TAM)", "string"),
            "mo_02_sam": ("Serviceable Addressable Market (SAM)", "string"),
            "mo_03_som_3_5_year": ("Serviceable Obtainable Market (SOM)", "string"),
            "mo_04_market_cagr": ("Market Growth Rate / CAGR", "string"),
            "mo_04_cagr_source": ("Market CAGR Source", "string"),
            "mo_05_key_market_drivers": ("Key Market Drivers", "json"),
            "mo_06_geographic_focus": ("Geographic Focus & Local Market Size", "string"),
            "mo_07_competitor_1": ("Competitor 1", "json"),
            "mo_08_competitor_2": ("Competitor 2", "json"),
            "mo_09_competitor_3_international": ("Competitor 3 (International)", "json"),
            "mo_07_competitor_details": ("Competitor Benchmark Details (Min 3)", "json"),
            "mo_08_competition_summary": ("Competition Summary", "string"),
            "mo_10_sustainable_competitive_advantage": ("Sustainable Competitive Advantage", "string"),

            # --- Canonical Criteria: Domain 3 Founder & Team Capability (FT-01 to FT-13) ---
            "ft_01_founder_details": ("Structured Founder Records", "json"),
            "ft_01_founder_1_identity_role": ("Founder 1 Identity & Role", "string"),
            "ft_01_founder_names": ("Founder Names", "string"),
            "ft_01_founder_roles": ("Founder Roles", "json"),
            "ft_02_founder_1_linkedin": ("Founder 1 LinkedIn Profile", "string"),
            "ft_03_founder_1_education": ("Founder 1 Education", "string"),
            "ft_04_founder_1_experience": ("Founder 1 Experience & Domain Expertise", "string"),
            "ft_04_team_summary": ("Team Capabilities & Domain Expertise", "string"),
            "ft_05_founder_1_entrepreneurship": ("Founder 1 Prior Entrepreneurship & Execution", "string"),
            "ft_06_co_founders": ("Co-Founders (Multiple Founders)", "json"),
            "ft_07_core_team": ("Core Team Members & Key Credentials", "json"),
            "ft_08_critical_skill_gaps": ("Critical Skill Gaps", "json"),
            "ft_09_hiring_plan": ("Hiring Plan & Timing (Next 3-6 Quarters)", "json"),
            "ft_10_advisors": ("Named Mentors & Advisors", "json"),
            "ft_11_primary_mentor_contribution": ("Primary Mentor & Contribution", "string"),
            "ft_12_secondary_mentor_contribution": ("Secondary Mentor / Institutional Support", "string"),
            "ft_13_institutional_affiliations": ("Institutional Affiliations", "json"),

            # --- Canonical Criteria: Domain 4 Business Model & Commercialisation (BC-01 to BC-13) ---
            "bc_01_business_model": ("Business Model Summary", "string"),
            "bc_01_revenue_model": ("Revenue Model", "string"),
            "bc_02_pricing_strategy_unit": ("Pricing & Pricing Unit", "string"),
            "bc_03_customer_acquisition_channels": ("Customer Acquisition Channels", "json"),
            "bc_04_cac": ("Customer Acquisition Cost (CAC)", "string"),
            "bc_05_expected_gross_margin": ("Expected Gross Margin", "string"),
            "bc_06_payback_period_months": ("Customer Payback Period", "string"),
            "bc_07_path_to_first_10l_10k": ("Concrete Path to First ₹10 Lakh / $10k", "string"),
            "bc_08_current_users": ("Current Users / Free Trials", "string"),
            "bc_08_paying_customers": ("Paying Customers", "string"),
            "bc_08_current_users_and_paying_customers": ("Current Users and Paying Customers", "json"),
            "bc_09_current_revenue": ("Revenue to Date", "string"),
            "bc_10_pilot_agreements": ("Letters of Intent (LOIs) & Pilot Agreements", "json"),
            "bc_11_awards_grants_recognition": ("Awards, Grants & Recognition", "json"),
            "bc_12_research_validation": ("Research Validation & Publications", "json"),
            "bc_13_customer_quotes": ("Customer Quotes & Testimonials", "json"),

            # --- Canonical Criteria: Domain 5 Innovation, IP & Impact (II-01 to II-11) ---
            "ii_01_proprietary_technology_moat": ("Proprietary Technology & Core Innovation", "string"),
            "ii_02_data_advantage": ("Data Advantage", "string"),
            "ii_03_network_effects": ("Network Effects", "string"),
            "ii_04_switching_costs": ("Switching Costs", "string"),
            "ii_05_brand_community_moat": ("Brand & Community Moat", "string"),
            "ii_06_regulatory_licensing_barriers": ("Regulatory & Licensing Barriers", "string"),
            "ii_07_patent_details": ("Patent Filing Details", "json"),
            "ii_07_patents_summary": ("Patent Summary", "string"),
            "ii_07_ip_status_patents": ("IP Status (Patents, Trademarks, Secrets)", "string"),
            "ii_08_primary_impact": ("Primary Social, Environmental or Economic Impact", "string"),
            "ii_09_sdg_alignments": ("SDG Alignment & Explanation", "json"),
            "ii_10_impact_metrics": ("Measurable Impact Metrics", "json"),
            "ii_11_potential_negative_effects_mitigation": ("Potential Negative Effects & Mitigation", "string"),

            # --- Canonical Criteria: Domain 6 Financials & Incubation Support (FI-01 to FI-21) ---
            "fi_01_three_year_revenue": ("Three-Year Revenue Projections", "json"),
            "fi_02_three_year_gross_margin": ("Three-Year Gross Margin Projections", "json"),
            "fi_03_three_year_customers": ("Three-Year Customer Count Projections", "json"),
            "fi_04_three_year_team_size": ("Three-Year Team-Size Projections", "json"),
            "fi_05_burn_rate": ("Monthly Cash Burn", "string"),
            "fi_06_break_even_timing": ("Break-Even Timing", "string"),
            "fi_07_financial_assumptions": ("Key Financial Assumptions", "json"),
            "fi_08_funding_raised": ("External Funding Received to Date (Optional)", "string"),
            "fi_09_current_monthly_operating_costs": ("Current Monthly Operating Costs", "string"),
            "fi_10_lab_facilities_requirements": ("Lab & Facilities Requirements", "json"),
            "fi_11_mentorship_expertise_needed": ("Mentorship & Technical Expertise Needed", "json"),
            "fi_12_industry_connections_needed": ("Industry Connections Needed", "json"),
            "fi_13_legal_ip_support_needed": ("Legal & IP Support Requirements", "json"),
            "fi_14_market_access_pilot_support_needed": ("Market Access & Pilot Support", "json"),
            "fi_15_training_skill_building_needed": ("Training & Skill-Building Needs", "json"),
            "fi_16_six_quarter_product_roadmap": ("Six-Quarter Product Roadmap", "json"),
            "fi_17_six_quarter_market_roadmap": ("Six-Quarter Market Roadmap", "json"),
            "fi_18_six_quarter_team_roadmap": ("Six-Quarter Team Roadmap", "json"),
            "fi_19_six_quarter_funding_roadmap": ("Six-Quarter Funding Roadmap", "json"),
            "fi_20_contact_info": ("Contact Information", "json"),
            "fi_21_applicant_declaration": ("Applicant Declaration, Signature & Date", "json"),
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

    def _gather_canonical_profile_fields(self, p: StartupProfileExtraction) -> dict[str, dict[str, Any]]:
        """Maps all 87 canonical criteria and legacy compatibility keys from StartupProfileExtraction."""
        def item(val: Any, why: str = "Canonical Extraction", snip: str | None = None, conf: float = 0.9, sec: str = "Pitch Deck"):
            if snip is None:
                if val is not None:
                    snip = f"Disclosed in pitch deck: {str(val)[:250]}"
                else:
                    snip = "Disclosed in pitch deck."
            if hasattr(val, "model_dump"):
                dumped = val.model_dump()
                return {"value": dumped, "why_extracted": why, "supporting_evidence": snip, "confidence_score": conf, "document_section": sec}
            elif isinstance(val, list) and val and hasattr(val[0], "model_dump"):
                dumped = [x.model_dump() for x in val]
                return {"value": dumped, "why_extracted": why, "supporting_evidence": snip, "confidence_score": conf, "document_section": sec}
            return {"value": val, "why_extracted": why, "supporting_evidence": snip, "confidence_score": conf, "document_section": sec}

        # Helper to safely extract numeric funding
        funding_str = p.funding_raised if p.funding_raised is not None else "0"
        funding_float = 0.0
        try:
            num_m = re.search(r"[-+]?\d*\.?\d+", str(funding_str).replace(",", ""))
            if num_m:
                funding_float = float(num_m.group(0))
        except Exception:
            funding_float = 0.0

        # Helper for revenue
        rev_str = p.current_revenue if p.current_revenue is not None else "0"
        rev_float = 0.0
        try:
            rev_m = re.search(r"[-+]?\d*\.?\d+", str(rev_str).replace(",", ""))
            if rev_m:
                rev_float = float(rev_m.group(0))
        except Exception:
            rev_float = 0.0

        founder_names_str = ", ".join(p.founders) if p.founders else (
            ", ".join(f.name for f in p.founder_details) if p.founder_details else None
        )
        comp_names_str = p.competition or (
            ", ".join(c.name for c in p.competitor_details) if p.competitor_details else None
        )

        patents_summary = p.patents or (
            "No IP filed" if not p.patent_details else f"{len(p.patent_details)} patent(s) recorded"
        )

        return {
            # --- Cover Metadata (CM-01 to CM-06) ---
            "cm_01_company_name": item(p.company_name, "Company Name", sec="Cover"),
            "cm_02_tagline": item(p.tagline, "Tagline / Elevator Pitch", sec="Cover"),
            "cm_03_sector": item(p.sector, "Sector classification", sec="Cover"),
            "cm_04_stage": item(p.stage, "Current operational stage", sec="Cover"),
            "cm_05_geography": item(p.geography, "Operating location", sec="Cover"),
            "cm_06_application_date": item(p.application_date, "Submission date", sec="Cover"),

            # --- Domain 1: Problem & Solution (PS-01 to PS-13) ---
            "ps_01_problem_statement": item(p.problem_statement, "Problem statement", sec="Slide 3"),
            "ps_02_who_is_affected": item(p.who_is_affected, "Affected demographic / personas", sec="Slide 3"),
            "ps_03_current_workarounds": item(p.current_workarounds, "Current workarounds & inertia", sec="Slide 3"),
            "ps_04_evidence_of_problem": item(p.evidence_of_problem, "Quantitative evidence of pain", sec="Slide 3"),
            "ps_05_why_problem_persists": item(p.why_problem_persists, "Structural persistence barrier", sec="Slide 3"),
            "ps_06_solution_description": item(p.solution, "Solution overview", sec="Slide 4"),
            "ps_07_key_features_benefits": item(p.key_features_benefits if p.key_features_benefits else None, "Three key features & benefits", sec="Slide 4"),
            "ps_08_unique_value_proposition": item(p.unique_value_proposition or p.solution, "Unique Value Proposition", sec="Slide 4"),
            "ps_09_current_trl": item(p.current_trl, "Self-reported TRL", sec="Slide 5"),
            "ps_09_trl_justification": item(p.trl_justification, "TRL justification", sec="Slide 5"),
            "ps_10_demo_prototype_link": item(p.demo_prototype_link, "Demo / prototype link (conditional)", sec="Slide 5"),
            "ps_11_prototype_stage": item(p.prototype_stage, "Prototype maturity stage", sec="Slide 5"),
            "ps_12_technical_architecture": item(p.technology, "Technical architecture", sec="Slide 5"),
            "ps_13_technical_validation_results": item(p.technical_validation_results, "Technical validation & test data", sec="Slide 5"),

            # --- Domain 2: Market Opportunity (MO-01 to MO-10) ---
            "mo_01_tam": item(p.market_size, "Total Addressable Market (TAM)", sec="Slide 6"),
            "mo_02_sam": item(p.sam, "Serviceable Addressable Market (SAM)", sec="Slide 6"),
            "mo_03_som_3_5_year": item(p.som_3_5_year, "Serviceable Obtainable Market (SOM)", sec="Slide 6"),
            "mo_04_market_cagr": item(p.market_cagr, "Market CAGR percentage", sec="Slide 6"),
            "mo_04_cagr_source": item(p.cagr_source, "CAGR research citation", sec="Slide 6"),
            "mo_05_key_market_drivers": item(p.key_market_drivers if p.key_market_drivers else None, "Market growth drivers", sec="Slide 6"),
            "mo_06_geographic_focus": item(p.market, "Geographic focus and local market", sec="Slide 6"),
            "mo_07_competitor_1": item(p.competitor_details[0].model_dump() if p.competitor_details and len(p.competitor_details) > 0 else None, "Competitor 1", sec="Slide 7"),
            "mo_08_competitor_2": item(p.competitor_details[1].model_dump() if p.competitor_details and len(p.competitor_details) > 1 else None, "Competitor 2", sec="Slide 7"),
            "mo_09_competitor_3_international": item(p.competitor_details[2].model_dump() if p.competitor_details and len(p.competitor_details) > 2 else None, "Competitor 3 (International)", sec="Slide 7"),
            "mo_07_competitor_details": item(p.competitor_details if p.competitor_details else None, "Competitor benchmark details", sec="Slide 7"),
            "mo_08_competition_summary": item(p.competition, "Competition landscape summary", sec="Slide 7"),
            "mo_10_sustainable_competitive_advantage": item(p.sustainable_competitive_advantage, "Sustainable competitive moat", sec="Slide 7"),

            # --- Domain 3: Founder & Team Capability (FT-01 to FT-13) ---
            "ft_01_founder_details": item(p.founder_details if p.founder_details else None, "Multi-founder records", sec="Slide 8"),
            "ft_01_founder_1_identity_role": item(f"{p.founder_details[0].name} ({p.founder_details[0].role})" if p.founder_details and len(p.founder_details) > 0 else (p.founders[0] if p.founders else None), "Founder 1 Identity & Role", sec="Slide 8"),
            "ft_01_founder_names": item(founder_names_str, "Founder names", sec="Slide 8"),
            "ft_01_founder_roles": item(p.founder_roles if p.founder_roles else None, "Founder roles", sec="Slide 8"),
            "ft_02_founder_1_linkedin": item(p.founder_details[0].linkedin_url if p.founder_details and len(p.founder_details) > 0 else None, "Founder 1 LinkedIn Profile", sec="Slide 8"),
            "ft_03_founder_1_education": item(f"{p.founder_details[0].education_degree or ''}, {p.founder_details[0].education_institution or ''} ({p.founder_details[0].graduation_year or ''})".strip(', () ') if p.founder_details and len(p.founder_details) > 0 else None, "Founder 1 Education", sec="Slide 8"),
            "ft_04_founder_1_experience": item(p.founder_details[0].relevant_experience if p.founder_details and len(p.founder_details) > 0 else p.team, "Founder 1 Experience & Domain Expertise", sec="Slide 8"),
            "ft_04_team_summary": item(p.team, "Team capability summary", sec="Slide 8"),
            "ft_05_founder_1_entrepreneurship": item(p.founder_details[0].prior_entrepreneurship if p.founder_details and len(p.founder_details) > 0 else None, "Founder 1 Prior Entrepreneurship", sec="Slide 8"),
            "ft_06_co_founders": item([f.model_dump() for f in p.founder_details[1:]] if p.founder_details and len(p.founder_details) > 1 else None, "Co-Founders (Multiple Founders)", sec="Slide 8"),
            "ft_07_core_team": item(p.core_team if p.core_team else None, "Core team members", sec="Slide 9"),
            "ft_08_critical_skill_gaps": item(p.critical_skill_gaps if p.critical_skill_gaps else None, "Critical skill gaps", sec="Slide 9"),
            "ft_09_hiring_plan": item(p.hiring_plan if p.hiring_plan else None, "Hiring roadmap", sec="Slide 9"),
            "ft_10_advisors": item(p.advisors if p.advisors else None, "Named mentors and advisors", sec="Slide 10"),
            "ft_11_primary_mentor_contribution": item(p.primary_mentor_contribution, "Primary mentor contribution", sec="Slide 10"),
            "ft_12_secondary_mentor_contribution": item(p.secondary_mentor_contribution, "Secondary mentor support", sec="Slide 10"),
            "ft_13_institutional_affiliations": item(p.institutional_affiliations if p.institutional_affiliations else None, "Institutional affiliations", sec="Slide 10"),

            # --- Domain 4: Business Model & Commercialisation (BC-01 to BC-13) ---
            "bc_01_business_model": item(p.business_model, "Business model description", sec="Slide 11"),
            "bc_01_revenue_model": item(p.revenue_model, "Revenue monetization model", sec="Slide 11"),
            "bc_02_pricing_strategy_unit": item(p.pricing_strategy_unit, "Pricing & unit metrics", sec="Slide 11"),
            "bc_03_customer_acquisition_channels": item(p.customer_acquisition_channels if p.customer_acquisition_channels else None, "GTM acquisition channels", sec="Slide 11"),
            "bc_04_cac": item(p.cac, "Customer Acquisition Cost", sec="Slide 11"),
            "bc_05_expected_gross_margin": item(p.expected_gross_margin, "Expected gross margin", sec="Slide 11"),
            "bc_06_payback_period_months": item(p.payback_period_months, "Payback period in months", sec="Slide 11"),
            "bc_07_path_to_first_10l_10k": item(p.path_to_first_10l_10k, "First ₹10 Lakh / $10k commercial path", sec="Slide 11"),
            "bc_08_current_users": item(p.current_users, "Current active/trial users", sec="Slide 12"),
            "bc_08_paying_customers": item(p.paying_customers, "Paying customers count", sec="Slide 12"),
            "bc_08_current_users_and_paying_customers": item({"current_users": p.current_users, "paying_customers": p.paying_customers} if (p.current_users is not None or p.paying_customers is not None) else None, "Current Users and Paying Customers", sec="Slide 12"),
            "bc_09_current_revenue": item(p.current_revenue, "Revenue to date", sec="Slide 12"),
            "bc_10_pilot_agreements": item(p.pilot_agreements if p.pilot_agreements else None, "Pilot agreements & LOIs", sec="Slide 12"),
            "bc_11_awards_grants_recognition": item(p.awards_grants_recognition if p.awards_grants_recognition else None, "Awards, grants, recognition", sec="Slide 12"),
            "bc_12_research_validation": item(p.research_validation if p.research_validation else None, "Research papers & clinical trials", sec="Slide 12"),
            "bc_13_customer_quotes": item(p.customer_quotes if p.customer_quotes else None, "Customer testimonials", sec="Slide 12"),

            # --- Domain 5: Innovation, IP & Impact (II-01 to II-11) ---
            "ii_01_proprietary_technology_moat": item(p.proprietary_technology_moat or p.technology, "Proprietary innovation", sec="Slide 13"),
            "ii_02_data_advantage": item(p.data_advantage, "Proprietary data flywheel", sec="Slide 13"),
            "ii_03_network_effects": item(p.network_effects, "Network effects", sec="Slide 13"),
            "ii_04_switching_costs": item(p.switching_costs, "Switching cost moat", sec="Slide 13"),
            "ii_05_brand_community_moat": item(p.brand_community_moat, "Brand & community moat", sec="Slide 13"),
            "ii_06_regulatory_licensing_barriers": item(p.regulatory_licensing_barriers, "Regulatory compliance barriers", sec="Slide 13"),
            "ii_07_patent_details": item(p.patent_details if p.patent_details else None, "Patent filing details", sec="Slide 13"),
            "ii_07_patents_summary": item(patents_summary, "Patent status summary", sec="Slide 13"),
            "ii_07_ip_status_patents": item(patents_summary, "IP Status (Patents, Trademarks, Secrets)", sec="Slide 13"),
            "ii_08_primary_impact": item(p.primary_impact, "Primary social or economic impact", sec="Slide 14"),
            "ii_09_sdg_alignments": item(p.sdg_alignments if p.sdg_alignments else None, "UN SDG alignment", sec="Slide 14"),
            "ii_10_impact_metrics": item(p.impact_metrics if p.impact_metrics else None, "Measurable impact KPIs", sec="Slide 14"),
            "ii_11_potential_negative_effects_mitigation": item(p.potential_negative_effects_mitigation, "Negative externality mitigation", sec="Slide 14"),

            # --- Domain 6: Financials & Incubation Support (FI-01 to FI-21) ---
            "fi_01_three_year_revenue": item(p.three_year_revenue, "Three-year revenue projections", sec="Slide 15"),
            "fi_02_three_year_gross_margin": item(p.three_year_gross_margin, "Three-year margin projections", sec="Slide 15"),
            "fi_03_three_year_customers": item(p.three_year_customers, "Three-year customer projections", sec="Slide 15"),
            "fi_04_three_year_team_size": item(p.three_year_team_size, "Three-year headcount projections", sec="Slide 15"),
            "fi_05_burn_rate": item(p.burn_rate, "Monthly net cash burn", sec="Slide 15"),
            "fi_06_break_even_timing": item(p.break_even_timing, "Break-even projected timing", sec="Slide 15"),
            "fi_07_financial_assumptions": item(p.financial_assumptions if p.financial_assumptions else None, "Core financial assumptions", sec="Slide 15"),
            "fi_08_funding_raised": item(p.funding_raised, "External funding (explicitly optional)", sec="Slide 15"),
            "fi_09_current_monthly_operating_costs": item(p.current_monthly_operating_costs, "Operating cost breakdown", sec="Slide 15"),
            "fi_10_lab_facilities_requirements": item(p.lab_facilities_requirements if p.lab_facilities_requirements else None, "Lab & facility needs", sec="Slide 16"),
            "fi_11_mentorship_expertise_needed": item(p.mentorship_expertise_needed if p.mentorship_expertise_needed else None, "Faculty/mentorship requests", sec="Slide 16"),
            "fi_12_industry_connections_needed": item(p.industry_connections_needed if p.industry_connections_needed else None, "Industry & PSU pilot links needed", sec="Slide 16"),
            "fi_13_legal_ip_support_needed": item(p.legal_ip_support_needed if p.legal_ip_support_needed else None, "Patent drafting & legal support", sec="Slide 16"),
            "fi_14_market_access_pilot_support_needed": item(p.market_access_pilot_support_needed if p.market_access_pilot_support_needed else None, "Market trial & testbed support", sec="Slide 16"),
            "fi_15_training_skill_building_needed": item(p.training_skill_building_needed if p.training_skill_building_needed else None, "Workshops & founder coaching", sec="Slide 16"),
            "fi_16_six_quarter_product_roadmap": item(p.six_quarter_product_roadmap, "Product development roadmap Q1-Q6", sec="Slide 17"),
            "fi_17_six_quarter_market_roadmap": item(p.six_quarter_market_roadmap, "Market expansion roadmap Q1-Q6", sec="Slide 17"),
            "fi_18_six_quarter_team_roadmap": item(p.six_quarter_team_roadmap, "Hiring roadmap Q1-Q6", sec="Slide 17"),
            "fi_19_six_quarter_funding_roadmap": item(p.six_quarter_funding_roadmap, "Capital deployment roadmap Q1-Q6", sec="Slide 17"),
            "fi_20_contact_info": item(p.contact_info, "Contact details", sec="Slide 18"),
            "fi_21_applicant_declaration": item(p.applicant_declaration, "Signed applicant declaration", sec="Slide 18"),

            # --- Backward Compatibility Legacy Keys ---
            "founder_names": item(founder_names_str or "Not specified", "Founder names (legacy)", sec="Slide 8"),
            "leadership_experience": item(p.team or "Not specified", "Leadership experience (legacy)", sec="Slide 8"),
            "domain_expertise": item(p.team or "Not specified", "Domain expertise (legacy)", sec="Slide 8"),
            "commitment_level": item("Full-Time", "Commitment level (legacy)", sec="Slide 8"),
            "description": item(p.solution or "Not specified", "Solution description (legacy)", sec="Slide 4"),
            "problem_solved": item(p.problem_statement or "Not specified", "Problem statement (legacy)", sec="Slide 3"),
            "solution_value_prop": item(p.unique_value_proposition or p.solution or "Not specified", "Solution value proposition (legacy)", sec="Slide 4"),
            "customers": item(p.traction or p.who_is_affected or "Not specified", "Customers / traction (legacy)", sec="Slide 4"),
            "business_model": item(p.business_model or "Not specified", "Business model (legacy)", sec="Slide 11"),
            "target_market": item(p.market or p.who_is_affected or "Not specified", "Target market (legacy)", sec="Slide 6"),
            "market_size": item(p.market_size or p.market or "Not specified", "Market size (legacy)", sec="Slide 6"),
            "competitors": item(comp_names_str or "Not specified", "Competitors (legacy)", sec="Slide 7"),
            "competition_analysis": item(p.sustainable_competitive_advantage or p.competition or "Not specified", "Competition analysis (legacy)", sec="Slide 7"),
            "revenue_model": item(p.revenue_model or p.business_model or "Not specified", "Revenue model (legacy)", sec="Slide 11"),
            "funding_received": item(funding_float, "Total funding received (legacy)", sec="Slide 15"),
            "current_revenue": item(rev_float, "Current revenue (legacy)", sec="Slide 12"),
            "financial_metrics": item(p.financial_information or (f"Monthly burn: {p.burn_rate}" if p.burn_rate else "Not specified"), "Financial metrics (legacy)", sec="Slide 15"),
            "trl_level": item(p.current_trl or 4, "TRL level (legacy)", sec="Slide 5"),
            "ip_status": item(patents_summary, "IP status (legacy)", sec="Slide 13"),
            "patents": item(patents_summary, "Patents (legacy)", sec="Slide 13"),
            "ownership_declarations": item("Founder owns intellectual property.", "IP ownership declaration", sec="Slide 13"),
            "licensing_agreements": item("Standard proprietary licensing applies.", "Licensing agreements", sec="Slide 13"),
            "differentiation_claims": item(p.sustainable_competitive_advantage or p.competition or "Competitive differentiation", sec="Slide 7"),
            "moat_claims": item(p.unique_value_proposition or p.proprietary_technology_moat or "Defensible moat", sec="Slide 4"),
            "technical_risk_claims": item("Technical feasibility and prototype scale-up risk", sec="Slide 5"),
            "market_risk_claims": item("Market adoption and competitive displacement risk", sec="Slide 6"),
            "financial_runway_risks": item("Burn rate and funding runway management risk", sec="Slide 15"),
            "execution_risk_claims": item("Core talent recruitment and milestone execution risk", sec="Slide 9"),
        }

    def _gather_extracted_fields(self, ext: DocumentExtraction) -> dict[str, ExtractedField]:
        """Flat maps fields from the DocumentExtraction model to registry keys."""
        def get_risk_or_default(idx: int) -> ExtractedString | None:
            if ext.risk and ext.risk.major_risks and idx < len(ext.risk.major_risks):
                return ext.risk.major_risks[idx]
            return None

        def has_val(field: Any) -> bool:
            return field is not None and getattr(field, "value", None) is not None

        return {
            "founder_names": ext.founder.founder_names if ext.founder else None,
            "leadership_experience": ext.founder.leadership_experience if ext.founder else None,
            "domain_expertise": ext.founder.domain_expertise if ext.founder else None,
            "commitment_level": ext.founder.commitment_level if ext.founder else None,
            "description": ext.product.description if ext.product else None,
            "problem_solved": ext.product.problem_solved if ext.product else None,
            "solution_value_prop": ext.product.solution_value_prop if ext.product else None,
            "customers": ext.product.customers if ext.product else None,
            "business_model": ext.product.business_model if ext.product else None,
            "target_market": ext.market.target_market if ext.market else None,
            "market_size": ext.market.market_size if ext.market else None,
            "competitors": ext.market.competitors if ext.market else None,
            "competition_analysis": ext.market.competition_analysis if ext.market else None,
            "revenue_model": ext.financial.revenue_model if ext.financial else None,
            "funding_received": ext.financial.funding_received if ext.financial else None,
            "current_revenue": ext.financial.current_revenue if ext.financial else None,
            "financial_metrics": ext.financial.financial_metrics if ext.financial else None,
            "trl_level": ext.technology.trl_level if ext.technology else None,
            "ip_status": ext.technology.ip_status if ext.technology else None,
            "patents": ext.technology.ip_status if ext.technology else None,
            "ownership_declarations": make_extracted_string(
                ext.technology.ip_status.value or "Founder owns intellectual property.",
                "Ownership declaration derived from IP status.",
                ext.technology.ip_status.supporting_evidence or "Technology owner declarations."
            ) if (ext.technology and has_val(ext.technology.ip_status)) else None,
            "licensing_agreements": make_extracted_string(
                "Standard proprietary licensing applies.",
                "Inferred licensing model.",
                "No licensing restrictions mentioned."
            ) if (ext.technology and has_val(ext.technology.ip_status)) else None,
            "differentiation_claims": ext.market.competition_analysis if ext.market else None,
            "moat_claims": ext.product.solution_value_prop if ext.product else None,
            "technical_risk_claims": get_risk_or_default(0),
            "market_risk_claims": get_risk_or_default(1),
            "financial_runway_risks": get_risk_or_default(2),
            "execution_risk_claims": get_risk_or_default(3),
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
