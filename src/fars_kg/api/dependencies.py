from __future__ import annotations

from collections.abc import Generator

from fastapi import Request
from sqlalchemy.orm import Session

from fars_kg.connectors.openalex import OpenAlexClientProtocol
from fars_kg.db import DatabaseManager
from fars_kg.parsers.base import ParserProtocol


def get_db_manager(request: Request) -> DatabaseManager:
    return request.app.state.db


def get_db_session(request: Request) -> Generator[Session, None, None]:
    db: DatabaseManager = request.app.state.db
    with db.session() as session:
        yield session


def get_openalex_client(request: Request) -> OpenAlexClientProtocol:
    return request.app.state.openalex_client


def get_default_parser(request: Request) -> ParserProtocol:
    return request.app.state.default_parser
