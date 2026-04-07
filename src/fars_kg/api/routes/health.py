from fastapi import APIRouter, Request

from fars_kg.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    return HealthResponse(status="ok", app=request.app.state.settings.app_name)
