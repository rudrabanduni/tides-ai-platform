from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class AISettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ai_default_provider: str = Field(default="mock", validation_alias="AI_DEFAULT_PROVIDER")
    ai_fallback_provider: str = Field(default="mock", validation_alias="AI_FALLBACK_PROVIDER")
    ai_temperature: float = Field(default=0.0, validation_alias="AI_TEMPERATURE")
    ai_max_tokens: int = Field(default=4096, validation_alias="AI_MAX_TOKENS")
    ai_request_timeout_seconds: int = Field(default=30, validation_alias="AI_REQUEST_TIMEOUT_SECONDS")
    ai_max_retries: int = Field(default=3, validation_alias="AI_MAX_RETRIES")
    
    # Model names mapping
    ai_openai_model: str = Field(default="gpt-4o", validation_alias="AI_OPENAI_MODEL")
    ai_anthropic_model: str = Field(default="claude-3-5-sonnet-20241022", validation_alias="AI_ANTHROPIC_MODEL")
    ai_gemini_model: str = Field(default="gemini-1.5-pro", validation_alias="AI_GEMINI_MODEL")
    ai_local_model: str = Field(default="local-model", validation_alias="AI_LOCAL_MODEL")
    ai_ollama_model: str = Field(default="llama3", validation_alias="AI_OLLAMA_MODEL")
    ai_lmstudio_model: str = Field(default="lmstudio-model", validation_alias="AI_LMSTUDIO_MODEL")

    # API keys & Endpoints
    openai_api_key: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    gemini_api_key: Optional[str] = Field(default=None, validation_alias="GEMINI_API_KEY")
    local_api_endpoint: str = Field(default="http://localhost:8000/v1", validation_alias="LOCAL_API_ENDPOINT")
    ollama_api_endpoint: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_API_ENDPOINT")
    lmstudio_api_endpoint: str = Field(default="http://localhost:1234/v1", validation_alias="LMSTUDIO_API_ENDPOINT")

_ai_settings: Optional[AISettings] = None

def get_ai_settings() -> AISettings:
    global _ai_settings
    if _ai_settings is None:
        _ai_settings = AISettings()
    return _ai_settings
