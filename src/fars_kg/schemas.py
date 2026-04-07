from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str
    app: str


class IngestTopicRequest(BaseModel):
    topic: str = Field(min_length=2)
    limit: int = Field(default=10, ge=1, le=50)


class IngestTopicResponse(BaseModel):
    topic: str
    papers_created: int
    papers_updated: int
    versions_created: int
    paper_ids: list[int]
    version_ids: list[int]


class ParseVersionResponse(BaseModel):
    version_id: int
    sections_created: int
    chunks_created: int
    citations_created: int
    contexts_created: int
    edges_created: int
    parser_provider: str


class PaperVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    version_type: str
    source_url: str | None = None
    pdf_url: str | None = None
    local_pdf_path: str | None = None
    parse_status: str


class PaperRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    canonical_title: str
    doi: str | None = None
    openalex_id: str | None = None
    publication_year: int | None = None
    venue: str | None = None
    citation_count: int


class PaperDetailResponse(PaperRead):
    abstract: str | None = None
    is_open_access: bool
    primary_source: str | None = None
    versions: list[PaperVersionRead] = []


class GraphNeighborResponse(BaseModel):
    paper_id: int
    title: str
    edge_type: str
    confidence: float
