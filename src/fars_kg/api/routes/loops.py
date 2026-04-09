from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from fars_kg.api.dependencies import get_db_manager, get_db_session, get_default_parser, get_openalex_client, get_worktree_manager
from fars_kg.db import DatabaseManager
from fars_kg.parsers.base import ParserProtocol
from fars_kg.schemas import (
    AutonomousResearchLoopRequest,
    AutonomousResearchLoopResponse,
    BatchArtifactIndexItem,
    BatchArtifactManifestResponse,
    BatchAutonomousResearchLoopRequest,
    BatchAutonomousResearchLoopResponse,
    ContinueRunRequest,
    RunReconciliationRequest,
    RunReconciliationResponse,
)
from fars_kg.services.research_loop import AutonomousResearchLoopService
from fars_kg.worktree import GitWorktreeManager

router = APIRouter(prefix="/research-loops", tags=["research-loops"])


@router.get("/batches", response_model=list[BatchArtifactIndexItem])
def list_batch_artifacts(
    limit: int = 20,
    kind: str | None = None,
    openalex_client=Depends(get_openalex_client),
    parser: ParserProtocol = Depends(get_default_parser),
    worktree_manager: GitWorktreeManager = Depends(get_worktree_manager),
) -> list[BatchArtifactIndexItem]:
    rows = AutonomousResearchLoopService(
        openalex_client=openalex_client,
        parser=parser,
        worktree_manager=worktree_manager,
    ).list_batch_artifacts(limit=limit, kind=kind)
    return [BatchArtifactIndexItem(**row) for row in rows]


@router.post("/run", response_model=AutonomousResearchLoopResponse)
def run_research_loop(
    payload: AutonomousResearchLoopRequest,
    session: Session = Depends(get_db_session),
    openalex_client=Depends(get_openalex_client),
    parser: ParserProtocol = Depends(get_default_parser),
    worktree_manager: GitWorktreeManager = Depends(get_worktree_manager),
) -> AutonomousResearchLoopResponse:
    try:
        result = AutonomousResearchLoopService(
            openalex_client=openalex_client,
            parser=parser,
            worktree_manager=worktree_manager,
        ).run(
            session,
            topic=payload.topic,
            limit=payload.limit,
            iterations=payload.iterations,
            branch_name=payload.branch_name,
            use_worktree=payload.use_worktree,
            llm_profile=payload.llm_profile,
            llm_model=payload.llm_model,
            llm_reasoning_effort=payload.llm_reasoning_effort,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AutonomousResearchLoopResponse(**result.__dict__)


@router.post("/batch-run", response_model=BatchAutonomousResearchLoopResponse)
def run_batch_research_loop(
    payload: BatchAutonomousResearchLoopRequest,
    db_manager: DatabaseManager = Depends(get_db_manager),
    openalex_client=Depends(get_openalex_client),
    parser: ParserProtocol = Depends(get_default_parser),
    worktree_manager: GitWorktreeManager = Depends(get_worktree_manager),
) -> BatchAutonomousResearchLoopResponse:
    try:
        result = AutonomousResearchLoopService(
            openalex_client=openalex_client,
            parser=parser,
            worktree_manager=worktree_manager,
        ).run_batch(
            db_manager,
            topics=payload.topics,
            limit=payload.limit,
            iterations=payload.iterations,
            use_worktree=payload.use_worktree,
            max_concurrency=payload.max_concurrency,
            branch_prefix=payload.branch_prefix,
            llm_profile=payload.llm_profile,
            llm_model=payload.llm_model,
            llm_reasoning_effort=payload.llm_reasoning_effort,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return BatchAutonomousResearchLoopResponse(**asdict(result))


@router.post("/reconcile", response_model=RunReconciliationResponse)
def reconcile_research_runs(
    payload: RunReconciliationRequest,
    db_manager: DatabaseManager = Depends(get_db_manager),
    openalex_client=Depends(get_openalex_client),
    parser: ParserProtocol = Depends(get_default_parser),
    worktree_manager: GitWorktreeManager = Depends(get_worktree_manager),
) -> RunReconciliationResponse:
    try:
        result = AutonomousResearchLoopService(
            openalex_client=openalex_client,
            parser=parser,
            worktree_manager=worktree_manager,
        ).reconcile_runs(
            db_manager,
            run_ids=payload.run_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RunReconciliationResponse(**asdict(result))


@router.get("/batches/{batch_id}/manifest", response_model=BatchArtifactManifestResponse)
def read_batch_manifest(
    batch_id: str,
    openalex_client=Depends(get_openalex_client),
    parser: ParserProtocol = Depends(get_default_parser),
    worktree_manager: GitWorktreeManager = Depends(get_worktree_manager),
) -> BatchArtifactManifestResponse:
    try:
        payload = AutonomousResearchLoopService(
            openalex_client=openalex_client,
            parser=parser,
            worktree_manager=worktree_manager,
        ).read_batch_manifest(batch_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return BatchArtifactManifestResponse(**payload)


@router.get("/batches/{batch_id}/download")
def download_batch_bundle(
    batch_id: str,
    openalex_client=Depends(get_openalex_client),
    parser: ParserProtocol = Depends(get_default_parser),
    worktree_manager: GitWorktreeManager = Depends(get_worktree_manager),
) -> FileResponse:
    try:
        zip_path = AutonomousResearchLoopService(
            openalex_client=openalex_client,
            parser=parser,
            worktree_manager=worktree_manager,
        ).get_batch_zip_path(batch_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(path=zip_path, filename=zip_path.name, media_type="application/zip")


@router.get("/batches/{batch_id}/summary/download")
def download_batch_summary(
    batch_id: str,
    openalex_client=Depends(get_openalex_client),
    parser: ParserProtocol = Depends(get_default_parser),
    worktree_manager: GitWorktreeManager = Depends(get_worktree_manager),
) -> FileResponse:
    try:
        summary_path = AutonomousResearchLoopService(
            openalex_client=openalex_client,
            parser=parser,
            worktree_manager=worktree_manager,
        ).get_batch_summary_path(batch_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(path=summary_path, filename=summary_path.name, media_type="application/json")


@router.get("/batches/{batch_id}/items/download")
def download_batch_items(
    batch_id: str,
    openalex_client=Depends(get_openalex_client),
    parser: ParserProtocol = Depends(get_default_parser),
    worktree_manager: GitWorktreeManager = Depends(get_worktree_manager),
) -> FileResponse:
    try:
        items_path = AutonomousResearchLoopService(
            openalex_client=openalex_client,
            parser=parser,
            worktree_manager=worktree_manager,
        ).get_batch_items_path(batch_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(path=items_path, filename=items_path.name, media_type="application/json")


@router.get("/batches/{batch_id}/reconciliation/download")
def download_batch_reconciliation(
    batch_id: str,
    openalex_client=Depends(get_openalex_client),
    parser: ParserProtocol = Depends(get_default_parser),
    worktree_manager: GitWorktreeManager = Depends(get_worktree_manager),
) -> FileResponse:
    try:
        reconciliation_path = AutonomousResearchLoopService(
            openalex_client=openalex_client,
            parser=parser,
            worktree_manager=worktree_manager,
        ).get_batch_reconciliation_path(batch_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(path=reconciliation_path, filename=reconciliation_path.name, media_type="application/json")


@router.post("/{run_id}/continue", response_model=AutonomousResearchLoopResponse)
def continue_research_loop(
    run_id: int,
    payload: ContinueRunRequest,
    session: Session = Depends(get_db_session),
    openalex_client=Depends(get_openalex_client),
    parser: ParserProtocol = Depends(get_default_parser),
    worktree_manager: GitWorktreeManager = Depends(get_worktree_manager),
) -> AutonomousResearchLoopResponse:
    try:
        result = AutonomousResearchLoopService(
            openalex_client=openalex_client,
            parser=parser,
            worktree_manager=worktree_manager,
        ).continue_run(
            session,
            run_id=run_id,
            iterations=payload.iterations,
            llm_profile=payload.llm_profile,
            llm_model=payload.llm_model,
            llm_reasoning_effort=payload.llm_reasoning_effort,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AutonomousResearchLoopResponse(**result.__dict__)
