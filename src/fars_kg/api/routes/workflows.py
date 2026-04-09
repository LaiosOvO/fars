import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from fars_kg.api.dependencies import get_db_session, get_worktree_manager
from fars_kg.models import ResearchRun
from fars_kg.schemas import (
    AutoExperimentResultWriteRequest,
    AutoExperimentResultWriteResponse,
    ExperimentPlanRead,
    ExperimentTaskRead,
    ExperimentResultRead,
    ExperimentResultWriteRequest,
    PaperDraftResponse,
    ResearchIterationRead,
    ResearchRunEventRead,
    ResearchReportResponse,
    ResearchHypothesisRead,
    ResearchRunCreateRequest,
    ResearchRunRead,
    ResearchRunResultWriteRequest,
    RunArtifactManifestResponse,
    ResearchRunStatusResponse,
    RunArtifactBundleResponse,
    SnapshotCreateRequest,
    SnapshotRead,
    WorktreeCreateResponse,
    WorktreeExecutionManifestResponse,
)
from fars_kg.services.repository import (
    build_execution_manifest,
    build_paper_draft,
    build_research_report,
    write_run_artifact_bundle,
    create_evidence_snapshot,
    create_research_run,
    get_run,
    get_snapshot,
    add_experiment_result,
    add_run_event,
    auto_add_experiment_results,
    list_experiment_tasks,
    list_experiment_plans,
    list_hypotheses,
    list_iterations,
    list_run_events,
    list_runs,
    update_research_run_result,
)
from fars_kg.services.task_runner import DeterministicLocalTaskRunner, execute_experiment_tasks
from fars_kg.worktree import GitWorktreeManager

router = APIRouter(tags=["workflows"])


@router.get("/runs", response_model=list[ResearchRunRead])
def read_runs(session: Session = Depends(get_db_session)) -> list[ResearchRunRead]:
    runs = list_runs(session)
    return [
        ResearchRunRead(
            id=run.id,
            snapshot_id=run.snapshot_id,
            branch_name=run.branch_name,
            worktree_path=run.worktree_path,
            status=run.status,
            result_summary=run.result_summary,
            result_payload_json=run.result_payload_json,
            report_title=run.report_title,
            report_figure_path=run.report_figure_path,
            paper_draft_title=run.paper_draft_title,
            artifact_dir=run.artifact_dir,
        )
        for run in runs
    ]


@router.get("/runs/{run_id}", response_model=ResearchRunRead)
def read_run(run_id: int, session: Session = Depends(get_db_session)) -> ResearchRunRead:
    run = get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return ResearchRunRead(
        id=run.id,
        snapshot_id=run.snapshot_id,
        branch_name=run.branch_name,
        worktree_path=run.worktree_path,
        status=run.status,
        result_summary=run.result_summary,
        result_payload_json=run.result_payload_json,
        report_title=run.report_title,
        report_figure_path=run.report_figure_path,
        paper_draft_title=run.paper_draft_title,
        artifact_dir=run.artifact_dir,
    )


@router.get("/runs/{run_id}/status", response_model=ResearchRunStatusResponse)
def read_run_status(run_id: int, session: Session = Depends(get_db_session)) -> ResearchRunStatusResponse:
    run = get_run(session, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return ResearchRunStatusResponse(run_id=run.id, status=run.status, summary=run.result_summary)


@router.get("/runs/{run_id}/events", response_model=list[ResearchRunEventRead])
def read_run_events(run_id: int, session: Session = Depends(get_db_session)) -> list[ResearchRunEventRead]:
    try:
        events = list_run_events(session, run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [
        ResearchRunEventRead(
            id=event.id,
            run_id=event.run_id,
            event_type=event.event_type,
            status=event.status,
            source=event.source,
            message=event.message,
            payload_json=event.payload_json,
            time_created=event.time_created.isoformat(),
        )
        for event in events
    ]


@router.post("/papers/{paper_id}/snapshots", response_model=SnapshotRead)
def create_snapshot(
    paper_id: int,
    payload: SnapshotCreateRequest,
    session: Session = Depends(get_db_session),
) -> SnapshotRead:
    try:
        snapshot = create_evidence_snapshot(session, paper_id, topic=payload.topic)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SnapshotRead(
        id=snapshot.id,
        paper_id=snapshot.paper_id,
        topic=snapshot.topic,
        payload_json=snapshot.payload_json,
    )


@router.get("/snapshots/{snapshot_id}", response_model=SnapshotRead)
def read_snapshot(snapshot_id: int, session: Session = Depends(get_db_session)) -> SnapshotRead:
    snapshot = get_snapshot(session, snapshot_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return SnapshotRead(
        id=snapshot.id,
        paper_id=snapshot.paper_id,
        topic=snapshot.topic,
        payload_json=snapshot.payload_json,
    )


@router.post("/runs", response_model=ResearchRunRead)
def create_run(payload: ResearchRunCreateRequest, session: Session = Depends(get_db_session)) -> ResearchRunRead:
    try:
        run = create_research_run(session, snapshot_id=payload.snapshot_id, branch_name=payload.branch_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ResearchRunRead(
        id=run.id,
        snapshot_id=run.snapshot_id,
        branch_name=run.branch_name,
        worktree_path=run.worktree_path,
        status=run.status,
        result_summary=run.result_summary,
        result_payload_json=run.result_payload_json,
        report_title=run.report_title,
        report_figure_path=run.report_figure_path,
        paper_draft_title=run.paper_draft_title,
        artifact_dir=run.artifact_dir,
    )


@router.post("/runs/{run_id}/result", response_model=ResearchRunRead)
def write_result(
    run_id: int,
    payload: ResearchRunResultWriteRequest,
    session: Session = Depends(get_db_session),
) -> ResearchRunRead:
    try:
        run = update_research_run_result(
            session,
            run_id,
            status=payload.status,
            result_summary=payload.result_summary,
            result_payload_json=payload.result_payload_json,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ResearchRunRead(
        id=run.id,
        snapshot_id=run.snapshot_id,
        branch_name=run.branch_name,
        worktree_path=run.worktree_path,
        status=run.status,
        result_summary=run.result_summary,
        result_payload_json=run.result_payload_json,
        report_title=run.report_title,
        report_figure_path=run.report_figure_path,
        paper_draft_title=run.paper_draft_title,
        artifact_dir=run.artifact_dir,
    )


@router.post("/runs/{run_id}/experiment-results", response_model=ExperimentResultRead)
def write_experiment_result(
    run_id: int,
    payload: ExperimentResultWriteRequest,
    session: Session = Depends(get_db_session),
) -> ExperimentResultRead:
    try:
        result = add_experiment_result(
            session,
            run_id=run_id,
            paper_id=payload.paper_id,
            method_name=payload.method_name,
            dataset_name=payload.dataset_name,
            metric_name=payload.metric_name,
            value=payload.value,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ExperimentResultRead(
        id=result.id,
        run_id=result.run_id,
        paper_id=result.paper_id,
        method_name=result.method.name if result.method else None,
        dataset_name=result.dataset.name if result.dataset else None,
        metric_name=result.metric.name if result.metric else None,
        value=result.value,
        source=result.source,
        notes=result.notes,
    )


@router.post("/runs/{run_id}/experiment-results/auto", response_model=AutoExperimentResultWriteResponse)
def auto_write_experiment_results(
    run_id: int,
    payload: AutoExperimentResultWriteRequest,
    session: Session = Depends(get_db_session),
) -> AutoExperimentResultWriteResponse:
    try:
        results = auto_add_experiment_results(session, run_id=run_id, paper_id=payload.paper_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return AutoExperimentResultWriteResponse(
        run_id=run_id,
        paper_id=payload.paper_id,
        created_count=len(results),
        results=[
            ExperimentResultRead(
                id=result.id,
                run_id=result.run_id,
                paper_id=result.paper_id,
                method_name=result.method.name if result.method else None,
                dataset_name=result.dataset.name if result.dataset else None,
                metric_name=result.metric.name if result.metric else None,
                value=result.value,
                source=result.source,
                notes=result.notes,
            )
            for result in results
        ],
    )


@router.get("/runs/{run_id}/hypotheses", response_model=list[ResearchHypothesisRead])
def read_hypotheses(run_id: int, session: Session = Depends(get_db_session)) -> list[ResearchHypothesisRead]:
    hypotheses = list_hypotheses(session, run_id)
    return [
        ResearchHypothesisRead(
            id=hypothesis.id,
            run_id=hypothesis.run_id,
            paper_id=hypothesis.paper_id,
            statement=hypothesis.statement,
            rationale=hypothesis.rationale,
        )
        for hypothesis in hypotheses
    ]


@router.get("/runs/{run_id}/experiment-plans", response_model=list[ExperimentPlanRead])
def read_experiment_plans(run_id: int, session: Session = Depends(get_db_session)) -> list[ExperimentPlanRead]:
    plans = list_experiment_plans(session, run_id)
    return [
        ExperimentPlanRead(
            id=plan.id,
            run_id=plan.run_id,
            paper_id=plan.paper_id,
            title=plan.title,
            steps=json.loads(plan.steps_json),
        )
        for plan in plans
    ]


@router.get("/runs/{run_id}/experiment-tasks", response_model=list[ExperimentTaskRead])
def read_experiment_tasks(run_id: int, session: Session = Depends(get_db_session)) -> list[ExperimentTaskRead]:
    tasks = list_experiment_tasks(session, run_id)
    return [
        ExperimentTaskRead(
            id=task.id,
            run_id=task.run_id,
            plan_id=task.plan_id,
            paper_id=task.paper_id,
            title=task.title,
            task_type=task.task_type,
            status=task.status,
            config_json=task.config_json,
        )
        for task in tasks
    ]


@router.post("/runs/{run_id}/execute-tasks", response_model=list[ResearchIterationRead])
def execute_tasks(run_id: int, session: Session = Depends(get_db_session)) -> list[ResearchIterationRead]:
    try:
        execute_experiment_tasks(session, run_id=run_id, runner=DeterministicLocalTaskRunner(), max_iterations=1)
        iterations = list_iterations(session, run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [
        ResearchIterationRead(
            id=iteration.id,
            run_id=iteration.run_id,
            iteration_index=iteration.iteration_index,
            plan_title=iteration.plan_title,
            metric_name=iteration.metric_name,
            metric_value=iteration.metric_value,
            decision=iteration.decision,
            rationale=iteration.rationale,
        )
        for iteration in iterations
    ]


@router.get("/runs/{run_id}/iterations", response_model=list[ResearchIterationRead])
def read_iterations(run_id: int, session: Session = Depends(get_db_session)) -> list[ResearchIterationRead]:
    iterations = list_iterations(session, run_id)
    return [
        ResearchIterationRead(
            id=iteration.id,
            run_id=iteration.run_id,
            iteration_index=iteration.iteration_index,
            plan_title=iteration.plan_title,
            metric_name=iteration.metric_name,
            metric_value=iteration.metric_value,
            decision=iteration.decision,
            rationale=iteration.rationale,
        )
        for iteration in iterations
    ]


@router.post("/runs/{run_id}/report", response_model=ResearchReportResponse)
def generate_research_report(run_id: int, session: Session = Depends(get_db_session)) -> ResearchReportResponse:
    try:
        title, markdown = build_research_report(session, run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    run = session.get(ResearchRun, run_id)
    return ResearchReportResponse(run_id=run_id, title=title, markdown=markdown, figure_path=run.report_figure_path if run else None)


@router.get("/runs/{run_id}/report", response_model=ResearchReportResponse)
def read_research_report(run_id: int, session: Session = Depends(get_db_session)) -> ResearchReportResponse:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if not run.report_markdown or not run.report_title:
        raise HTTPException(status_code=404, detail="Report not generated")
    return ResearchReportResponse(run_id=run_id, title=run.report_title, markdown=run.report_markdown, figure_path=run.report_figure_path)


@router.post("/runs/{run_id}/paper-draft", response_model=PaperDraftResponse)
def generate_paper_draft(run_id: int, session: Session = Depends(get_db_session)) -> PaperDraftResponse:
    try:
        title, markdown = build_paper_draft(session, run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    run = session.get(ResearchRun, run_id)
    return PaperDraftResponse(run_id=run_id, title=title, markdown=markdown, figure_path=run.report_figure_path if run else None)


@router.get("/runs/{run_id}/paper-draft", response_model=PaperDraftResponse)
def read_paper_draft(run_id: int, session: Session = Depends(get_db_session)) -> PaperDraftResponse:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if not run.paper_draft_markdown or not run.paper_draft_title:
        raise HTTPException(status_code=404, detail="Paper draft not generated")
    return PaperDraftResponse(run_id=run_id, title=run.paper_draft_title, markdown=run.paper_draft_markdown, figure_path=run.report_figure_path)


@router.post("/runs/{run_id}/bundle", response_model=RunArtifactBundleResponse)
def generate_run_bundle(run_id: int, session: Session = Depends(get_db_session)) -> RunArtifactBundleResponse:
    try:
        payload = write_run_artifact_bundle(session, run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RunArtifactBundleResponse(**payload)


@router.get("/runs/{run_id}/bundle", response_model=RunArtifactBundleResponse)
def read_run_bundle(run_id: int, session: Session = Depends(get_db_session)) -> RunArtifactBundleResponse:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if not run.artifact_dir:
        raise HTTPException(status_code=404, detail="Bundle not generated")
    payload = {
        "run_id": run.id,
        "artifact_dir": run.artifact_dir,
        "report_path": str(Path(run.artifact_dir) / "report.md"),
        "paper_draft_path": str(Path(run.artifact_dir) / "paper_draft.md"),
        "figure_path": run.report_figure_path,
        "summary_path": str(Path(run.artifact_dir) / "summary.json"),
        "iterations_path": str(Path(run.artifact_dir) / "iterations.jsonl"),
        "hypotheses_path": str(Path(run.artifact_dir) / "hypotheses.json"),
        "experiment_plans_path": str(Path(run.artifact_dir) / "experiment_plans.json"),
        "experiment_tasks_path": str(Path(run.artifact_dir) / "experiment_tasks.json"),
        "experiment_results_path": str(Path(run.artifact_dir) / "experiment_results.json"),
        "events_path": str(Path(run.artifact_dir) / "events.jsonl"),
        "manifest_path": str(Path(run.artifact_dir) / "manifest.json"),
        "zip_path": str(Path(run.artifact_dir) / "bundle.zip"),
    }
    return RunArtifactBundleResponse(**payload)


@router.get("/runs/{run_id}/bundle/manifest", response_model=RunArtifactManifestResponse)
def read_run_bundle_manifest(run_id: int, session: Session = Depends(get_db_session)) -> RunArtifactManifestResponse:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if not run.artifact_dir:
        raise HTTPException(status_code=404, detail="Bundle not generated")
    manifest_path = Path(run.artifact_dir) / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail="Manifest not found")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return RunArtifactManifestResponse(**payload)


@router.get("/runs/{run_id}/bundle/download")
def download_run_bundle(run_id: int, session: Session = Depends(get_db_session)) -> FileResponse:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if not run.artifact_dir:
        raise HTTPException(status_code=404, detail="Bundle not generated")
    zip_path = Path(run.artifact_dir) / "bundle.zip"
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Bundle archive not found")
    return FileResponse(path=zip_path, filename=zip_path.name, media_type="application/zip")


@router.get("/runs/{run_id}/report/download")
def download_run_report(run_id: int, session: Session = Depends(get_db_session)) -> FileResponse:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if not run.artifact_dir:
        raise HTTPException(status_code=404, detail="Bundle not generated")
    report_path = Path(run.artifact_dir) / "report.md"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report artifact not found")
    return FileResponse(path=report_path, filename=report_path.name, media_type="text/markdown")


@router.get("/runs/{run_id}/paper-draft/download")
def download_paper_draft(run_id: int, session: Session = Depends(get_db_session)) -> FileResponse:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if not run.artifact_dir:
        raise HTTPException(status_code=404, detail="Bundle not generated")
    draft_path = Path(run.artifact_dir) / "paper_draft.md"
    if not draft_path.exists():
        raise HTTPException(status_code=404, detail="Paper draft artifact not found")
    return FileResponse(path=draft_path, filename=draft_path.name, media_type="text/markdown")


@router.get("/runs/{run_id}/figure/download")
def download_run_figure(run_id: int, session: Session = Depends(get_db_session)) -> FileResponse:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    if not run.report_figure_path:
        raise HTTPException(status_code=404, detail="Figure artifact not found")
    figure_path = Path(run.report_figure_path)
    if not figure_path.exists():
        raise HTTPException(status_code=404, detail="Figure artifact not found")
    return FileResponse(path=figure_path, filename=figure_path.name, media_type="image/svg+xml")


@router.post("/runs/{run_id}/worktree", response_model=WorktreeCreateResponse)
def create_run_worktree(
    run_id: int,
    session: Session = Depends(get_db_session),
    worktree_manager: GitWorktreeManager = Depends(get_worktree_manager),
) -> WorktreeCreateResponse:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    try:
        allocation = worktree_manager.create_worktree(run.id, run.branch_name or f"run-{run.id}")
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    run.branch_name = allocation.branch_name
    run.worktree_path = allocation.worktree_path
    session.flush()
    add_run_event(
        session,
        run.id,
        event_type="worktree.created",
        source="worktree_manager",
        message=f"Created worktree for run {run.id}.",
        payload={"branch_name": allocation.branch_name, "worktree_path": allocation.worktree_path},
    )
    return WorktreeCreateResponse(
        run_id=allocation.run_id,
        branch_name=allocation.branch_name,
        worktree_path=allocation.worktree_path,
        repo_root=allocation.repo_root,
    )


@router.get("/runs/{run_id}/execution-manifest", response_model=WorktreeExecutionManifestResponse)
def execution_manifest(run_id: int, session: Session = Depends(get_db_session)) -> WorktreeExecutionManifestResponse:
    try:
        manifest = build_execution_manifest(session, run_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return WorktreeExecutionManifestResponse(**manifest)
