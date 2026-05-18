from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_db_url: str

    # AI providers
    anthropic_api_key: str
    openai_api_key: str
    assemblyai_api_key: str

    # Runtime
    env: str = "development"
    log_level: str = "INFO"
    port: int = 8000


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance; safe to call from any context."""
    # pydantic-settings populates fields from env vars at instantiation,
    # but mypy doesn't model that — fields are 'missing' from its POV.
    return Settings()  # type: ignore[call-arg]
