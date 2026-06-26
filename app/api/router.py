from fastapi import APIRouter

from app.modules.audit.routes import router as audit_router
from app.modules.auth.routes import router as auth_router
from app.modules.company_profiles.routes import router as company_profiles_router
from app.modules.dashboard.routes import router as dashboard_router
from app.modules.documents.routes import router as documents_router
from app.modules.evaluations.routes import router as evaluations_router
from app.modules.founders.routes import router as founders_router
from app.modules.intake.routes import router as intake_router
from app.modules.recommendation_rules.routes import router as recommendation_rules_router
from app.modules.reviews.routes import router as reviews_router
from app.modules.startup_profiles.routes import router as startup_profiles_router
from app.modules.startups.routes import router as startups_router
from app.modules.users.routes import router as users_router
from app.modules.intelligence.routes import router as intelligence_router
from app.modules.apikeys.routes import router as apikeys_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(intake_router)
api_router.include_router(startup_profiles_router)
api_router.include_router(startups_router)
api_router.include_router(founders_router)
api_router.include_router(company_profiles_router)
api_router.include_router(documents_router)
api_router.include_router(evaluations_router)
api_router.include_router(recommendation_rules_router)
api_router.include_router(reviews_router)
api_router.include_router(audit_router)
api_router.include_router(dashboard_router)
api_router.include_router(intelligence_router)
api_router.include_router(apikeys_router)



