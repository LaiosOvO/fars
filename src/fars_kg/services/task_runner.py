from __future__ import annotations

from dataclasses import dataclass
import json
from itertools import cycle, islice

from sqlalchemy.orm import Session

from fars_kg.models import ExperimentTask, ResearchIteration, ResearchRun
from fars_kg.services.repository import (
    BENCHMARK_REGISTRY,
    KEEP_THRESHOLDS,
    add_experiment_result,
    add_run_event,
    get_paper,
    list_experiment_tasks,
)


@dataclass
class TaskExecutionRecord:
    task_id: int
    iteration_id: int
    metric_name: str | None
    metric_value: str | None
    decision: str


class DeterministicLocalTaskRunner:
    def execute(self, session: Session, task: ExperimentTask, *, iteration_index: int) -> TaskExecutionRecord:
        paper = get_paper(session, task.paper_id)
        if paper is None:
            raise ValueError(f"Unknown paper: {task.paper_id}")

        config = json.loads(task.config_json)
        method = config.get("method")
        dataset = config.get("dataset")
        metric = config.get("metric")
        task_type = config.get("task_type", task.task_type)
        value, decision, rationale, source = self._run_task(task_type, method, dataset, metric)
        if value is not None:
            add_experiment_result(
                session,
                run_id=task.run_id,
                paper_id=paper.id,
                method_name=method,
                dataset_name=dataset,
                metric_name=metric,
                value=value,
                notes=f"deterministic {task_type} task runner result",
                source=source,
            )

        task.status = "completed"
        iteration = ResearchIteration(
            run_id=task.run_id,
            iteration_index=iteration_index,
            plan_title=task.title,
            metric_name=metric,
            metric_value=value,
            decision=decision,
            rationale=rationale,
        )
        session.add(iteration)
        session.flush()
        return TaskExecutionRecord(
            task_id=task.id,
            iteration_id=iteration.id,
            metric_name=metric,
            metric_value=value,
            decision=decision,
        )

    def _run_task(
        self,
        task_type: str,
        method: str | None,
        dataset: str | None,
        metric: str | None,
    ) -> tuple[str | None, str, str, str]:
        if not (method and dataset and metric):
            return None, "discard", "Missing method/dataset/metric configuration.", f"executor_{task_type}"

        base_value = BENCHMARK_REGISTRY.get((method, dataset, metric))
        if base_value is None:
            return None, "discard", "No deterministic benchmark mapping available.", f"executor_{task_type}"

        numeric_value = float(base_value)
        threshold = KEEP_THRESHOLDS.get(metric, 0.0)

        if task_type == "benchmark":
            final_value = numeric_value
            decision = "keep" if final_value >= threshold else "discard"
            rationale = f"{metric}={final_value} benchmark {'meets' if decision == 'keep' else 'misses'} threshold {threshold}."
            return str(final_value), decision, rationale, "executor_benchmark"

        if task_type == "ablation":
            penalty = 1.0 if metric in {"BLEU", "Accuracy"} else 0.05
            final_value = max(0.0, numeric_value - penalty)
            decision = "keep" if final_value >= threshold else "discard"
            rationale = f"{metric}={final_value} after ablation {'meets' if decision == 'keep' else 'misses'} threshold {threshold}."
            return str(final_value), decision, rationale, "executor_ablation"

        if task_type == "comparison":
            bonus = 0.2 if metric in {"BLEU", "Accuracy"} else 0.01
            final_value = numeric_value + bonus
            decision = "keep" if final_value >= threshold else "discard"
            rationale = f"{metric}={final_value} comparison run {'meets' if decision == 'keep' else 'misses'} threshold {threshold}."
            return str(final_value), decision, rationale, "executor_comparison"

        return str(numeric_value), "discard", f"Unknown task type '{task_type}', defaulting to discard.", f"executor_{task_type}"


def execute_experiment_tasks(
    session: Session,
    *,
    run_id: int,
    runner: DeterministicLocalTaskRunner,
    max_iterations: int,
) -> list[TaskExecutionRecord]:
    run = session.get(ResearchRun, run_id)
    if run is None:
        raise ValueError(f"Unknown run: {run_id}")

    tasks = list_experiment_tasks(session, run_id)
    if not tasks:
        return []

    start_index = len(run.iterations) + 1
    selected_tasks = list(islice(cycle(tasks), max_iterations))
    records: list[TaskExecutionRecord] = []
    for offset, task in enumerate(selected_tasks, start=0):
        record = runner.execute(session, task, iteration_index=start_index + offset)
        records.append(record)
    if records:
        add_run_event(
            session,
            run.id,
            event_type="experiment_tasks.executed",
            source="task_runner",
            message=f"Executed {len(records)} experiment tasks.",
            payload={
                "count": len(records),
                "iteration_range": [start_index, start_index + len(records) - 1],
                "decisions": [record.decision for record in records],
            },
        )
    return records
