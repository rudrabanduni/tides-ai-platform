from functools import lru_cache
from typing import Annotated

from pydantic import AnyHttpUrl, BeforeValidator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _split_cors_origins(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        return value
    if not value:
        return []
    return [origin.strip() for origin in value.split(",") if origin.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "TIDES AI Startup Evaluation Platform"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    dev_mode: bool = Field(default=False, validation_alias="DEV_MODE")

    database_url: str = Field(
        default="postgresql+psycopg://tides:tides@postgres:5432/tides_ai",
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
    litellm_model: str = Field(default="claude-3-5-sonnet-20241022", validation_alias="LITELLM_MODEL")
    ai_request_timeout_seconds: int = Field(default=120, validation_alias="AI_REQUEST_TIMEOUT_SECONDS")
    ai_max_retries: int = Field(default=2, validation_alias="AI_MAX_RETRIES")
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")


@lru_cache
def get_settings() -> Settings:
    return Settings()
