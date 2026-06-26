from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import ReadOnlyUser
from app.modules.intelligence.service import IntelligenceService
from app.modules.intelligence.schemas import (
    StartupIntelligenceProfileRead,
    StartupClaimRead,
    StartupEvidenceRead,
    FieldConflictRead,
    StartupIntelligenceProfileVersionRead
)

router = APIRouter(prefix="/intelligence/{startup_id}", tags=["Intelligence Engine"])


@router.get("", response_model=StartupIntelligenceProfileRead, status_code=status.HTTP_200_OK)
def get_startup_intelligence_profile(
    startup_id: UUID,
    current_user: ReadOnlyUser,
    db: Session = Depends(get_db)
):
    """Fetch the full, unified Startup Intelligence Profile (Digital Twin)."""
    service = IntelligenceService(db)
    profile = service.get_profile(startup_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup intelligence profile not found"
        )
    return profile


@router.get("/claims", response_model=list[StartupClaimRead], status_code=status.HTTP_200_OK)
def get_startup_claims(
    startup_id: UUID,
    current_user: ReadOnlyUser,
    db: Session = Depends(get_db)
):
    """Retrieve all claims (preferred, conflicting, and historical)."""
    service = IntelligenceService(db)
    profile = service.get_profile(startup_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup intelligence profile not found"
        )
    return service.claims.list_for_profile(profile.id)


@router.get("/claims/{claim_id}", response_model=StartupClaimRead, status_code=status.HTTP_200_OK)
def get_startup_claim(
    startup_id: UUID,
    claim_id: UUID,
    current_user: ReadOnlyUser,
    db: Session = Depends(get_db)
):
    """Fetch a specific Claim by ID."""
    service = IntelligenceService(db)
    claim = service.claims.get(claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found"
        )
    profile = service.profiles.get(claim.profile_id)
    if not profile or profile.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Claim does not belong to this startup"
        )
    return claim


@router.get("/evidence", response_model=list[StartupEvidenceRead], status_code=status.HTTP_200_OK)
def get_startup_evidence(
    startup_id: UUID,
    current_user: ReadOnlyUser,
    db: Session = Depends(get_db)
):
    """Fetch supporting evidence logs and document section coordinates."""
    service = IntelligenceService(db)
    profile = service.get_profile(startup_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup intelligence profile not found"
        )
    claims = service.claims.list_for_profile(profile.id)
    evidence_list = []
    for claim in claims:
        evidence_list.extend(service.evidence.list_for_claim(claim.id))
    return evidence_list


@router.get("/conflicts", response_model=list[FieldConflictRead], status_code=status.HTTP_200_OK)
def get_startup_conflicts(
    startup_id: UUID,
    current_user: ReadOnlyUser,
    db: Session = Depends(get_db)
):
    """List unresolved data conflicts across uploaded document sources."""
    service = IntelligenceService(db)
    profile = service.get_profile(startup_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup intelligence profile not found"
        )
    return service.conflicts.list_unresolved_for_profile(profile.id)


@router.get("/versions", response_model=list[StartupIntelligenceProfileVersionRead], status_code=status.HTTP_200_OK)
def get_startup_profile_versions(
    startup_id: UUID,
    current_user: ReadOnlyUser,
    db: Session = Depends(get_db)
):
    """Retrieve history of immutable profile version snapshots."""
    service = IntelligenceService(db)
    profile = service.get_profile(startup_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Startup intelligence profile not found"
        )
    return service.profile_versions.list_versions(profile.id)
