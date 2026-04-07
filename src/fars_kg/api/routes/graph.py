from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from fars_kg.api.dependencies import get_db_session
from fars_kg.schemas import GraphNeighborResponse
from fars_kg.services.repository import list_graph_neighbors

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/papers/{paper_id}/neighbors", response_model=list[GraphNeighborResponse])
def neighbors(paper_id: int, session: Session = Depends(get_db_session)) -> list[GraphNeighborResponse]:
    rows = list_graph_neighbors(session, paper_id)
    return [
        GraphNeighborResponse(
            paper_id=paper.id,
            title=paper.canonical_title,
            edge_type=edge.edge_type,
            confidence=edge.confidence,
        )
        for edge, paper in rows
    ]
