from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.enums import StartupStatus
from app.core.exceptions import NotFoundError
from app.db.mixins import utcnow
from app.modules.audit.service import AuditService
from app.modules.startups.models import StartupApplication, StartupStatusHistory
from app.modules.startups.repository import StartupRepository, StartupStatusHistoryRepository
from app.modules.startups.schemas import StartupCreate, StartupUpdate

from app.modules.reviews.models import ReviewerComment, CommitteeNote, ScoreOverride
from app.modules.evaluations.models import Evaluation, EvaluationScore, EvaluationEvidence
from app.modules.startup_profiles.models import StartupProfile, StartupProfileVersion, AIAssessmentRecord
from app.modules.founders.models import Founder
from app.modules.company_profiles.models import CompanyProfile
from app.modules.documents.models import Document, DocumentSource


class StartupService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.startups = StartupRepository(db)
        self.history = StartupStatusHistoryRepository(db)
        self.audit = AuditService(db)

    def create(self, payload: StartupCreate, *, actor_id: UUID | None) -> StartupApplication:
        startup = StartupApplication(**payload.model_dump(), created_by=actor_id)
        self.startups.add(startup)
        self.history.add(
            StartupStatusHistory(
                startup_id=startup.id,
                old_status=None,
                new_status=StartupStatus.DRAFT,
                changed_by=actor_id,
                reason="Startup application created",
            )
        )
        self.audit.log(
            actor_id=actor_id,
            entity_type="startup",
            entity_id=startup.id,
            action="startup_created",
            details={"startup_name": startup.startup_name},
        )
        self.db.commit()
        self.db.refresh(startup)
        return startup

    def get(self, startup_id: UUID) -> StartupApplication:
        startup = self.startups.get(startup_id)
        if not startup:
            raise NotFoundError("Startup not found")
        return startup

    def list(self, *, skip: int = 0, limit: int = 100) -> Sequence[StartupApplication]:
        # Check if empty, and trigger demo seed dynamically!
        existing = self.startups.list(skip=0, limit=1)
        if not existing:
            self.seed_demo_mode()
        return self.startups.list(skip=skip, limit=limit)

    def seed_demo_mode(self) -> None:
        import uuid
        import os
        import json

        demo_startups = [
            {
                "id": uuid.UUID("550e8400-e29b-41d4-a716-446655440001"),
                "startup_name": "AeroFusion Technologies",
                "sector": "CleanTech",
                "stage": "Seed",
                "problem_statement": "Traditional aerospace propulsion systems rely heavily on fossil fuels, contributing significantly to global carbon emissions.",
                "solution_summary": "We design high-efficiency, zero-emission hydrogen-plasma propulsion engines for commercial aviation.",
                "business_model": "B2B sales to aircraft manufacturing giants and technology licensing.",
                "target_market": "Commercial aviation sectors, cargo transports, and military drone applications.",
                "traction_summary": "Successful bench prototyping at TRL 4 with active LOIs signed by three tier-1 airline operators.",
                "funding_status": "Bootstrapped with $250k initial research grants."
            },
            {
                "id": uuid.UUID("550e8400-e29b-41d4-a716-446655440002"),
                "startup_name": "BioGenix Diagnostics",
                "sector": "HealthTech",
                "stage": "Pre-Seed",
                "problem_statement": "Early-stage oncology diagnostic tests are invasive, expensive, and have low reliability metrics.",
                "solution_summary": "A microfluidic liquid biopsy platform utilizing machine learning to identify circulating tumor cells with 98% accuracy.",
                "business_model": "Direct-to-clinic diagnostics services and SaaS-based diagnostic reports.",
                "target_market": "Clinical diagnostic laboratories and regional oncology research centers.",
                "traction_summary": "Pre-clinical validation under way with 500 patient sample datasets.",
                "funding_status": "Awaiting Pre-Seed round validation."
            },
            {
                "id": uuid.UUID("550e8400-e29b-41d4-a716-446655440003"),
                "startup_name": "QuantumSync Crypto",
                "sector": "Cybersecurity",
                "stage": "Growth",
                "problem_statement": "Modern encryption algorithms are highly vulnerable to upcoming quantum computing attacks.",
                "solution_summary": "Post-quantum lattice-based secure key exchange protocols for corporate data backbones.",
                "business_model": "Annual recurring enterprise software license subscriptions.",
                "target_market": "Defense departments, global financial institutions, and cloud providers.",
                "traction_summary": "Active pilot deployments with two major European banking associations.",
                "funding_status": "Raised $2M Seed funding."
            }
        ]

        for demo in demo_startups:
            exists = self.db.query(StartupApplication).filter(StartupApplication.id == demo["id"]).first()
            if not exists:
                startup = StartupApplication(
                    id=demo["id"],
                    startup_name=demo["startup_name"],
                    sector=demo["sector"],
                    stage=demo["stage"],
                    problem_statement=demo["problem_statement"],
                    solution_summary=demo["solution_summary"],
                    business_model=demo["business_model"],
                    target_market=demo["target_market"],
                    traction_summary=demo["traction_summary"],
                    funding_status=demo["funding_status"]
                )
                self.db.add(startup)
                self.db.commit()
                
                # Write a high-quality evaluation graph JSON to uploads/graphs/{id}.json
                graphs_dir = os.path.join("uploads", "graphs")
                os.makedirs(graphs_dir, exist_ok=True)
                path = os.path.join(graphs_dir, f"{demo['id']}.json")
                
                demo_graph = {
                    "graph_id": f"graph-{demo['id']}",
                    "graph_version": "1.0.0",
                    "graph_hash": "dummy_hash_123",
                    "startup_name": demo["startup_name"],
                    "startup_id": str(demo["id"]),
                    "category": demo["sector"],
                    "executive_assessment": {
                        "summary": f"Outstanding investment opportunity in the {demo['sector']} sector. The company shows a solid value proposition, addressing a key customer paint point with clear differentiation.",
                        "confidence": 0.85,
                        "overall_score": 0.82 if demo["stage"] == "Seed" else (0.72 if demo["stage"] == "Pre-Seed" else 0.88),
                        "recommendation": "INCUBATE"
                    },
                    "investment_assessment": {
                        "recommendation": "INCUBATE",
                        "investment_score": 0.84 if demo["stage"] == "Seed" else (0.75 if demo["stage"] == "Pre-Seed" else 0.89),
                        "confidence": 0.88
                    },
                    "founder_assessment": {
                        "overall_score": 0.85,
                        "confidence": 0.90,
                        "summary": "Founding team consists of PhDs and experienced leaders in the target industry domain."
                    },
                    "product_assessment": {
                        "overall_score": 0.80,
                        "confidence": 0.85,
                        "summary": "Prototype validated under bench validation conditions showing strong technical differentiators."
                    },
                    "market_assessment": {
                        "overall_score": 0.75,
                        "confidence": 0.80,
                        "summary": "Large market opportunity with robust early customer validation and LOIs."
                    },
                    "report": {
                        "report_id": f"rep-{demo['id']}",
                        "graph_version": "1.0.0",
                        "executive_summary": {
                            "content": f"Due Diligence Report for {demo['startup_name']}.\n\nThe startup demonstrates a highly structured solution addressing a valid market gap. We recommend incubation under standard terms.",
                            "confidence": 0.88
                        },
                        "investment_summary": {
                            "content": "Investment Thesis: Strong technical barriers to entry and low immediate capital intensity make this a high-viability deal.",
                            "confidence": 0.85
                        },
                        "founder_analysis": {
                            "content": "Founders show domain relevance, PhD track records, and clear execution capacity.",
                            "confidence": 0.90
                        },
                        "product_analysis": {
                            "content": "Innovative microfluidic / propulsion hardware design coverable by provisional patent filings.",
                            "confidence": 0.82
                        },
                        "market_analysis": {
                            "content": "TAM exceeds $5B with clear competitive positioning and early traction signals.",
                            "confidence": 0.80
                        },
                        "financial_analysis": {
                            "content": "Solid pre-revenue model with 18 months runway on research grants.",
                            "confidence": 0.75
                        },
                        "risk_analysis": {
                            "content": "Key risks include regulatory timelines and hardware manufacturing setup dependencies.",
                            "confidence": 0.85
                        },
                        "follow_up_questions": {
                            "content": "1. What is the timeline for scale-up manufacturing?\n2. Are there dependencies on foreign-sourced supply chains?",
                            "confidence": 0.90
                        }
                    },
                    "claims": {
                        "c1": {
                            "claim_id": "c1",
                            "statement": demo["problem_statement"]
                        },
                        "c2": {
                            "claim_id": "c2",
                            "statement": demo["solution_summary"]
                        }
                    },
                    "observations": {
                        "o1": {
                            "node_id": "o1",
                            "claim_id": "c1",
                            "content": "Validated industry problem statement backed by initial interview statements.",
                            "score": 0.90,
                            "source": "Intake Form"
                        },
                        "o2": {
                            "node_id": "o2",
                            "claim_id": "c2",
                            "content": "Advanced plasma/microfluidic prototyping covers core tech differentiators.",
                            "score": 0.85,
                            "source": "Pitch Deck"
                        }
                    },
                    "risks": {
                        "r1": {
                            "node_id": "r1",
                            "observation_id": "o1",
                            "content": "Capital expenditures might escalate during pilot transitions.",
                            "severity": "MEDIUM",
                            "category": "Financial"
                        }
                    },
                    "questions": {
                        "q1": {
                            "node_id": "q1",
                            "observation_id": "o2",
                            "content": "What supply-chain bottlenecks are expected for critical assembly components?",
                            "priority": "HIGH",
                            "domain": "Technology"
                        }
                    }
                }
                
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(demo_graph, f, indent=2)

    def update(self, startup_id: UUID, payload: StartupUpdate, *, actor_id: UUID | None) -> StartupApplication:
        startup = self.get(startup_id)
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(startup, field, value)
        self.audit.log(
            actor_id=actor_id,
            entity_type="startup",
            entity_id=startup.id,
            action="startup_updated",
            details=data,
        )
        self.db.commit()
        self.db.refresh(startup)
        return startup

    def change_status(
        self,
        startup_id: UUID,
        *,
        new_status: StartupStatus,
        reason: str,
        actor_id: UUID | None,
    ) -> StartupApplication:
        startup = self.get(startup_id)
        old_status = startup.current_status
        startup.current_status = new_status
        if new_status == StartupStatus.SUBMITTED and startup.submitted_at is None:
            startup.submitted_at = utcnow()
        self.history.add(
            StartupStatusHistory(
                startup_id=startup.id,
                old_status=old_status,
                new_status=new_status,
                changed_by=actor_id,
                reason=reason,
            )
        )
        self.audit.log(
            actor_id=actor_id,
            entity_type="startup",
            entity_id=startup.id,
            action="startup_status_changed",
            reason=reason,
            details={"old_status": old_status.value, "new_status": new_status.value},
        )
        self.db.commit()
        self.db.refresh(startup)
        return startup

    def submit(self, startup_id: UUID, *, actor_id: UUID | None) -> StartupApplication:
        return self.change_status(
            startup_id,
            new_status=StartupStatus.SUBMITTED,
            reason="Startup submitted for evaluation",
            actor_id=actor_id,
        )

    def status_history(self, startup_id: UUID) -> Sequence[StartupStatusHistory]:
        self.get(startup_id)
        return self.history.list_for_startup(startup_id)

    def delete(self, startup_id: UUID, *, actor_id: UUID | None) -> None:
        startup = self.get(startup_id)

        # 1. Fetch evaluations to get evaluation IDs
        evaluations = self.db.query(Evaluation).filter(Evaluation.startup_id == startup_id).all()
        eval_ids = [e.id for e in evaluations]

        # 2. Fetch evaluation scores to get score IDs
        eval_score_ids = []
        if eval_ids:
            eval_scores = self.db.query(EvaluationScore).filter(EvaluationScore.evaluation_id.in_(eval_ids)).all()
            eval_score_ids = [es.id for es in eval_scores]

        # 3. Fetch startup profiles to get profile IDs
        profiles = self.db.query(StartupProfile).filter(StartupProfile.startup_id == startup_id).all()
        profile_ids = [p.id for p in profiles]

        # 4. Perform sequential deletions in correct dependency order
        # Score overrides & evidence
        if eval_score_ids:
            self.db.query(ScoreOverride).filter(ScoreOverride.evaluation_score_id.in_(eval_score_ids)).delete(synchronize_session=False)
            self.db.query(EvaluationEvidence).filter(EvaluationEvidence.evaluation_score_id.in_(eval_score_ids)).delete(synchronize_session=False)

        # Evaluation scores
        if eval_ids:
            self.db.query(EvaluationScore).filter(EvaluationScore.evaluation_id.in_(eval_ids)).delete(synchronize_session=False)

        # Evaluations
        self.db.query(Evaluation).filter(Evaluation.startup_id == startup_id).delete(synchronize_session=False)

        # Reviewer comments & committee notes
        self.db.query(ReviewerComment).filter(ReviewerComment.startup_id == startup_id).delete(synchronize_session=False)
        self.db.query(CommitteeNote).filter(CommitteeNote.startup_id == startup_id).delete(synchronize_session=False)

        # Startup status history
        self.db.query(StartupStatusHistory).filter(StartupStatusHistory.startup_id == startup_id).delete(synchronize_session=False)

        # Startup profile versions
        if profile_ids:
            self.db.query(StartupProfileVersion).filter(StartupProfileVersion.startup_profile_id.in_(profile_ids)).delete(synchronize_session=False)

        # Startup profiles
        self.db.query(StartupProfile).filter(StartupProfile.startup_id == startup_id).delete(synchronize_session=False)

        # Founders
        self.db.query(Founder).filter(Founder.startup_id == startup_id).delete(synchronize_session=False)

        # Company profiles
        self.db.query(CompanyProfile).filter(CompanyProfile.startup_id == startup_id).delete(synchronize_session=False)

        # Document sources
        self.db.query(DocumentSource).filter(DocumentSource.startup_id == startup_id).delete(synchronize_session=False)

        # Documents
        self.db.query(Document).filter(Document.startup_id == startup_id).delete(synchronize_session=False)

        # AI assessment records
        self.db.query(AIAssessmentRecord).filter(AIAssessmentRecord.startup_id == startup_id).delete(synchronize_session=False)

        # Audit log entry for deletion
        self.audit.log(
            actor_id=actor_id,
            entity_type="startup",
            entity_id=startup_id,
            action="startup_deleted",
            details={"startup_name": startup.startup_name},
        )

        # Finally delete startup application itself
        self.db.query(StartupApplication).filter(StartupApplication.id == startup_id).delete(synchronize_session=False)
        self.db.commit()
