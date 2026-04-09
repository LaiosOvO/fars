from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from fars_kg.api.dependencies import get_db_session, get_default_parser
from fars_kg.models import PaperVersion
from fars_kg.parsers.base import ParserProtocol
from fars_kg.schemas import (
    CitationContextRead,
    CitationRead,
    ExperimentResultRead,
    PaperDetailResponse,
    PaperRead,
    PaperSectionRead,
    PaperVersionRead,
    ParseVersionResponse,
)
from fars_kg.services.parsing import ParsingService
from fars_kg.services.repository import (
    build_paper_result_stats,
    get_paper,
    list_experiment_results,
    list_paper_citations,
    list_paper_sections,
    search_papers,
)

router = APIRouter(tags=["papers"])


@router.get("/papers/search", response_model=list[PaperRead])
def paper_search(
    q: str,
    limit: int = 20,
    session: Session = Depends(get_db_session),
) -> list[PaperRead]:
    papers = search_papers(session, q, limit=limit)
    return [PaperRead.model_validate(paper) for paper in papers]


@router.get("/papers/{paper_id}", response_model=PaperDetailResponse)
def read_paper(paper_id: int, session: Session = Depends(get_db_session)) -> PaperDetailResponse:
    paper = get_paper(session, paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    return PaperDetailResponse(
        id=paper.id,
        canonical_title=paper.canonical_title,
        doi=paper.doi,
        openalex_id=paper.openalex_id,
        publication_year=paper.publication_year,
        venue=paper.venue,
        citation_count=paper.citation_count,
        abstract=paper.abstract,
        is_open_access=paper.is_open_access,
        primary_source=paper.primary_source,
        versions=[PaperVersionRead.model_validate(version) for version in paper.versions],
        result_stats=build_paper_result_stats(paper),
    )


@router.get("/papers/{paper_id}/results", response_model=list[ExperimentResultRead])
def read_paper_results(paper_id: int, session: Session = Depends(get_db_session)) -> list[ExperimentResultRead]:
    paper = get_paper(session, paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    results = list_experiment_results(session, paper_id)
    return [
        ExperimentResultRead(
            id=result.id,
            run_id=result.run_id,
            paper_id=result.paper_id,
            method_name=result.method.name if result.method else None,
            dataset_name=result.dataset.name if result.dataset else None,
            metric_name=result.metric.name if result.metric else None,
            value=result.value,
            source=result.source,
            notes=result.notes,
        )
        for result in results
    ]


@router.get("/papers/{paper_id}/sections", response_model=list[PaperSectionRead])
def read_paper_sections(paper_id: int, session: Session = Depends(get_db_session)) -> list[PaperSectionRead]:
    try:
        sections = list_paper_sections(session, paper_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [
        PaperSectionRead(
            id=section.id,
            section_type=section.section_type,
            heading=section.heading,
            order_index=section.order_index,
            text=section.text,
        )
        for section in sections
    ]


@router.get("/papers/{paper_id}/citations", response_model=list[CitationRead])
def read_paper_citations(paper_id: int, session: Session = Depends(get_db_session)) -> list[CitationRead]:
    try:
        citations = list_paper_citations(session, paper_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [
        CitationRead(
            id=citation.id,
            raw_reference=citation.raw_reference,
            citation_key=citation.citation_key,
            target_paper_id=citation.target_paper_id,
            target_paper_title=citation.target_paper.canonical_title if citation.target_paper else None,
            resolution_confidence=citation.resolution_confidence,
            contexts=[
                CitationContextRead(
                    id=context.id,
                    context_text=context.context_text,
                    context_type=context.context_type,
                )
                for context in citation.contexts
            ],
        )
        for citation in citations
    ]


@router.post("/paper-versions/{version_id}/parse", response_model=ParseVersionResponse)
def parse_paper_version(
    version_id: int,
    session: Session = Depends(get_db_session),
    parser: ParserProtocol = Depends(get_default_parser),
) -> ParseVersionResponse:
    version = session.get(PaperVersion, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Paper version not found")
    try:
        result = ParsingService(parser).parse_version(session=session, version_id=version_id)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    persistence = result.persistence
    return ParseVersionResponse(
        version_id=result.version_id,
        parser_provider=result.parser_provider,
        sections_created=persistence.sections_created,
        chunks_created=persistence.chunks_created,
        citations_created=persistence.citations_created,
        contexts_created=persistence.contexts_created,
        edges_created=persistence.edges_created,
    )
