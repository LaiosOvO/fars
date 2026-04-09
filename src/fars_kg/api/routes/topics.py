from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from fars_kg.api.dependencies import get_db_session, get_openalex_client
from fars_kg.connectors.openalex import OpenAlexClientProtocol
from fars_kg.schemas import IngestTopicRequest, IngestTopicResponse, TopicLandscapeResponse
from fars_kg.services.ingestion import TopicIngestionService
from fars_kg.services.repository import build_topic_landscape

router = APIRouter(prefix="/topics", tags=["topics"])


@router.post("/ingest", response_model=IngestTopicResponse)
def ingest_topic(
    payload: IngestTopicRequest,
    session: Session = Depends(get_db_session),
    openalex_client: OpenAlexClientProtocol = Depends(get_openalex_client),
) -> IngestTopicResponse:
    result = TopicIngestionService(openalex_client).ingest_topic(session=session, topic=payload.topic, limit=payload.limit)
    return IngestTopicResponse(**result.__dict__)


@router.get("/landscape", response_model=TopicLandscapeResponse)
def topic_landscape(
    q: str,
    limit: int = 20,
    session: Session = Depends(get_db_session),
) -> TopicLandscapeResponse:
    return TopicLandscapeResponse(**build_topic_landscape(session, q, limit=limit))
