from fastapi import APIRouter, Depends, HTTPException, Query, status

from fars.api.schemas import PaperVersionsResponse, TopicIngestRequest, TopicIngestResponse
from fars.dependencies import get_knowledge_base
from fars.repositories.memory import InMemoryKnowledgeBase

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("/search")
def search_papers(
    q: str = Query(..., min_length=1),
    knowledge_base: InMemoryKnowledgeBase = Depends(get_knowledge_base),
):
    return knowledge_base.search(q)


@router.get("/{paper_id}")
def get_paper(
    paper_id: str,
    knowledge_base: InMemoryKnowledgeBase = Depends(get_knowledge_base),
):
    paper = knowledge_base.get(paper_id)
    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper '{paper_id}' was not found.",
        )
    return paper


@router.get("/{paper_id}/versions", response_model=PaperVersionsResponse)
def get_paper_versions(
    paper_id: str,
    knowledge_base: InMemoryKnowledgeBase = Depends(get_knowledge_base),
):
    if knowledge_base.get(paper_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper '{paper_id}' was not found.",
        )
    return PaperVersionsResponse(
        paper_id=paper_id,
        versions=knowledge_base.list_versions(paper_id),
    )


@router.post("/ingest/topic", response_model=TopicIngestResponse)
def ingest_topic(
    payload: TopicIngestRequest,
    knowledge_base: InMemoryKnowledgeBase = Depends(get_knowledge_base),
):
    results = knowledge_base.search(payload.query)[: payload.limit]
    return TopicIngestResponse(query=payload.query, count=len(results), results=results)
