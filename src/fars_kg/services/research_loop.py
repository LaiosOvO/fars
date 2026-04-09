from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import uuid
import zipfile

from sqlalchemy.orm import Session

from fars_kg.db import DatabaseManager
from fars_kg.models import Paper
from fars_kg.parsers.base import ParserProtocol
from fars_kg.services.ingestion import TopicIngestionService
from fars_kg.services.parsing import ParsingService
from fars_kg.services.repository import (
    add_run_event,
    auto_add_experiment_results,
    auto_attach_semantic_enrichment,
    auto_generate_experiment_plans,
    auto_generate_experiment_tasks,
    auto_generate_hypotheses,
    build_paper_draft,
    build_research_report,
    build_topic_landscape,
    create_evidence_snapshot,
    create_research_run,
    get_run,
    get_paper,
    infer_semantic_edges,
    list_experiment_tasks,
    list_run_results,
    write_run_artifact_bundle,
    update_research_run_result,
)
from fars_kg.services.task_runner import DeterministicLocalTaskRunner, execute_experiment_tasks
from fars_kg.worktree import GitWorktreeManager


@dataclass
class AutonomousResearchLoopResult:
    topic: str
    requested_iterations: int
    paper_ids: list[int]
    version_ids: list[int]
    parsed_versions: int
    enriched_papers: int
    inferred_edges: int
    result_count: int
    executed_result_count: int
    hypothesis_count: int
    experiment_plan_count: int
    experiment_task_count: int
    iteration_count: int
    snapshot_id: int
    run_id: int
    lead_paper_id: int
    lead_paper_title: str
    used_worktree: bool
    worktree_path: str | None
    artifact_dir: str | None
    summary: str


@dataclass
class BatchLoopItemResult:
    topic: str
    status: str
    run_id: int | None
    lead_paper_id: int | None
    lead_paper_title: str | None
    artifact_dir: str | None
    summary: str | None
    result_count: int
    error: str | None = None


@dataclass
class BatchLoopReconciliation:
    successful_run_count: int
    failed_run_count: int
    total_result_count: int
    best_metrics: list[dict]


@dataclass
class BatchArtifactBundle:
    batch_id: str
    kind: str
    artifact_dir: str
    summary_path: str
    items_path: str
    reconciliation_path: str
    manifest_path: str
    zip_path: str


@dataclass
class BatchAutonomousResearchLoopResult:
    requested_topics: list[str]
    requested_iterations: int
    requested_concurrency: int
    completed_count: int
    failed_count: int
    items: list[BatchLoopItemResult]
    reconciliation: BatchLoopReconciliation
    artifact: BatchArtifactBundle


@dataclass
class RunReconciliationResult:
    requested_run_ids: list[int]
    missing_run_ids: list[int]
    found_count: int
    items: list[BatchLoopItemResult]
    reconciliation: BatchLoopReconciliation
    artifact: BatchArtifactBundle


class AutonomousResearchLoopService:
    def __init__(
        self,
        *,
        openalex_client,
        parser: ParserProtocol,
        worktree_manager: GitWorktreeManager | None = None,
    ) -> None:
        self.openalex_client = openalex_client
        self.parser = parser
        self.worktree_manager = worktree_manager

    def run(
        self,
        session: Session,
        *,
        topic: str,
        limit: int = 5,
        iterations: int = 1,
        branch_name: str | None = None,
        use_worktree: bool = False,
    ) -> AutonomousResearchLoopResult:
        ingestion = TopicIngestionService(self.openalex_client).ingest_topic(session=session, topic=topic, limit=limit)

        parsed_versions = 0
        for version_id in ingestion.version_ids:
            ParsingService(self.parser).parse_version(session=session, version_id=version_id)
            parsed_versions += 1

        enriched_papers = 0
        inferred_edges = 0
        result_count = 0
        executed_result_count = 0
        hypothesis_count = 0
        experiment_plan_count = 0
        experiment_task_count = 0
        iteration_count = 0
        for paper_id in ingestion.paper_ids:
            auto_attach_semantic_enrichment(session, paper_id)
            enriched_papers += 1
            edge_result = infer_semantic_edges(session, paper_id)
            inferred_edges += edge_result.edges_created

        landscape = build_topic_landscape(session, topic, limit=limit)
        lead_paper = self._select_lead_paper(session, ingestion.paper_ids, landscape)
        snapshot = create_evidence_snapshot(session, lead_paper.id, topic=topic)
        run = create_research_run(session, snapshot_id=snapshot.id, branch_name=branch_name or f"loop-{lead_paper.id}")
        add_run_event(
            session,
            run.id,
            event_type="research_loop.started",
            source="autonomous_loop",
            message=f"Autonomous research loop started for topic '{topic}'.",
            payload={"topic": topic, "limit": limit, "iterations": iterations, "use_worktree": use_worktree},
        )

        worktree_path: str | None = None
        if use_worktree and self.worktree_manager is not None:
            allocation = self.worktree_manager.create_worktree(run.id, run.branch_name or f"run-{run.id}")
            run.branch_name = allocation.branch_name
            run.worktree_path = allocation.worktree_path
            worktree_path = allocation.worktree_path

        for paper_id in ingestion.paper_ids:
            hypothesis_count += len(auto_generate_hypotheses(session, run_id=run.id, paper_id=paper_id))
            experiment_plan_count += len(auto_generate_experiment_plans(session, run_id=run.id, paper_id=paper_id))
        experiment_task_count = len(auto_generate_experiment_tasks(session, run_id=run.id))
        if experiment_task_count == 0:
            experiment_task_count = len(list_experiment_tasks(session, run.id))

        iteration_count = len(
            execute_experiment_tasks(
                session,
                run_id=run.id,
                runner=DeterministicLocalTaskRunner(),
                max_iterations=iterations,
            )
        )
        executed_result_count = len(list_run_results(session, run.id))

        for paper_id in ingestion.paper_ids:
            results = auto_add_experiment_results(session, run_id=run.id, paper_id=paper_id)
            result_count += len(results)

        summary = (
            f"Autonomous loop completed for topic '{topic}' with {len(ingestion.paper_ids)} papers, "
            f"{parsed_versions} parsed versions, {enriched_papers} enriched papers, "
            f"{inferred_edges} inferred semantic edges, {hypothesis_count} hypotheses, "
            f"{experiment_plan_count} experiment plans, {experiment_task_count} experiment tasks, "
            f"{iteration_count} executed iterations, "
            f"{executed_result_count} executed benchmark results, and {result_count} extracted experiment results."
        )
        update_research_run_result(
            session,
            run.id,
            status="completed",
            result_summary=summary,
            result_payload_json=json.dumps(
                {
                    "topic": topic,
                    "paper_ids": ingestion.paper_ids,
                    "version_ids": ingestion.version_ids,
                    "parsed_versions": parsed_versions,
                    "enriched_papers": enriched_papers,
                    "inferred_edges": inferred_edges,
                    "hypothesis_count": hypothesis_count,
                    "experiment_plan_count": experiment_plan_count,
                    "experiment_task_count": experiment_task_count,
                    "iteration_count": iteration_count,
                    "executed_result_count": executed_result_count,
                    "result_count": result_count,
                    "snapshot_id": snapshot.id,
                    "lead_paper_id": lead_paper.id,
                },
                sort_keys=True,
            ),
        )
        build_research_report(session, run.id)
        build_paper_draft(session, run.id)
        add_run_event(
            session,
            run.id,
            event_type="research_loop.completed",
            source="autonomous_loop",
            message=f"Autonomous research loop completed for topic '{topic}'.",
            payload={"topic": topic, "run_id": run.id},
        )
        bundle = write_run_artifact_bundle(session, run.id)

        return AutonomousResearchLoopResult(
            topic=topic,
            requested_iterations=iterations,
            paper_ids=ingestion.paper_ids,
            version_ids=ingestion.version_ids,
            parsed_versions=parsed_versions,
            enriched_papers=enriched_papers,
            inferred_edges=inferred_edges,
            result_count=result_count,
            executed_result_count=executed_result_count,
            hypothesis_count=hypothesis_count,
            experiment_plan_count=experiment_plan_count,
            experiment_task_count=experiment_task_count,
            iteration_count=iteration_count,
            snapshot_id=snapshot.id,
            run_id=run.id,
            lead_paper_id=lead_paper.id,
            lead_paper_title=lead_paper.canonical_title,
            used_worktree=use_worktree,
            worktree_path=worktree_path,
            artifact_dir=bundle["artifact_dir"],
            summary=summary,
        )

    def continue_run(self, session: Session, *, run_id: int, iterations: int) -> AutonomousResearchLoopResult:
        from fars_kg.services.repository import (
            build_paper_draft,
            build_research_report,
            get_run,
            list_hypotheses,
            list_experiment_plans,
            list_experiment_tasks,
            list_run_results,
            list_iterations,
            write_run_artifact_bundle,
        )

        run = get_run(session, run_id)
        if run is None:
            raise ValueError(f"Unknown run: {run_id}")
        snapshot = run.snapshot
        if snapshot is None:
            raise ValueError(f"Run {run_id} has no snapshot")
        lead_paper = get_paper(session, snapshot.paper_id)
        if lead_paper is None:
            raise ValueError(f"Run {run_id} lead paper not found")

        iteration_count_before = len(run.iterations)
        execute_experiment_tasks(
            session,
            run_id=run.id,
            runner=DeterministicLocalTaskRunner(),
            max_iterations=iterations,
        )
        iteration_count_after = len(list_iterations(session, run.id))
        executed_result_count = len(list_run_results(session, run.id))

        hypotheses = list_hypotheses(session, run.id)
        plans = list_experiment_plans(session, run.id)
        tasks = list_experiment_tasks(session, run.id)
        results = list_run_results(session, run.id)

        summary = (
            f"Autonomous loop continued for topic '{snapshot.topic or lead_paper.canonical_title}' with "
            f"{iteration_count_after - iteration_count_before} new iterations; total iterations={iteration_count_after}, "
            f"executed benchmark results={executed_result_count}, extracted experiment results={len(results)}."
        )
        add_run_event(
            session,
            run.id,
            event_type="research_loop.continued",
            source="autonomous_loop",
            message=f"Autonomous research loop continued with {iteration_count_after - iteration_count_before} new iterations.",
            payload={"new_iterations": iteration_count_after - iteration_count_before, "total_iterations": iteration_count_after},
        )
        update_research_run_result(
            session,
            run.id,
            status="completed",
            result_summary=summary,
            result_payload_json=json.dumps(
                {
                    "topic": snapshot.topic,
                    "paper_ids": [version.paper_id for version in lead_paper.versions] or [lead_paper.id],
                    "parsed_versions": len(lead_paper.versions),
                    "hypothesis_count": len(hypotheses),
                    "experiment_plan_count": len(plans),
                    "experiment_task_count": len(tasks),
                    "iteration_count": iteration_count_after,
                    "executed_result_count": executed_result_count,
                    "result_count": len(results),
                    "snapshot_id": snapshot.id,
                    "lead_paper_id": lead_paper.id,
                },
                sort_keys=True,
            ),
        )
        build_research_report(session, run.id)
        build_paper_draft(session, run.id)
        bundle = write_run_artifact_bundle(session, run.id)

        return AutonomousResearchLoopResult(
            topic=snapshot.topic or lead_paper.canonical_title,
            requested_iterations=iterations,
            paper_ids=[lead_paper.id],
            version_ids=[version.id for version in lead_paper.versions],
            parsed_versions=len(lead_paper.versions),
            enriched_papers=1,
            inferred_edges=len(lead_paper.outgoing_edges),
            result_count=len(results),
            executed_result_count=executed_result_count,
            hypothesis_count=len(hypotheses),
            experiment_plan_count=len(plans),
            experiment_task_count=len(tasks),
            iteration_count=iteration_count_after,
            snapshot_id=snapshot.id,
            run_id=run.id,
            lead_paper_id=lead_paper.id,
            lead_paper_title=lead_paper.canonical_title,
            used_worktree=bool(run.worktree_path),
            worktree_path=run.worktree_path,
            artifact_dir=bundle["artifact_dir"],
            summary=summary,
        )

    def run_batch(
        self,
        db_manager: DatabaseManager,
        *,
        topics: list[str],
        limit: int = 5,
        iterations: int = 1,
        use_worktree: bool = False,
        max_concurrency: int = 1,
        branch_prefix: str | None = None,
    ) -> BatchAutonomousResearchLoopResult:
        normalized_topics = self._normalize_topics(topics)
        if not normalized_topics:
            raise ValueError("At least one non-empty topic is required")

        requested_concurrency = max(1, min(max_concurrency, len(normalized_topics)))
        if use_worktree and requested_concurrency > 1:
            requested_concurrency = 1
        items_by_index: list[BatchLoopItemResult | None] = [None] * len(normalized_topics)

        if requested_concurrency == 1:
            for index, topic in enumerate(normalized_topics):
                items_by_index[index] = self._run_single_batch_topic(
                    db_manager,
                    index=index,
                    topic=topic,
                    limit=limit,
                    iterations=iterations,
                    use_worktree=use_worktree,
                    branch_prefix=branch_prefix,
                )
        else:
            with ThreadPoolExecutor(max_workers=requested_concurrency) as executor:
                future_to_index = {
                    executor.submit(
                        self._run_single_batch_topic,
                        db_manager,
                        index=index,
                        topic=topic,
                        limit=limit,
                        iterations=iterations,
                        use_worktree=use_worktree,
                        branch_prefix=branch_prefix,
                    ): index
                    for index, topic in enumerate(normalized_topics)
                }
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        items_by_index[index] = future.result()
                    except Exception as exc:  # pragma: no cover - safety fallback
                        topic = normalized_topics[index]
                        items_by_index[index] = BatchLoopItemResult(
                            topic=topic,
                            status="failed",
                            run_id=None,
                            lead_paper_id=None,
                            lead_paper_title=None,
                            artifact_dir=None,
                            summary=None,
                            result_count=0,
                            error=f"{type(exc).__name__}: {exc}",
                        )
            for index, item in enumerate(items_by_index):
                if item is None or not self._should_retry_batch_item(item):
                    continue
                retried = self._run_single_batch_topic(
                    db_manager,
                    index=index,
                    topic=normalized_topics[index],
                    limit=limit,
                    iterations=iterations,
                    use_worktree=use_worktree,
                    branch_prefix=branch_prefix,
                )
                items_by_index[index] = retried

        items = [item for item in items_by_index if item is not None]
        completed_count = sum(1 for item in items if item.status == "completed")
        failed_count = len(items) - completed_count
        reconciliation = self._build_batch_reconciliation(db_manager, items)
        artifact = self._write_batch_artifact_bundle(
            kind="batch-run",
            payload={
                "requested_topics": normalized_topics,
                "requested_iterations": iterations,
                "requested_concurrency": requested_concurrency,
                "completed_count": completed_count,
                "failed_count": failed_count,
                "items": [asdict(item) for item in items],
                "reconciliation": asdict(reconciliation),
            },
        )

        return BatchAutonomousResearchLoopResult(
            requested_topics=normalized_topics,
            requested_iterations=iterations,
            requested_concurrency=requested_concurrency,
            completed_count=completed_count,
            failed_count=failed_count,
            items=items,
            reconciliation=reconciliation,
            artifact=artifact,
        )

    def _run_single_batch_topic(
        self,
        db_manager: DatabaseManager,
        *,
        index: int,
        topic: str,
        limit: int,
        iterations: int,
        use_worktree: bool,
        branch_prefix: str | None,
    ) -> BatchLoopItemResult:
        branch_name = self._build_batch_branch_name(index=index, topic=topic, branch_prefix=branch_prefix)
        try:
            with db_manager.session() as session:
                result = self.run(
                    session,
                    topic=topic,
                    limit=limit,
                    iterations=iterations,
                    branch_name=branch_name,
                    use_worktree=use_worktree,
                )
            return BatchLoopItemResult(
                topic=topic,
                status="completed",
                run_id=result.run_id,
                lead_paper_id=result.lead_paper_id,
                lead_paper_title=result.lead_paper_title,
                artifact_dir=result.artifact_dir,
                summary=result.summary,
                result_count=result.result_count + result.executed_result_count,
                error=None,
            )
        except Exception as exc:
            return BatchLoopItemResult(
                topic=topic,
                status="failed",
                run_id=None,
                lead_paper_id=None,
                lead_paper_title=None,
                artifact_dir=None,
                summary=None,
                result_count=0,
                error=f"{type(exc).__name__}: {exc}",
            )

    def _build_batch_reconciliation(
        self,
        db_manager: DatabaseManager,
        items: list[BatchLoopItemResult],
    ) -> BatchLoopReconciliation:
        successful_items = [item for item in items if item.status == "completed" and item.run_id is not None]
        best_metrics: dict[str, dict] = {}
        total_result_count = 0
        if successful_items:
            with db_manager.session() as session:
                for item in successful_items:
                    run_results = list_run_results(session, item.run_id)  # type: ignore[arg-type]
                    total_result_count += len(run_results)
                    for result in run_results:
                        if result.metric is None:
                            continue
                        metric_name = result.metric.name
                        numeric_value = self._parse_float(result.value)
                        if numeric_value is None:
                            continue
                        current = best_metrics.get(metric_name)
                        if current is None or numeric_value > current["value"]:
                            best_metrics[metric_name] = {
                                "metric_name": metric_name,
                                "run_id": item.run_id,
                                "topic": item.topic,
                                "value": numeric_value,
                                "value_raw": result.value,
                            }
        return BatchLoopReconciliation(
            successful_run_count=len(successful_items),
            failed_run_count=len(items) - len(successful_items),
            total_result_count=total_result_count,
            best_metrics=sorted(best_metrics.values(), key=lambda item: item["metric_name"]),
        )

    @staticmethod
    def _should_retry_batch_item(item: BatchLoopItemResult) -> bool:
        if item.status != "failed":
            return False
        if not item.error:
            return False
        lowered = item.error.lower()
        return (
            "database is locked" in lowered
            or "operationalerror" in lowered
            or "timeout" in lowered
        )

    def reconcile_runs(self, db_manager: DatabaseManager, *, run_ids: list[int]) -> RunReconciliationResult:
        requested_run_ids = self._normalize_run_ids(run_ids)
        if not requested_run_ids:
            raise ValueError("At least one run_id is required")

        items: list[BatchLoopItemResult] = []
        missing_run_ids: list[int] = []
        with db_manager.session() as session:
            for run_id in requested_run_ids:
                run = get_run(session, run_id)
                if run is None:
                    missing_run_ids.append(run_id)
                    continue

                snapshot = run.snapshot
                lead_paper = get_paper(session, snapshot.paper_id) if snapshot is not None else None
                topic = snapshot.topic if snapshot and snapshot.topic else (lead_paper.canonical_title if lead_paper else f"run-{run.id}")
                items.append(
                    BatchLoopItemResult(
                        topic=topic,
                        status=run.status,
                        run_id=run.id,
                        lead_paper_id=lead_paper.id if lead_paper else None,
                        lead_paper_title=lead_paper.canonical_title if lead_paper else None,
                        artifact_dir=run.artifact_dir,
                        summary=run.result_summary,
                        result_count=len(list_run_results(session, run.id)),
                        error=None if run.status == "completed" else run.result_summary,
                    )
                )

        reconciliation = self._build_batch_reconciliation(db_manager, items)
        artifact = self._write_batch_artifact_bundle(
            kind="reconcile",
            payload={
                "requested_run_ids": requested_run_ids,
                "missing_run_ids": missing_run_ids,
                "found_count": len(items),
                "items": [asdict(item) for item in items],
                "reconciliation": asdict(reconciliation),
            },
        )
        return RunReconciliationResult(
            requested_run_ids=requested_run_ids,
            missing_run_ids=missing_run_ids,
            found_count=len(items),
            items=items,
            reconciliation=reconciliation,
            artifact=artifact,
        )

    def read_batch_manifest(self, batch_id: str) -> dict:
        index = self._read_batch_index()
        record = index.get(batch_id)
        if record is None:
            raise ValueError(f"Unknown batch artifact: {batch_id}")
        manifest_path = Path(record["manifest_path"])
        if not manifest_path.exists():
            raise ValueError(f"Batch manifest not found: {manifest_path}")
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        return payload

    def get_batch_zip_path(self, batch_id: str) -> Path:
        manifest = self.read_batch_manifest(batch_id)
        zip_info = manifest.get("files", {}).get("zip_path")
        zip_path = Path(zip_info.get("path", "")) if isinstance(zip_info, dict) else Path("")
        if not zip_path.exists():
            raise ValueError("Batch bundle archive not found")
        return zip_path

    def get_batch_summary_path(self, batch_id: str) -> Path:
        manifest = self.read_batch_manifest(batch_id)
        summary_info = manifest.get("files", {}).get("summary_path")
        summary_path = Path(summary_info.get("path", "")) if isinstance(summary_info, dict) else Path("")
        if not summary_path.exists():
            raise ValueError("Batch summary artifact not found")
        return summary_path

    def get_batch_items_path(self, batch_id: str) -> Path:
        manifest = self.read_batch_manifest(batch_id)
        items_info = manifest.get("files", {}).get("items_path")
        items_path = Path(items_info.get("path", "")) if isinstance(items_info, dict) else Path("")
        if not items_path.exists():
            raise ValueError("Batch items artifact not found")
        return items_path

    def get_batch_reconciliation_path(self, batch_id: str) -> Path:
        manifest = self.read_batch_manifest(batch_id)
        reconciliation_info = manifest.get("files", {}).get("reconciliation_path")
        reconciliation_path = Path(reconciliation_info.get("path", "")) if isinstance(reconciliation_info, dict) else Path("")
        if not reconciliation_path.exists():
            raise ValueError("Batch reconciliation artifact not found")
        return reconciliation_path

    def list_batch_artifacts(self, *, limit: int = 20, kind: str | None = None) -> list[dict]:
        index = self._read_batch_index()
        rows: list[dict] = []
        for batch_id, record in index.items():
            record_kind = str(record.get("kind", ""))
            if kind is not None and record_kind != kind:
                continue
            artifact_dir = str(record.get("artifact_dir", ""))
            manifest_path = str(record.get("manifest_path", ""))
            created_at = record.get("created_at")
            rows.append(
                {
                    "batch_id": batch_id,
                    "kind": record_kind,
                    "artifact_dir": artifact_dir,
                    "manifest_path": manifest_path,
                    "created_at": str(created_at) if created_at else None,
                    "exists": Path(manifest_path).exists() if manifest_path else False,
                }
            )

        rows.sort(key=lambda item: item["created_at"] or "", reverse=True)
        return rows[: max(1, limit)]

    @staticmethod
    def _parse_float(value: str | None) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def _write_batch_artifact_bundle(self, *, kind: str, payload: dict) -> BatchArtifactBundle:
        batch_id = uuid.uuid4().hex[:12]
        artifacts_root = Path(os.getenv("FARS_ARTIFACTS_ROOT", ".artifacts"))
        artifact_dir = artifacts_root / "batches" / f"{kind}-{batch_id}"
        artifact_dir.mkdir(parents=True, exist_ok=True)

        summary_path = artifact_dir / "summary.json"
        items_path = artifact_dir / "items.json"
        reconciliation_path = artifact_dir / "reconciliation.json"
        manifest_path = artifact_dir / "manifest.json"
        zip_path = artifact_dir / "bundle.zip"

        summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        items_path.write_text(json.dumps(payload.get("items", []), indent=2, ensure_ascii=False), encoding="utf-8")
        reconciliation_path.write_text(
            json.dumps(payload.get("reconciliation", {}), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in (summary_path, items_path, reconciliation_path):
                if path.exists():
                    archive.write(path, arcname=path.name)

        manifest_payload = {
            "batch_id": batch_id,
            "kind": kind,
            "artifact_dir": str(artifact_dir),
            "files": {
                "summary_path": self._artifact_file_descriptor(summary_path),
                "items_path": self._artifact_file_descriptor(items_path),
                "reconciliation_path": self._artifact_file_descriptor(reconciliation_path),
                "zip_path": self._artifact_file_descriptor(zip_path),
            },
        }
        manifest_path.write_text(json.dumps(manifest_payload, indent=2, ensure_ascii=False), encoding="utf-8")
        with zipfile.ZipFile(zip_path, "a", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(manifest_path, arcname=manifest_path.name)

        index = self._read_batch_index()
        index[batch_id] = {
            "kind": kind,
            "artifact_dir": str(artifact_dir),
            "manifest_path": str(manifest_path),
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._write_batch_index(index)

        return BatchArtifactBundle(
            batch_id=batch_id,
            kind=kind,
            artifact_dir=str(artifact_dir),
            summary_path=str(summary_path),
            items_path=str(items_path),
            reconciliation_path=str(reconciliation_path),
            manifest_path=str(manifest_path),
            zip_path=str(zip_path),
        )

    @staticmethod
    def _select_lead_paper(session: Session, paper_ids: list[int], landscape: dict) -> Paper:
        if landscape["papers"]:
            lead_id = landscape["papers"][0]["id"]
            lead = get_paper(session, lead_id)
            if lead is not None:
                return lead
        fallback = get_paper(session, paper_ids[0])
        if fallback is None:
            raise ValueError("Unable to select lead paper for research loop")
        return fallback

    @staticmethod
    def _normalize_topics(topics: list[str]) -> list[str]:
        seen: set[str] = set()
        normalized: list[str] = []
        for topic in topics:
            item = topic.strip()
            if not item:
                continue
            dedupe_key = item.lower()
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            normalized.append(item)
        return normalized

    @staticmethod
    def _normalize_run_ids(run_ids: list[int]) -> list[int]:
        seen: set[int] = set()
        normalized: list[int] = []
        for run_id in run_ids:
            if run_id <= 0:
                continue
            if run_id in seen:
                continue
            seen.add(run_id)
            normalized.append(run_id)
        return normalized

    @staticmethod
    def _build_batch_branch_name(*, index: int, topic: str, branch_prefix: str | None) -> str:
        raw_prefix = (branch_prefix or "batch").strip().lower()
        prefix = re.sub(r"[^a-z0-9]+", "-", raw_prefix).strip("-")
        prefix = prefix[:24] if prefix else "batch"
        slug = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
        slug = slug[:32] if slug else "topic"
        return f"{prefix}-{index + 1:02d}-{slug}"

    @staticmethod
    def _batch_index_path() -> Path:
        root = Path(os.getenv("FARS_ARTIFACTS_ROOT", ".artifacts"))
        return root / "batches" / "index.json"

    def _read_batch_index(self) -> dict[str, dict]:
        path = self._batch_index_path()
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return {}
        return {str(key): value for key, value in payload.items() if isinstance(value, dict)}

    def _write_batch_index(self, index_payload: dict[str, dict]) -> None:
        path = self._batch_index_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(index_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def _artifact_file_descriptor(path: Path | None) -> dict:
        if path is None:
            return {"path": "", "exists": False, "size_bytes": None, "sha256": None}
        if not path.exists():
            return {"path": str(path), "exists": False, "size_bytes": None, "sha256": None}
        return {
            "path": str(path),
            "exists": True,
            "size_bytes": path.stat().st_size,
            "sha256": AutonomousResearchLoopService._file_sha256(path),
        }

    @staticmethod
    def _file_sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest()
