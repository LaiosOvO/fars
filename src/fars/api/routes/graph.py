from fastapi import APIRouter, Depends, HTTPException, status

from fars.api.schemas import PaperGraphResponse
from fars.dependencies import get_knowledge_base
from fars.repositories.memory import InMemoryKnowledgeBase

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/papers/{paper_id}/neighbors", response_model=PaperGraphResponse)
def get_paper_neighbors(
    paper_id: str,
    knowledge_base: InMemoryKnowledgeBase = Depends(get_knowledge_base),
):
    if knowledge_base.get(paper_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paper '{paper_id}' was not found.",
        )
    return PaperGraphResponse(
        paper_id=paper_id,
        neighbors=knowledge_base.neighbors(paper_id),
    )
