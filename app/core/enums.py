from enum import Enum


class RoleName(str, Enum):
    ADMIN = "admin"
    EVALUATOR = "evaluator"
    COMMITTEE_MEMBER = "committee_member"
    VIEWER = "viewer"


class StartupStatus(str, Enum):
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "Under Review"
    AI_EVALUATED = "AI Evaluated"
    COMMITTEE_REVIEW = "Committee Review"
    RECOMMENDED = "Recommended"
    CONDITIONALLY_RECOMMENDED = "Conditionally Recommended"
    NOT_RECOMMENDED = "Not Recommended"
    INCUBATED = "Incubated"
    GRADUATED = "Graduated"
    ARCHIVED = "Archived"


class DocumentProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    PARSED = "parsed"
    FAILED = "failed"


class DocumentType(str, Enum):
    APPLICATION_FORM = "application_form"
    PITCH_DECK = "pitch_deck"
    FOUNDER_RESUME = "founder_resume"
    COMPANY_DOCUMENT = "company_document"
    OTHER = "other"


class SourceType(str, Enum):
    PDF = "pdf"
    FORM = "form"
    WEBSITE = "website"
    LINKEDIN = "linkedin"
    MANUAL_ENTRY = "manual_entry"


class EvaluationStatus(str, Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    READY_FOR_REVIEW = "ready_for_review"
    FINALIZED = "finalized"
    CANCELLED = "cancelled"


class RecommendationValue(str, Enum):
    RECOMMENDED = "Recommended"
    COMMITTEE_REVIEW = "Committee Review"
    CONDITIONALLY_RECOMMENDED = "Conditionally Recommended"
    NOT_RECOMMENDED = "Not Recommended"
