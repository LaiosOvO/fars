from functools import lru_cache
import os

from fars_kg import __version__
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FARS Paper Knowledge Layer"
    app_version: str = __version__
    environment: str = "development"
    api_prefix: str = "/api"
    database_url: str = "sqlite+pysqlite:///./fars_kg.db"
    database_bootstrap_mode: str = "create_all"
    alembic_config_path: str = "alembic.ini"
    artifacts_root: str = ".artifacts"
    enable_request_logging: bool = True
    request_id_header: str = "X-Request-ID"
    log_level: str = "INFO"
    operator_token: str | None = None

    openalex_base_url: str = "https://api.openalex.org"
    openalex_api_key: str | None = None
    openalex_mailto: str | None = None
    openalex_timeout_seconds: float = 20.0

    parser_provider: str = "noop"
    grobid_base_url: str = "http://localhost:8070"
    grobid_timeout_seconds: float = 60.0
    repo_root: str = "."
    worktree_root: str = ".worktrees"
    llm_provider: str = "codex"
    llm_default_profile: str = "frontier"
    llm_frontier_model: str = Field(default_factory=lambda: os.getenv("OMX_DEFAULT_FRONTIER_MODEL", "gpt-5.4"))
    llm_standard_model: str = Field(
        default_factory=lambda: os.getenv("OMX_DEFAULT_STANDARD_MODEL", os.getenv("OMX_DEFAULT_FRONTIER_MODEL", "gpt-5.4-mini"))
    )
    llm_spark_model: str = Field(default_factory=lambda: os.getenv("OMX_DEFAULT_SPARK_MODEL", "gpt-5.3-codex-spark"))
    llm_default_reasoning_effort: str = "high"

    model_config = SettingsConfigDict(
        env_prefix="FARS_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
