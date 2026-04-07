from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from fars_kg.api.dependencies import get_db_session, get_default_parser
from fars_kg.models import PaperVersion
from fars_kg.parsers.base import ParserProtocol
from fars_kg.schemas import PaperDetailResponse, ParseVersionResponse
from fars_kg.services.parsing import ParsingService
from fars_kg.services.repository import get_paper

router = APIRouter(tags=["papers"])


@router.get("/papers/{paper_id}", response_model=PaperDetailResponse)
def read_paper(paper_id: int, session: Session = Depends(get_db_session)) -> PaperDetailResponse:
    paper = get_paper(session, paper_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    return PaperDetailResponse.model_validate(paper)


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
