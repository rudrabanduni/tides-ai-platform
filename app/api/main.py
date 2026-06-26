from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import get_settings
from app.api.middleware import RequestIDMiddleware, TimingMiddleware, LoggingMiddleware
from app.api.exceptions import setup_exception_handlers
from app.api.routers import (
    system_router, startups_router, documents_router, evaluation_router,
    graph_router, reports_router, portfolio_router, committee_router
)

def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title="TIDES Intelligence Engine API",
        version="1.0.0",
        description="Production-grade REST API exposing all evaluation, ranking, report, and committee decision layers of the TIDES Intelligence Engine.",
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # 1. Custom Middlewares (order: Logging -> RequestID -> Timing)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(TimingMiddleware)

    # 1b. Security Middlewares (onion wrapper: outermost is executed first)
    from app.security.middleware import (
        RequestIdentityMiddleware,
        SecurityHeadersMiddleware,
        AuthContextMiddleware,
        RateLimitMiddleware,
        AuditMiddleware,
    )
    app.add_middleware(AuditMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(AuthContextMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdentityMiddleware)

    # 2. Standard Middlewares
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

    # 3. Setup Exception Handlers
    setup_exception_handlers(app)


    # 4. Include Routers (Mount both at Root / and Prefix /api/v1 for 100% path compatibility)
    app.include_router(system_router)
    app.include_router(startups_router)
    app.include_router(documents_router)
    app.include_router(evaluation_router)
    app.include_router(graph_router)
    app.include_router(reports_router)
    app.include_router(portfolio_router)
    app.include_router(committee_router)
    
    from app.modules.apikeys.routes import router as apikeys_router_root
    app.include_router(apikeys_router_root)

    from app.api.router import api_router
    app.include_router(api_router, prefix="/api/v1")


    return app

app = create_app()
