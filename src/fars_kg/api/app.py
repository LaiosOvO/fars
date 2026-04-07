from __future__ import annotations

from fastapi import FastAPI

from fars_kg.api.routes import graph_router, health_router, papers_router, topics_router
from fars_kg.config import Settings, get_settings
from fars_kg.connectors.openalex import OpenAlexClientProtocol, OpenAlexHTTPClient
from fars_kg.db import DatabaseManager
from fars_kg.parsers.base import NoopParser, ParserProtocol
from fars_kg.parsers.grobid import GrobidParser


def create_app(
    *,
    settings: Settings | None = None,
    openalex_client: OpenAlexClientProtocol | None = None,
    default_parser: ParserProtocol | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    db = DatabaseManager(settings.database_url)
    db.init_db()

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

    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(topics_router, prefix=settings.api_prefix)
    app.include_router(papers_router, prefix=settings.api_prefix)
    app.include_router(graph_router, prefix=settings.api_prefix)
    return app


app = create_app()
