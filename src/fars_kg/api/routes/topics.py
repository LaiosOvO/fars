from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from fars_kg.api.dependencies import get_db_session, get_openalex_client
from fars_kg.connectors.openalex import OpenAlexClientProtocol
from fars_kg.schemas import IngestTopicRequest, IngestTopicResponse
from fars_kg.services.ingestion import TopicIngestionService

router = APIRouter(prefix="/topics", tags=["topics"])


@router.post("/ingest", response_model=IngestTopicResponse)
def ingest_topic(
    payload: IngestTopicRequest,
    session: Session = Depends(get_db_session),
    openalex_client: OpenAlexClientProtocol = Depends(get_openalex_client),
) -> IngestTopicResponse:
    result = TopicIngestionService(openalex_client).ingest_topic(session=session, topic=payload.topic, limit=payload.limit)
    return IngestTopicResponse(**result.__dict__)
