from app.api.routers.system import router as system_router
from app.api.routers.startups import router as startups_router
from app.api.routers.documents import router as documents_router
from app.api.routers.evaluation import router as evaluation_router
from app.api.routers.graph import router as graph_router
from app.api.routers.reports import router as reports_router
from app.api.routers.portfolio import router as portfolio_router
from app.api.routers.committee import router as committee_router

__all__ = [
    "system_router",
    "startups_router",
    "documents_router",
    "evaluation_router",
    "graph_router",
    "reports_router",
    "portfolio_router",
    "committee_router",
]
