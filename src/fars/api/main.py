from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from fars.config import get_settings
from fars.models import GraphNeighborhood, PaperEdge, PaperRecord, TopicExpansionRequest, TopicExpansionResponse
from fars.repository import InMemoryKnowledgeBase
from fars.services.normalize import normalize_identifiers, normalize_title
from fars.services.topic import expand_topic


def create_app(repo: InMemoryKnowledgeBase | None = None) -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="FARS", version="0.1.0")
    app.state.repo = repo or InMemoryKnowledgeBase()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.service_name}

    @app.post("/topics/expand", response_model=TopicExpansionResponse)
    def topic_expand(payload: TopicExpansionRequest) -> TopicExpansionResponse:
        max_terms = payload.max_terms or settings.default_topic_expansion_limit
        return TopicExpansionResponse(topic=payload.topic, expansions=expand_topic(payload.topic, max_terms=max_terms))

    @app.post("/papers/ingest", response_model=PaperRecord)
    def paper_ingest(payload: PaperRecord) -> PaperRecord:
        normalized = payload.model_copy(
            update={
                "identifiers": normalize_identifiers(payload.identifiers),
                "normalized_title": normalize_title(payload.normalized_title or payload.title),
            }
        )
        return app.state.repo.upsert_paper(normalized)

    @app.get("/papers", response_model=list[PaperRecord])
    def list_papers() -> list[PaperRecord]:
        return app.state.repo.list_papers()

    @app.get("/papers/{paper_id}", response_model=PaperRecord)
    def get_paper(paper_id: str) -> PaperRecord:
        paper = app.state.repo.get_paper(paper_id)
        if paper is None:
            raise HTTPException(status_code=404, detail="paper not found")
        return paper

    @app.post("/graph/edges", response_model=PaperEdge)
    def add_edge(edge: PaperEdge) -> PaperEdge:
        if app.state.repo.get_paper(edge.src_paper_id) is None or app.state.repo.get_paper(edge.dst_paper_id) is None:
            raise HTTPException(status_code=400, detail="edge endpoints must reference known papers")
        return app.state.repo.add_edge(edge)

    @app.get("/papers/{paper_id}/graph", response_model=GraphNeighborhood)
    def graph(paper_id: str) -> GraphNeighborhood:
        if app.state.repo.get_paper(paper_id) is None:
            raise HTTPException(status_code=404, detail="paper not found")
        return app.state.repo.get_neighbors(paper_id)

    @app.get("/papers/{paper_id}/evidence-pack")
    def evidence_pack(paper_id: str, topic: str | None = Query(default=None)) -> dict:
        if app.state.repo.get_paper(paper_id) is None:
            raise HTTPException(status_code=404, detail="paper not found")
        return app.state.repo.build_evidence_pack(paper_id, topic=topic).model_dump()

    return app
