from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass(frozen=True)
class Settings:
    """Unified settings object for the current scaffold and future integrations."""

    app_name: str = "FARS Paper Knowledge Layer"
    app_env: str = "development"
    app_version: str = "0.1.0"
    debug: bool = False
    api_prefix: str = ""

    # Integration defaults kept available for next phases.
    openalex_base_url: str = "https://api.openalex.org"
    openalex_api_key: str | None = None
    grobid_base_url: str = "http://localhost:8070"
    service_name: str = "fars-paper-kg"
    default_topic_expansion_limit: int = 8


def _as_bool(raw: str | None, default: bool = False) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("FARS_APP_NAME", "FARS Paper Knowledge Layer"),
        app_env=os.getenv("FARS_APP_ENV", "development"),
        app_version=os.getenv("FARS_APP_VERSION", "0.1.0"),
        debug=_as_bool(os.getenv("FARS_DEBUG"), False),
        api_prefix=os.getenv("FARS_API_PREFIX", ""),
        openalex_base_url=os.getenv("FARS_OPENALEX_BASE_URL", "https://api.openalex.org"),
        openalex_api_key=os.getenv("FARS_OPENALEX_API_KEY"),
        grobid_base_url=os.getenv("FARS_GROBID_BASE_URL", "http://localhost:8070"),
        service_name=os.getenv("FARS_SERVICE_NAME", "fars-paper-kg"),
        default_topic_expansion_limit=int(os.getenv("FARS_TOPIC_EXPANSION_LIMIT", "8")),
    )
