from __future__ import annotations

from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


EdgeType = Literal[
    "cites",
    "extends",
    "compares",
    "contradicts",
    "reproduces",
    "uses_dataset",
    "proposes_method",
    "reports_result_against",
]


class IdentifierSet(BaseModel):
    doi: str | None = None
    arxiv_id: str | None = None
    openalex_id: str | None = None
    semantic_scholar_id: str | None = None

    def keys(self) -> list[tuple[str, str]]:
        keys: list[tuple[str, str]] = []
        for name in ("doi", "arxiv_id", "openalex_id", "semantic_scholar_id"):
            value = getattr(self, name)
            if value:
                keys.append((name, value))
        return keys


class PaperVersion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    version_type: str = "unknown"
    source_url: str | None = None
    pdf_url: str | None = None
    tei_url: str | None = None
    checksum: str | None = None


class PaperSection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    section_type: str = "unknown"
    heading: str | None = None
    order_index: int = 0
    text: str = ""


class PaperChunk(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    section_id: str | None = None
    text: str
    page_start: int | None = None
    page_end: int | None = None
    bbox_json: dict | None = None


class ParsedReference(BaseModel):
    raw_reference: str
    target_title: str | None = None
    target_year: int | None = None
    target_identifiers: IdentifierSet = Field(default_factory=IdentifierSet)


class CitationContext(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    context_text: str
    context_type: str = "unknown"
    raw_reference: str | None = None


class ParsedPaper(BaseModel):
    title: str | None = None
    abstract: str | None = None
    sections: list[PaperSection] = Field(default_factory=list)
    chunks: list[PaperChunk] = Field(default_factory=list)
    references: list[ParsedReference] = Field(default_factory=list)
    citation_contexts: list[CitationContext] = Field(default_factory=list)
    raw_tei: str | None = None


class PaperRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    abstract: str | None = None
    normalized_title: str | None = None
    year: int | None = None
    venue: str | None = None
    authors: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    identifiers: IdentifierSet = Field(default_factory=IdentifierSet)
    versions: list[PaperVersion] = Field(default_factory=list)
    parsed: ParsedPaper | None = None


class PaperEdge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    src_paper_id: str
    dst_paper_id: str
    edge_type: EdgeType = "cites"
    confidence: float = 1.0
    evidence_text: str | None = None
    source: str = "manual"


class TopicExpansionRequest(BaseModel):
    topic: str
    max_terms: int | None = None


class TopicExpansionResponse(BaseModel):
    topic: str
    expansions: list[str]


class GraphNeighborhood(BaseModel):
    paper_id: str
    papers: list[PaperRecord]
    edges: list[PaperEdge]


class EvidencePack(BaseModel):
    paper_id: str
    topic: str | None = None
    center_paper: PaperRecord
    related_papers: list[PaperRecord]
    edges: list[PaperEdge]
