from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FARS Paper Knowledge Layer"
    api_prefix: str = "/api"
    database_url: str = "sqlite+pysqlite:///./fars_kg.db"

    openalex_base_url: str = "https://api.openalex.org"
    openalex_api_key: str | None = None
    openalex_mailto: str | None = None
    openalex_timeout_seconds: float = 20.0

    parser_provider: str = "noop"
    grobid_base_url: str = "http://localhost:8070"
    grobid_timeout_seconds: float = 60.0

    model_config = SettingsConfigDict(
        env_prefix="FARS_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
