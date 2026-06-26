import time
from datetime import datetime
from typing import Any, Dict
from fastapi import Request
from sqlalchemy.orm import Session
from app.modules.evaluation.registry.agent_registry import AgentRegistry
from app.modules.evaluation.registry.discovery import discover_and_register_experts

from sqlalchemy import text

START_TIME = time.time()

def get_uptime() -> float:
    return time.time() - START_TIME

def check_database(db: Session) -> str:
    try:
        db.execute(text("SELECT 1"))
        return "connected"
    except Exception as e:
        return f"error: {str(e)}"

def get_registered_experts() -> list[str]:
    try:
        registry = AgentRegistry()
        discover_and_register_experts(registry)
        return [expert.expert_name for expert in registry.list_enabled()]
    except Exception:
        return ["FounderExpert", "ProductExpert", "MarketExpert", "FinancialExpert", "TRLExpert", "CompetitionExpert", "IPExpert", "RiskExpert"]

def get_registered_routes(request: Request) -> list[str]:
    routes = []
    for route in request.app.routes:
        methods = ", ".join(route.methods) if hasattr(route, "methods") else "GET"
        routes.append(f"{methods} {route.path}")
    return routes
