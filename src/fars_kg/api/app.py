from __future__ import annotations

import json
import logging
import time
import uuid

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from fars_kg.api.auth import operator_access_granted
from fars_kg.api.routes import console_router, evidence_router, graph_router, health_router, loops_router, papers_router, topics_router, workflows_router
from fars_kg.config import Settings, get_settings
from fars_kg.connectors.openalex import OpenAlexClientProtocol, OpenAlexHTTPClient
from fars_kg.db import DatabaseManager
from fars_kg.parsers.base import NoopParser, ParserProtocol
from fars_kg.parsers.grobid import GrobidParser
from fars_kg.worktree import GitWorktreeManager


def create_app(
    *,
    settings: Settings | None = None,
    openalex_client: OpenAlexClientProtocol | None = None,
    default_parser: ParserProtocol | None = None,
    worktree_manager: GitWorktreeManager | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    request_logger = logging.getLogger("fars_kg.request")
    db = DatabaseManager(settings.database_url)
    db.init_db(settings.database_bootstrap_mode, settings.alembic_config_path)

    if openalex_client is None:
        openalex_client = OpenAlexHTTPClient(
            base_url=settings.openalex_base_url,
            timeout_seconds=settings.openalex_timeout_seconds,
            api_key=settings.openalex_api_key,
            mailto=settings.openalex_mailto,
        )

    if default_parser is None:
        default_parser = (
            GrobidParser(settings.grobid_base_url, settings.grobid_timeout_seconds)
            if settings.parser_provider == "grobid"
            else NoopParser()
        )

    app = FastAPI(title=settings.app_name)
    app.state.settings = settings
    app.state.db = db
    app.state.openalex_client = openalex_client
    app.state.default_parser = default_parser
    app.state.worktree_manager = worktree_manager or GitWorktreeManager(
        repo_root=settings.repo_root,
        worktree_root=settings.worktree_root,
    )

    @app.middleware("http")
    async def request_context_middleware(request, call_next):
        normalized_path = request.url.path.rstrip("/") or "/"
        public_api_paths = {
            f"{settings.api_prefix}/health",
            f"{settings.api_prefix}/health/readiness",
            f"{settings.api_prefix}/system/info",
        }
        if (
            settings.operator_token
            and normalized_path.startswith(settings.api_prefix)
            and normalized_path not in public_api_paths
            and not operator_access_granted(request, settings.operator_token)
        ):
            return JSONResponse(status_code=401, content={"detail": "Operator token required"})

        request_id = request.headers.get(settings.request_id_header) or str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 3)
        response.headers[settings.request_id_header] = request_id
        response.headers["X-Process-Time-Ms"] = str(duration_ms)
        if settings.enable_request_logging:
            request_logger.info(
                json.dumps(
                    {
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                    },
                    sort_keys=True,
                )
            )
        return response

    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(topics_router, prefix=settings.api_prefix)
    app.include_router(papers_router, prefix=settings.api_prefix)
    app.include_router(evidence_router, prefix=settings.api_prefix)
    app.include_router(loops_router, prefix=settings.api_prefix)
    app.include_router(workflows_router, prefix=settings.api_prefix)
    app.include_router(graph_router, prefix=settings.api_prefix)
    app.include_router(console_router)
    return app


app = create_app()
