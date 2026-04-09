from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from fastapi import HTTPException

from fars_kg.api.dependencies import get_db_session
from fars_kg.schemas import (
    GraphExplanationResponse,
    GraphMermaidResponse,
    GraphNeighborResponse,
    SemanticEdgeInferenceResponse,
)
from fars_kg.services.repository import build_graph_explanations, get_paper, infer_semantic_edges, list_graph_neighbors

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


@router.get("/papers/{paper_id}/mermaid", response_model=GraphMermaidResponse)
def mermaid_graph(paper_id: int, session: Session = Depends(get_db_session)) -> GraphMermaidResponse:
    center = get_paper(session, paper_id)
    if center is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    rows = list_graph_neighbors(session, paper_id)
    lines = ["graph LR", f'    P{paper_id}["{center.canonical_title}"]']
    for edge, paper in rows:
        lines.append(f'    P{paper_id} -->|{edge.edge_type}| P{paper.id}["{paper.canonical_title}"]')
    return GraphMermaidResponse(paper_id=paper_id, mermaid="\n".join(lines))


@router.get("/papers/{paper_id}/explanations", response_model=GraphExplanationResponse)
def graph_explanations(paper_id: int, session: Session = Depends(get_db_session)) -> GraphExplanationResponse:
    try:
        payload = build_graph_explanations(session, paper_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return GraphExplanationResponse(**payload)


@router.post("/papers/{paper_id}/infer-semantic-edges", response_model=SemanticEdgeInferenceResponse)
def infer_edges(paper_id: int, session: Session = Depends(get_db_session)) -> SemanticEdgeInferenceResponse:
    try:
        result = infer_semantic_edges(session, paper_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SemanticEdgeInferenceResponse(**result.__dict__)
