from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field


class ParsedSection(BaseModel):
    section_type: str = "unknown"
    heading: str | None = None
    paragraphs: list[str] = Field(default_factory=list)
    page_start: int | None = None
    page_end: int | None = None


class ParsedCitation(BaseModel):
    raw_reference: str
    citation_key: str | None = None
    target_openalex_id: str | None = None
    target_doi: str | None = None
    resolution_confidence: float = 0.0
    contexts: list[str] = Field(default_factory=list)


class ParseResult(BaseModel):
    raw_tei_xml: str | None = None
    sections: list[ParsedSection] = Field(default_factory=list)
    citations: list[ParsedCitation] = Field(default_factory=list)


class ParserProtocol(Protocol):
    provider_name: str

    def parse_version(self, version: object) -> ParseResult: ...


class NoopParser:
    provider_name = "noop"

    def parse_version(self, version: object) -> ParseResult:
        return ParseResult()
