"""Cost-aware model routing for AI completions.

Routes tasks to appropriate models based on task complexity:
- Cheaper fast model (e.g. Claude Haiku) for extraction, classification, field mapping, normalisation.
- Stronger reasoning model (e.g. Claude Sonnet) for complex domain reasoning, conflict resolution, final review.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import Settings, get_settings
from app.services.ai.schemas import AICompletionRequest

logger = logging.getLogger(__name__)

# Operations routed to the fast/cheaper model
FAST_TASK_OPERATIONS = {
    "extraction",
    "document_extraction",
    "profile_extraction",
    "classification",
    "field_mapping",
    "normalisation",
    "normalization",
    "parsing",
}

# Operations routed to the deeper reasoning model
REASONING_TASK_OPERATIONS = {
    "expert_evaluation",
    "domain_evaluation",
    "founder_evaluation",
    "product_evaluation",
    "market_evaluation",
    "financial_evaluation",
    "trl_evaluation",
    "competition_evaluation",
    "ip_evaluation",
    "risk_evaluation",
    "conflict_resolution",
    "supervisory_review",
    "final_review",
    "investment_decision",
    "due_diligence_report",
}


class ModelRouter:
    """Resolves the optimal model for a given AICompletionRequest based on task complexity and settings."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def resolve_model(self, request: AICompletionRequest, default_model: str | None = None) -> str:
        """Determines the model to use for the request.

        Precedence:
        1. Explicit model override in request (`request.model`).
        2. Task-based routing via `operation_type` or `agent_name`.
        3. Instance default model (`default_model`), if provided.
        4. Configured default `litellm_model`.
        """
        # 1. Explicit request override
        if request.model and request.model.strip():
            return request.model.strip()

        op = (request.operation_type or "").lower().strip()
        agent = (request.agent_name or "").lower().strip()

        # 2. Check if it's a fast/extraction task
        if op in FAST_TASK_OPERATIONS or any(fast_term in agent for fast_term in ("extractor", "extraction", "intake")):
            selected_model = self.settings.ai_fast_model
            logger.debug(f"[ROUTER] Routing '{request.agent_name}' ({op}) to fast model: {selected_model}")
            return selected_model

        # 3. Check if it's an expert reasoning or review task
        if op in REASONING_TASK_OPERATIONS or any(expert_term in agent for expert_term in ("expert", "review", "committee")):
            selected_model = self.settings.ai_reasoning_model
            logger.debug(f"[ROUTER] Routing '{request.agent_name}' ({op}) to reasoning model: {selected_model}")
            return selected_model

        # 4. Fallback to instance default model, then configured litellm_model
        return default_model or self.settings.litellm_model
