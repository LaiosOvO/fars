from fastapi import APIRouter

from fars.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def healthcheck() -> dict[str, str | bool]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "version": settings.app_version,
        "debug": settings.debug,
        "canonical_runtime": "fars_kg.api.app:app",
    }
