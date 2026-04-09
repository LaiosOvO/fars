from __future__ import annotations

from pathlib import Path
import tempfile

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


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "flow.db"
        settings = Settings(database_url=f"sqlite+pysqlite:///{db_path}")
        app = create_app(settings=settings, openalex_client=FakeOpenAlexClient(), default_parser=FakeParser())
        client = TestClient(app)

        ingest = client.post("/api/topics/ingest", json={"topic": "transformers", "limit": 2})
        ingest.raise_for_status()
        ingest_payload = ingest.json()
        source_paper_id = ingest_payload["paper_ids"][0]
        source_version_id = ingest_payload["version_ids"][0]

        parse = client.post(f"/api/paper-versions/{source_version_id}/parse")
        parse.raise_for_status()

        enrich = client.post(f"/api/papers/{source_paper_id}/semantic-enrichment/auto")
        enrich.raise_for_status()

        infer = client.post(f"/api/graph/papers/{source_paper_id}/infer-semantic-edges")
        infer.raise_for_status()

        evidence = client.get(f"/api/papers/{source_paper_id}/evidence-pack")
        evidence.raise_for_status()
        landscape = client.get("/api/topics/landscape", params={"q": "paper"})
        landscape.raise_for_status()

        snapshot = client.post(f"/api/papers/{source_paper_id}/snapshots", json={"topic": "transformers"})
        snapshot.raise_for_status()
        snapshot_payload = snapshot.json()

        run = client.post("/api/runs", json={"snapshot_id": snapshot_payload["id"], "branch_name": "demo-run"})
        run.raise_for_status()
        run_payload = run.json()

        result = client.post(
            f"/api/runs/{run_payload['id']}/result",
            json={
                "status": "completed",
                "result_summary": "Completed without worktree",
                "result_payload_json": "{\"status\": \"ok\"}",
            },
        )
        result.raise_for_status()

        experiment = client.post(
            f"/api/runs/{run_payload['id']}/experiment-results/auto",
            json={"paper_id": source_paper_id},
        )
        experiment.raise_for_status()

        results = client.get(f"/api/papers/{source_paper_id}/results")
        results.raise_for_status()

        print("E2E flow completed without worktree")
        print(
            {
                "paper_id": source_paper_id,
                "version_id": source_version_id,
                "snapshot_id": snapshot_payload["id"],
                "run_id": run_payload["id"],
                "neighbors": len(evidence.json()["neighbors"]),
                "methods": [m["name"] for m in evidence.json()["methods"]],
                "landscape_methods": landscape.json()["methods"],
                "result_count": len(results.json()),
            }
        )


if __name__ == "__main__":
    main()
