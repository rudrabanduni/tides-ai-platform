from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import DocumentProcessingStatus, StartupStatus
from app.modules.company_profiles.models import CompanyProfile
from app.modules.documents.models import Document
from app.modules.founders.models import Founder
from app.modules.startup_profiles.models import StartupProfile
from app.modules.startups.models import StartupApplication


class StartupContextSection(BaseModel):
    id: UUID
    startup_name: str
    sector: str | None = None
    stage: str | None = None
    current_status: str
    problem_statement: str | None = None
    solution_summary: str | None = None
    business_model: str | None = None
    target_market: str | None = None
    traction_summary: str | None = None
    funding_status: str | None = None
    submitted_at: datetime | None = None


class FounderContextSection(BaseModel):
    id: UUID
    name: str
    email: str | None = None
    phone: str | None = None
    education: str | None = None
    experience_summary: str | None = None
    linkedin_url: str | None = None
    role_in_startup: str | None = None


class CompanyProfileContextSection(BaseModel):
    id: UUID
    website: str | None = None
    incorporation_status: str | None = None
    registration_number: str | None = None
    location: str | None = None
    team_size: int | None = None
    revenue_status: str | None = None
    ip_status: str | None = None
    market_category: str | None = None


class DocumentContextSection(BaseModel):
    id: UUID
    document_type: str
    original_filename: str
    processing_status: str
    parsed_text: str | None = None
    content_type: str | None = None
    file_size: int


class CurrentProfileContextSection(BaseModel):
    id: UUID
    startup_id: UUID
    problem_statement: str | None = None
    solution_summary: str | None = None
    target_market: str | None = None
    business_model: str | None = None
    technology_summary: str | None = None
    traction_summary: str | None = None
    funding_summary: str | None = None
    ip_summary: str | None = None
    generated_at: datetime
    updated_at: datetime


class StartupProfileContext(BaseModel):
    """Structured startup context for downstream AI agents."""

    startup: StartupContextSection
    founders: list[FounderContextSection] = Field(default_factory=list)
    company_profile: CompanyProfileContextSection | None = None
    documents: list[DocumentContextSection] = Field(default_factory=list)
    current_profile: CurrentProfileContextSection | None = None

    model_config = ConfigDict(from_attributes=True)

    def to_prompt_dict(self) -> dict[str, object]:
        return self.model_dump(mode="json")


class StartupProfileContextBuilder:
    """Assembles a startup profile context object from platform records."""

    def build(
        self,
        *,
        startup: StartupApplication,
        founders: Sequence[Founder] | None = None,
        profile: StartupProfile | None = None,
        company_profile: CompanyProfile | None = None,
        documents: Sequence[Document] | None = None,
    ) -> StartupProfileContext:
        return StartupProfileContext(
            startup=self._build_startup(startup),
            founders=[self._build_founder(founder) for founder in founders or ()],
            company_profile=self._build_company_profile(company_profile),
            documents=[
                self._build_document(doc)
                for doc in documents or ()
                if (doc.processing_status.value if hasattr(doc.processing_status, "value") else doc.processing_status) == DocumentProcessingStatus.PARSED.value
            ],
            current_profile=self._build_current_profile(profile),
        )

    @staticmethod
    def _build_startup(startup: StartupApplication) -> StartupContextSection:
        current_status = startup.current_status
        if isinstance(current_status, StartupStatus):
            current_status = current_status.value
        return StartupContextSection(
            id=startup.id,
            startup_name=startup.startup_name,
            sector=startup.sector,
            stage=startup.stage,
            current_status=current_status,
            problem_statement=startup.problem_statement,
            solution_summary=startup.solution_summary,
            business_model=startup.business_model,
            target_market=startup.target_market,
            traction_summary=startup.traction_summary,
            funding_status=startup.funding_status,
            submitted_at=startup.submitted_at,
        )

    @staticmethod
    def _build_founder(founder: Founder) -> FounderContextSection:
        return FounderContextSection(
            id=founder.id,
            name=founder.name,
            email=founder.email,
            phone=founder.phone,
            education=founder.education,
            experience_summary=founder.experience_summary,
            linkedin_url=founder.linkedin_url,
            role_in_startup=founder.role_in_startup,
        )

    @staticmethod
    def _build_company_profile(company_profile: CompanyProfile | None) -> CompanyProfileContextSection | None:
        if company_profile is None:
            return None
        return CompanyProfileContextSection(
            id=company_profile.id,
            website=company_profile.website,
            incorporation_status=company_profile.incorporation_status,
            registration_number=company_profile.registration_number,
            location=company_profile.location,
            team_size=company_profile.team_size,
            revenue_status=company_profile.revenue_status,
            ip_status=company_profile.ip_status,
            market_category=company_profile.market_category,
        )

    @staticmethod
    def _build_document(document: Document) -> DocumentContextSection:
        document_type = document.document_type.value if hasattr(document.document_type, "value") else document.document_type
        processing_status = (
            document.processing_status.value
            if hasattr(document.processing_status, "value")
            else document.processing_status
        )
        parsed_text = document.parsed_text
        if parsed_text is not None and document.processing_status != DocumentProcessingStatus.PARSED:
            parsed_text = None
        return DocumentContextSection(
            id=document.id,
            document_type=document_type,
            original_filename=document.original_filename,
            processing_status=processing_status,
            parsed_text=parsed_text,
            content_type=document.content_type,
            file_size=document.file_size,
        )

    @staticmethod
    def _build_current_profile(profile: StartupProfile | None) -> CurrentProfileContextSection | None:
        if profile is None:
            return None
        return CurrentProfileContextSection(
            id=profile.id,
            startup_id=profile.startup_id,
            problem_statement=profile.problem_statement,
            solution_summary=profile.solution_summary,
            target_market=profile.target_market,
            business_model=profile.business_model,
            technology_summary=profile.technology_summary,
            traction_summary=profile.traction_summary,
            funding_summary=profile.funding_summary,
            ip_summary=profile.ip_summary,
            generated_at=profile.generated_at,
            updated_at=profile.updated_at,
        )
