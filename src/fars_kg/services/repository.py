from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from fars_kg.connectors.openalex import OpenAlexWork
from fars_kg.models import Citation, CitationContext, Paper, PaperChunk, PaperEdge, PaperSection, PaperVersion
from fars_kg.parsers.base import ParseResult


@dataclass
class UpsertResult:
    paper: Paper
    created: bool
    version: PaperVersion
    version_created: bool


@dataclass
class ParsePersistenceResult:
    sections_created: int
    chunks_created: int
    citations_created: int
    contexts_created: int
    edges_created: int


def normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    doi = doi.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.lower().startswith(prefix):
            return doi[len(prefix) :]
    return doi


def get_paper(session: Session, paper_id: int) -> Paper | None:
    stmt = (
        select(Paper)
        .where(Paper.id == paper_id)
        .options(selectinload(Paper.versions))
    )
    return session.scalar(stmt)


def get_paper_by_identifiers(session: Session, *, openalex_id: str | None = None, doi: str | None = None, arxiv_id: str | None = None) -> Paper | None:
    if openalex_id:
        paper = session.scalar(select(Paper).where(Paper.openalex_id == openalex_id))
        if paper:
            return paper
    if doi:
        paper = session.scalar(select(Paper).where(Paper.doi == doi))
        if paper:
            return paper
    if arxiv_id:
        paper = session.scalar(select(Paper).where(Paper.arxiv_id == arxiv_id))
        if paper:
            return paper
    return None


def upsert_paper_from_openalex(session: Session, work: OpenAlexWork) -> UpsertResult:
    normalized_doi = normalize_doi(work.doi)
    paper = get_paper_by_identifiers(session, openalex_id=work.openalex_id, doi=normalized_doi, arxiv_id=work.arxiv_id)
    created = paper is None
    if paper is None:
        paper = Paper(canonical_title=work.title)
        session.add(paper)
        session.flush()

    paper.canonical_title = work.title
    paper.openalex_id = work.openalex_id or paper.openalex_id
    paper.doi = normalized_doi or paper.doi
    paper.arxiv_id = work.arxiv_id or paper.arxiv_id
    paper.publication_year = work.publication_year
    paper.venue = work.venue
    paper.abstract = work.abstract
    paper.language = work.language
    paper.is_open_access = work.is_open_access
    paper.citation_count = work.citation_count
    paper.primary_source = work.primary_source

    version = session.scalar(
        select(PaperVersion).where(
            PaperVersion.paper_id == paper.id,
            PaperVersion.source_url == work.source_url,
            PaperVersion.pdf_url == work.pdf_url,
        )
    )
    version_created = version is None
    if version is None:
        version = PaperVersion(
            paper_id=paper.id,
            version_type="source",
            source_url=work.source_url,
            pdf_url=work.pdf_url,
        )
        session.add(version)
        session.flush()
    else:
        version.source_url = work.source_url
        version.pdf_url = work.pdf_url

    return UpsertResult(paper=paper, created=created, version=version, version_created=version_created)


def persist_parse_result(session: Session, version: PaperVersion, result: ParseResult, parser_provider: str) -> ParsePersistenceResult:
    version.raw_tei_xml = result.raw_tei_xml
    version.parse_status = f"parsed:{parser_provider}"
    version.parse_error = None

    for existing in list(version.sections):
        session.delete(existing)
    for existing in list(version.citations):
        session.delete(existing)
    session.flush()

    sections_created = 0
    chunks_created = 0
    citations_created = 0
    contexts_created = 0
    edges_created = 0

    for section_index, parsed_section in enumerate(result.sections):
        section = PaperSection(
            paper_version_id=version.id,
            section_type=parsed_section.section_type,
            heading=parsed_section.heading,
            order_index=section_index,
            page_start=parsed_section.page_start,
            page_end=parsed_section.page_end,
            text="\n\n".join(parsed_section.paragraphs) if parsed_section.paragraphs else None,
        )
        session.add(section)
        session.flush()
        sections_created += 1

        for chunk_index, paragraph in enumerate(parsed_section.paragraphs):
            chunk = PaperChunk(
                section_id=section.id,
                text=paragraph,
                order_index=chunk_index,
                page_start=parsed_section.page_start,
                page_end=parsed_section.page_end,
            )
            session.add(chunk)
            chunks_created += 1

    session.flush()

    for parsed_citation in result.citations:
        target_paper = get_paper_by_identifiers(
            session,
            openalex_id=parsed_citation.target_openalex_id,
            doi=normalize_doi(parsed_citation.target_doi),
        )
        citation = Citation(
            source_paper_version_id=version.id,
            target_paper_id=target_paper.id if target_paper else None,
            raw_reference=parsed_citation.raw_reference,
            citation_key=parsed_citation.citation_key,
            resolution_confidence=parsed_citation.resolution_confidence,
        )
        session.add(citation)
        session.flush()
        citations_created += 1

        for context_text in parsed_citation.contexts:
            context = CitationContext(citation_id=citation.id, context_text=context_text, context_type="unknown")
            session.add(context)
            contexts_created += 1

        if target_paper:
            edge = PaperEdge(
                src_paper_id=version.paper_id,
                dst_paper_id=target_paper.id,
                edge_type="cites",
                confidence=max(parsed_citation.resolution_confidence, 0.5),
                source="citation",
            )
            session.add(edge)
            edges_created += 1

    return ParsePersistenceResult(
        sections_created=sections_created,
        chunks_created=chunks_created,
        citations_created=citations_created,
        contexts_created=contexts_created,
        edges_created=edges_created,
    )


def list_graph_neighbors(session: Session, paper_id: int) -> list[tuple[PaperEdge, Paper]]:
    stmt = (
        select(PaperEdge, Paper)
        .join(Paper, Paper.id == PaperEdge.dst_paper_id)
        .where(PaperEdge.src_paper_id == paper_id)
        .order_by(Paper.canonical_title.asc())
    )
    return list(session.execute(stmt).all())
