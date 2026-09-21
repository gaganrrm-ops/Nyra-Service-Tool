"""Runtime configuration. Secrets come from the environment only (never committed, never logged)."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(REPO_ROOT / ".env"), extra="ignore", case_sensitive=False)

    app_env: str = "dev"
    log_level: str = "INFO"

    # database
    database_url: str = "postgresql://nyra:nyra@localhost:5433/nyra"

    # auth
    auth_mode: str = "dev"  # dev | supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_jwt_secret: str = ""
    default_tenant_slug: str = "nyra-demo"

    # ai (day 12)
    ai_enabled: bool = False
    ai_autonomy_tier: int = 2
    llm_provider: str = ""
    llm_model: str = ""
    llm_api_key: str = ""

    # email (day 8-9)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_from: str = "helpdesk@example.com"
    imap_host: str = ""
    imap_mailbox: str = "INBOX"

    @property
    def migrations_dir(self) -> Path:
        return REPO_ROOT / "db" / "migrations"

    @property
    def seeds_dir(self) -> Path:
        return REPO_ROOT / "db" / "seeds"


@lru_cache
def settings() -> Settings:
    return Settings()
