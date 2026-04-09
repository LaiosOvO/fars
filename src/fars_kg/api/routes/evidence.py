from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from fars_kg.api.dependencies import get_db_session
from fars_kg.schemas import (
    AutoSemanticEnrichmentResponse,
    EvidencePackResponse,
    SemanticEnrichmentRequest,
    SemanticEnrichmentResponse,
)
from fars_kg.services.repository import attach_semantic_enrichment, auto_attach_semantic_enrichment, build_evidence_pack

router = APIRouter(tags=["evidence"])


@router.post("/papers/{paper_id}/semantic-enrichment", response_model=SemanticEnrichmentResponse)
def semantic_enrichment(
    paper_id: int,
    payload: SemanticEnrichmentRequest,
    session: Session = Depends(get_db_session),
) -> SemanticEnrichmentResponse:
    try:
        result = attach_semantic_enrichment(
            session,
            paper_id,
            methods=payload.methods,
            datasets=payload.datasets,
            metrics=payload.metrics,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SemanticEnrichmentResponse(**result.__dict__)


@router.post("/papers/{paper_id}/semantic-enrichment/auto", response_model=AutoSemanticEnrichmentResponse)
def auto_semantic_enrichment(
    paper_id: int,
    session: Session = Depends(get_db_session),
) -> AutoSemanticEnrichmentResponse:
    try:
        result = auto_attach_semantic_enrichment(session, paper_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AutoSemanticEnrichmentResponse(**result.__dict__)


@router.get("/papers/{paper_id}/evidence-pack", response_model=EvidencePackResponse)
def evidence_pack(paper_id: int, session: Session = Depends(get_db_session)) -> EvidencePackResponse:
    try:
        payload = build_evidence_pack(session, paper_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return EvidencePackResponse(**payload)
