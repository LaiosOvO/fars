from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from fars_kg.models import PaperVersion
from fars_kg.parsers.base import ParserProtocol
from fars_kg.services.repository import ParsePersistenceResult, persist_parse_result


@dataclass
class ParseDispatchResult:
    version_id: int
    parser_provider: str
    persistence: ParsePersistenceResult


class ParsingService:
    def __init__(self, parser: ParserProtocol):
        self.parser = parser

    def parse_version(self, session: Session, version_id: int) -> ParseDispatchResult:
        version = session.get(PaperVersion, version_id)
        if version is None:
            raise ValueError(f"Unknown paper version: {version_id}")
        result = self.parser.parse_version(version)
        persistence = persist_parse_result(session, version, result, parser_provider=self.parser.provider_name)
        return ParseDispatchResult(version_id=version.id, parser_provider=self.parser.provider_name, persistence=persistence)
