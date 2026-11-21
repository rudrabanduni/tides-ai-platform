from functools import lru_cache
import os
from pathlib import Path
from typing import Annotated

from pydantic import AnyHttpUrl, BeforeValidator, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_SNAPSHOT_DB_NAME = "tides_ai.db"
PROTECTED_SNAPSHOT_DB_PATH = (PROJECT_ROOT / PROTECTED_SNAPSHOT_DB_NAME).resolve()


def resolve_sqlite_db_path(database_url: str, base_dir: Path | None = None) -> Path | None:
    """Resolve the filesystem Path targeted by a sqlite:/// SQLAlchemy URL, or None for non-SQLite/memory URLs."""
    raw = (database_url or "").strip()
    lowered = raw.lower()
    if not lowered.startswith("sqlite:"):
        return None
    if ":memory:" in lowered:
        return None
    for prefix in ("sqlite+pysqlite:///", "sqlite+aiosqlite:///", "sqlite:///"):
        if lowered.startswith(prefix):
            path_part = raw[len(prefix):].split("?", 1)[0]
            if not path_part:
                return None
            p = Path(path_part)
            if not p.is_absolute():
                p = (base_dir or PROJECT_ROOT) / p
            return p.resolve()
    return None


def validate_database_configuration(settings: "Settings") -> "Settings":
    """Enforce fail-closed database isolation rules across local dev and production."""
    db_url = (settings.database_url or "").strip()
    db_url_lower = db_url.lower()
    resolved_sqlite = resolve_sqlite_db_path(db_url)
    target_is_protected_snapshot = (
        resolved_sqlite is not None
        and (
            resolved_sqlite == PROTECTED_SNAPSHOT_DB_PATH
            or resolved_sqlite.name.lower() == PROTECTED_SNAPSHOT_DB_NAME
        )
    ) or (
        db_url_lower.startswith("sqlite:")
        and db_url_lower.split("?", 1)[0].rstrip("/\\").endswith(PROTECTED_SNAPSHOT_DB_NAME)
    )

    if target_is_protected_snapshot:
        raise RuntimeError(
            "FATAL: DATABASE_URL targets protected historical snapshot 'tides_ai.db'. "
            "Runtime startup refuses to connect to 'tides_ai.db'; use 'sqlite:///./tides_dev.db' "
            "for local development or an explicit production database URL."
        )

    app_env_norm = (settings.app_env or "").strip().lower()
    if app_env_norm == "production":
        explicit_in_env = bool(os.environ.get("DATABASE_URL", "").strip())
        explicit_in_model = "database_url" in settings.model_fields_set
        if not (explicit_in_env or explicit_in_model):
            raise RuntimeError(
                "FATAL: APP_ENV=production requires an explicitly configured DATABASE_URL."
            )
        if db_url_lower.startswith("sqlite:") or "tides_dev.db" in db_url_lower:
            raise RuntimeError(
                "FATAL: APP_ENV=production refuses development/workspace SQLite defaults "
                f"('{db_url}'). Configure an explicit production non-SQLite DATABASE_URL."
            )

    return settings


_INSECURE_JWT_SECRETS = {"change-me-in-production", "replace-with-a-long-random-secret", "secret", "changeme"}


def validate_production_secrets(settings: "Settings") -> "Settings":
    """Fail closed when production would sign tokens with a default or weak JWT secret."""
    if (settings.app_env or "").strip().lower() == "production":
        secret = (settings.jwt_secret_key or "").strip()
        if secret in _INSECURE_JWT_SECRETS or len(secret) < 32:
            raise RuntimeError(
                "FATAL: APP_ENV=production requires JWT_SECRET_KEY set to a random value of at least 32 characters."
            )
    return settings


def _split_cors_origins(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        return value
    if not value:
        return []
    return [origin.strip() for origin in value.split(",") if origin.strip()]


def _normalize_claude_model(value: str | None) -> str:
    if not value:
        return "claude-sonnet-5-5"
    val = str(value).strip()
    # Transparently migrate retired Claude 3.5 model IDs to active Claude 5.5 models
    if val in ("claude-3-5-sonnet-20241022", "claude-3-5-sonnet", "anthropic/claude-3-5-sonnet-20241022"):
        return "claude-sonnet-5-5"
    if val in ("claude-3-5-haiku-20241022", "claude-3-5-haiku", "anthropic/claude-3-5-haiku-20241022"):
        return "claude-haiku-5-5"
    return val


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", populate_by_name=True)

    app_name: str = "TIDES AI Startup Evaluation Platform"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    dev_mode: bool = Field(default=False, validation_alias="DEV_MODE")

    database_url: str = Field(
        default="sqlite:///./tides_dev.db",
        validation_alias="DATABASE_URL",
    )

    jwt_secret_key: str = Field(default="change-me-in-production", validation_alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    upload_dir: str = Field(default="uploads", validation_alias="UPLOAD_DIR")
    max_upload_size_mb: int = Field(default=25, validation_alias="MAX_UPLOAD_SIZE_MB")

    cors_origins: Annotated[list[str] | list[AnyHttpUrl], BeforeValidator(_split_cors_origins)] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"],
        validation_alias="CORS_ORIGINS",
    )

    ai_enabled: bool = Field(default=False, validation_alias="AI_ENABLED")
    ai_provider: str = Field(default="mock", validation_alias="AI_PROVIDER")
    litellm_model: Annotated[str, BeforeValidator(_normalize_claude_model)] = Field(
        default="claude-sonnet-5-5", validation_alias="LITELLM_MODEL"
    )
    ai_request_timeout_seconds: int = Field(default=120, validation_alias="AI_REQUEST_TIMEOUT_SECONDS")
    # Transport-level retries in the gateway (the ONLY automatic retry layer). Truncated or
    # malformed completions are never retried with an identical request.
    ai_max_retries: int = Field(default=1, ge=0, le=3, validation_alias="AI_MAX_RETRIES")
    # "off": disable adaptive thinking for structured JSON calls (thinking tokens count toward
    # max_tokens and caused the PETREVOLT 900-token domain truncation). "provider_default": omit.
    ai_structured_thinking_mode: str = Field(default="off", validation_alias="AI_STRUCTURED_THINKING_MODE")
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")

    # Evaluation Budget & Cost Observability (Production default ceiling: $0.35 USD; explicit override supported)
    ai_max_evaluation_budget_usd: float = Field(default=0.35, validation_alias="AI_MAX_EVALUATION_BUDGET_USD")
    ai_max_evaluation_budget: float = Field(default=0.35, validation_alias="AI_MAX_EVALUATION_BUDGET")
    ai_inr_exchange_rate: float = Field(default=96.0, validation_alias="AI_INR_EXCHANGE_RATE")
    ai_inr_buffer_multiplier: float = Field(default=1.18, validation_alias="AI_INR_BUFFER_MULTIPLIER")
    ai_target_cost_inr_min: float = Field(default=50.0, validation_alias="AI_TARGET_COST_INR_MIN")
    ai_target_cost_inr_max: float = Field(default=60.0, validation_alias="AI_TARGET_COST_INR_MAX")
    ai_absolute_cost_inr_ceiling: float = Field(default=70.0, validation_alias="AI_ABSOLUTE_COST_INR_CEILING")

    # Cost-Aware Model Routing (Active production Claude models)
    ai_fast_model: Annotated[str, BeforeValidator(_normalize_claude_model)] = Field(
        default="claude-haiku-5-5", validation_alias="AI_FAST_MODEL"
    )
    ai_reasoning_model: Annotated[str, BeforeValidator(_normalize_claude_model)] = Field(
        default="claude-sonnet-5-5", validation_alias="AI_REASONING_MODEL"
    )
    ai_pricing_catalog_version: str = Field(default="2026-10-v3", validation_alias="AI_PRICING_CATALOG_VERSION")
    ai_default_cache_write_ttl: str = Field(default="5m", validation_alias="AI_DEFAULT_CACHE_WRITE_TTL")
    ai_cache_pricing_policy: str = Field(default="conservative_1h", validation_alias="AI_CACHE_PRICING_POLICY")
    # Domain criterion batching (see docs/ARCHITECTURE.md "Domain batch sizing" for the cost model).
    # 3 criteria/batch -> 30 batches for the 81 domain criteria; per-batch output cap = 80 + 220*n.
    ai_domain_batch_max_criteria: int = Field(default=3, ge=1, le=10, validation_alias="AI_DOMAIN_BATCH_MAX_CRITERIA")
    ai_domain_batch_max_output_tokens: int = Field(default=900, ge=300, le=2400, validation_alias="AI_DOMAIN_BATCH_MAX_OUTPUT_TOKENS")
    # Retries of a parse/validation failure with the same request. Default 0: identical requests
    # fail identically and the PETREVOLT run paid twice for every truncated batch.
    ai_domain_batch_max_retries: int = Field(default=0, ge=0, le=3, validation_alias="AI_DOMAIN_BATCH_MAX_RETRIES")
    # One-time recovery when a multi-criterion batch is truncated: re-run each criterion alone.
    ai_domain_split_on_truncation: bool = Field(default=True, validation_alias="AI_DOMAIN_SPLIT_ON_TRUNCATION")

    # Evaluation-run execution from the web application
    evaluation_runner_mode: str = Field(default="thread", validation_alias="EVALUATION_RUNNER_MODE")
    # Paid live-provider evaluations can never be launched from the browser unless explicitly enabled.
    allow_ui_live_evaluations: bool = Field(default=False, validation_alias="ALLOW_UI_LIVE_EVALUATIONS")

    # External Research Integration (Configurable provider abstraction)
    research_provider: str = Field(default="disabled", validation_alias="RESEARCH_PROVIDER")
    research_api_key: str | None = Field(default=None, validation_alias="RESEARCH_API_KEY")
    research_cost_per_query_usd: float = Field(default=0.005, validation_alias="RESEARCH_COST_PER_QUERY_USD")
    research_max_queries_per_eval: int = Field(default=4, validation_alias="RESEARCH_MAX_QUERIES_PER_EVAL")

    # Tavily Provider Configuration
    tavily_api_key: str | None = Field(default=None, validation_alias="TAVILY_API_KEY")
    tavily_api_url: str = Field(default="https://api.tavily.com/search", validation_alias="TAVILY_API_URL")
    tavily_search_depth: str = Field(default="basic", validation_alias="TAVILY_SEARCH_DEPTH")
    tavily_cost_per_credit_usd: float = Field(default=0.008, validation_alias="TAVILY_COST_PER_CREDIT_USD")
    tavily_timeout_seconds: float = Field(default=15.0, validation_alias="TAVILY_TIMEOUT_SECONDS")

    @model_validator(mode="after")
    def _enforce_database_policy(self) -> "Settings":
        validate_database_configuration(self)
        validate_production_secrets(self)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
