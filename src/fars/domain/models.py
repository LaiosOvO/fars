from pydantic import BaseModel, ConfigDict, Field

from fars.domain.types import (
    CitationContextType,
    PaperEdgeType,
    PaperVersionType,
    SectionType,
)


class PaperIdentifiers(BaseModel):
    model_config = ConfigDict(extra="forbid")

    doi: str | None = None
    arxiv_id: str | None = None
    openalex_id: str | None = None
    semantic_scholar_id: str | None = None


class PaperVersion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    paper_id: str
    version_type: PaperVersionType = PaperVersionType.UNKNOWN
    source_url: str | None = None
    pdf_url: str | None = None
    tei_url: str | None = None
    checksum: str | None = None
    fetched_at: str | None = None


class PaperSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    paper_version_id: str
    section_type: SectionType = SectionType.OTHER
    heading: str | None = None
    order_index: int = 0


class PaperChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    section_id: str
    text: str
    page_start: int | None = None
    page_end: int | None = None
    bbox_json: dict | None = None


class SourceArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    paper_version_id: str
    artifact_type: str
    storage_uri: str | None = None
    content_type: str | None = None
    created_at: str | None = None


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    source_paper_version_id: str
    target_paper_id: str | None = None
    raw_reference: str
    citation_key: str | None = None
    resolution_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class CitationContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    citation_id: str
    chunk_id: str
    context_text: str
    context_type: CitationContextType = CitationContextType.UNKNOWN


class PaperEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    src_paper_id: str
    dst_paper_id: str
    edge_type: PaperEdgeType
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_chunk_id: str | None = None
    source: str | None = None


class Paper(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    canonical_title: str
    identifiers: PaperIdentifiers = Field(default_factory=PaperIdentifiers)
    publication_year: int | None = None
    venue: str | None = None
    abstract: str | None = None
    language: str | None = None
    is_open_access: bool = False
    citation_count: int = 0
    retraction_status: str | None = None
    primary_source: str | None = None


class ParsedPaperDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    paper_version: PaperVersion
    sections: list[PaperSection] = Field(default_factory=list)
    chunks: list[PaperChunk] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    citation_contexts: list[CitationContext] = Field(default_factory=list)
    artifacts: list[SourceArtifact] = Field(default_factory=list)
