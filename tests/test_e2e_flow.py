from pathlib import Path

from fastapi.testclient import TestClient

from fars_kg.api.app import create_app
from fars_kg.config import Settings
from fars_kg.connectors.openalex import OpenAlexWork
from fars_kg.parsers.base import ParseResult, ParsedCitation, ParsedSection


class FakeOpenAlexClient:
    def search_topic(self, topic: str, limit: int = 10) -> list[OpenAlexWork]:
        return [
            OpenAlexWork(
                openalex_id="https://openalex.org/W1",
                title="Source Paper",
                doi="10.1000/source",
                publication_year=2024,
                venue="TestConf",
                abstract="Source abstract",
                source_url="https://example.com/source",
                pdf_url="https://example.com/source.pdf",
                citation_count=5,
            ),
            OpenAlexWork(
                openalex_id="https://openalex.org/W2",
                title="Target Paper",
                doi="10.1000/target",
                publication_year=2023,
                venue="TestConf",
                abstract="Target abstract",
                source_url="https://example.com/target",
                pdf_url="https://example.com/target.pdf",
                citation_count=7,
            ),
        ][:limit]


class FakeParser:
    provider_name = "fake"

    def parse_version(self, version: object) -> ParseResult:
        return ParseResult(
            sections=[
                ParsedSection(
                    section_type="body",
                    heading="Introduction",
                    paragraphs=[
                        "First paragraph.",
                        "Transformer achieves 28.4 BLEU on WMT14.",
                        "We compare against Target Paper.",
                    ],
                )
            ],
            citations=[
                ParsedCitation(
                    raw_reference="Target Paper citation",
                    target_openalex_id="https://openalex.org/W2",
                    resolution_confidence=0.9,
                    contexts=["We compare against Target Paper."],
                )
            ],
        )


def build_client(tmp_path: Path) -> TestClient:
    settings = Settings(database_url=f"sqlite+pysqlite:///{tmp_path / 'flow.db'}")
    app = create_app(settings=settings, openalex_client=FakeOpenAlexClient(), default_parser=FakeParser())
    return TestClient(app)


def test_local_end_to_end_flow_without_worktree(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    ingest = client.post("/api/topics/ingest", json={"topic": "transformers", "limit": 2})
    assert ingest.status_code == 200
    ingest_payload = ingest.json()
    source_paper_id = ingest_payload["paper_ids"][0]
    source_version_id = ingest_payload["version_ids"][0]

    parse = client.post(f"/api/paper-versions/{source_version_id}/parse")
    assert parse.status_code == 200
    assert parse.json()["edges_created"] == 1

    enrich = client.post(f"/api/papers/{source_paper_id}/semantic-enrichment/auto")
    assert enrich.status_code == 200

    infer = client.post(f"/api/graph/papers/{source_paper_id}/infer-semantic-edges")
    assert infer.status_code == 200
    assert infer.json()["edges_created"] >= 1

    evidence = client.get(f"/api/papers/{source_paper_id}/evidence-pack")
    assert evidence.status_code == 200
    evidence_payload = evidence.json()
    assert evidence_payload["methods"][0]["name"] == "Transformer"
    assert any(item["edge_type"] == "compares" for item in evidence_payload["neighbors"])

    landscape = client.get("/api/topics/landscape", params={"q": "paper"})
    assert landscape.status_code == 200
    landscape_payload = landscape.json()
    assert "Transformer" in landscape_payload["methods"]
    assert "BLEU" in landscape_payload["metrics"]
    assert landscape_payload["result_count"] == 0

    snapshot = client.post(f"/api/papers/{source_paper_id}/snapshots", json={"topic": "transformers"})
    assert snapshot.status_code == 200
    snapshot_payload = snapshot.json()

    run = client.post("/api/runs", json={"snapshot_id": snapshot_payload["id"], "branch_name": "demo-run"})
    assert run.status_code == 200
    run_payload = run.json()
    assert run_payload["status"] == "created"

    result = client.post(
        f"/api/runs/{run_payload['id']}/result",
        json={
            "status": "completed",
            "result_summary": "Completed without worktree",
            "result_payload_json": "{\"status\": \"ok\"}",
        },
    )
    assert result.status_code == 200
    result_payload = result.json()
    assert result_payload["status"] == "completed"
    assert result_payload["result_summary"] == "Completed without worktree"

    experiment = client.post(
        f"/api/runs/{run_payload['id']}/experiment-results/auto",
        json={"paper_id": source_paper_id},
    )
    assert experiment.status_code == 200

    results = client.get(f"/api/papers/{source_paper_id}/results")
    assert results.status_code == 200
    assert len(results.json()) == 1

    detail = client.get(f"/api/papers/{source_paper_id}")
    assert detail.status_code == 200
    assert detail.json()["result_stats"]["result_count"] == 1

    evidence = client.get(f"/api/papers/{source_paper_id}/evidence-pack")
    assert evidence.status_code == 200
    assert evidence.json()["result_stats"]["result_count"] == 1

    landscape = client.get("/api/topics/landscape", params={"q": "paper"})
    assert landscape.status_code == 200
    updated_landscape = landscape.json()
    assert updated_landscape["result_count"] == 1
    assert updated_landscape["papers_with_results"] == 1


def test_api_autonomous_loop_without_worktree(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    response = client.post(
        "/api/research-loops/run",
        json={"topic": "transformers", "limit": 2, "iterations": 3, "use_worktree": False},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["requested_iterations"] == 3
    assert payload["used_worktree"] is False
    assert payload["result_count"] >= 1
    assert payload["executed_result_count"] >= 1
    assert payload["hypothesis_count"] >= 1
    assert payload["experiment_plan_count"] >= 1
    assert payload["experiment_task_count"] >= 3
    assert payload["iteration_count"] == 3

    report = client.get(f"/api/runs/{payload['run_id']}/report")
    assert report.status_code == 200
    report_payload = report.json()
    assert "Autonomous Research Report" in report_payload["title"]
    assert report_payload["figure_path"].endswith(".svg")
    assert Path(report_payload["figure_path"]).exists()

    draft = client.get(f"/api/runs/{payload['run_id']}/paper-draft")
    assert draft.status_code == 200
    draft_payload = draft.json()
    assert "## Abstract" in draft_payload["markdown"]
    assert "## Results" in draft_payload["markdown"]

    bundle = client.get(f"/api/runs/{payload['run_id']}/bundle")
    assert bundle.status_code == 200
    bundle_payload = bundle.json()
    assert Path(bundle_payload["artifact_dir"]).exists()
    assert Path(bundle_payload["report_path"]).exists()
    assert Path(bundle_payload["events_path"]).exists()
    assert Path(bundle_payload["zip_path"]).exists()

    events = client.get(f"/api/runs/{payload['run_id']}/events")
    assert events.status_code == 200
    assert len(events.json()) >= 1

    continued = client.post(f"/api/research-loops/{payload['run_id']}/continue", json={"iterations": 1})
    assert continued.status_code == 200
    assert continued.json()["iteration_count"] == 4

    run_status = client.get(f"/api/runs/{payload['run_id']}/status")
    assert run_status.status_code == 200
    assert run_status.json()["status"] == "completed"
