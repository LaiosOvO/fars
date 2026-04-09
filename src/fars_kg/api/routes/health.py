from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from fars_kg.api.dependencies import get_db_session
from fars_kg.schemas import HealthResponse, ReadinessResponse, SystemInfoResponse
from fars_kg.services.repository import get_system_counts

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/health/readiness", response_model=ReadinessResponse)
def readiness(request: Request, response: Response, session: Session = Depends(get_db_session)) -> ReadinessResponse:
    settings = request.app.state.settings
    try:
        request.app.state.db.ping()
        counts = get_system_counts(session)
    except SQLAlchemyError:
        response.status_code = 503
        return ReadinessResponse(
            status="not_ready",
            app=settings.app_name,
            version=settings.app_version,
            environment=settings.environment,
            database_status="error",
            database_bootstrap_mode=settings.database_bootstrap_mode,
            request_logging_enabled=settings.enable_request_logging,
            paper_count=0,
            run_count=0,
        )
    return ReadinessResponse(
        status="ready",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        database_status="ok",
        database_bootstrap_mode=settings.database_bootstrap_mode,
        request_logging_enabled=settings.enable_request_logging,
        paper_count=counts["paper_count"],
        run_count=counts["run_count"],
    )


@router.get("/system/info", response_model=SystemInfoResponse)
def system_info(request: Request) -> SystemInfoResponse:
    settings = request.app.state.settings
    return SystemInfoResponse(
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        api_prefix=settings.api_prefix,
        database_bootstrap_mode=settings.database_bootstrap_mode,
        parser_provider=settings.parser_provider,
        artifacts_root=settings.artifacts_root,
        repo_root=settings.repo_root,
        worktree_root=settings.worktree_root,
        request_id_header=settings.request_id_header,
        request_logging_enabled=settings.enable_request_logging,
    )
