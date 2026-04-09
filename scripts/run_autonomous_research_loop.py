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
        db_path = Path(tmp) / "loop.db"
        settings = Settings(database_url=f"sqlite+pysqlite:///{db_path}")
        app = create_app(settings=settings, openalex_client=FakeOpenAlexClient(), default_parser=FakeParser())
        client = TestClient(app)

        response = client.post(
            "/api/research-loops/run",
            json={"topic": "transformers", "limit": 2, "iterations": 3, "use_worktree": False},
        )
        response.raise_for_status()
        payload = response.json()
        report = client.get(f"/api/runs/{payload['run_id']}/report")
        report.raise_for_status()
        draft = client.get(f"/api/runs/{payload['run_id']}/paper-draft")
        draft.raise_for_status()
        bundle = client.get(f"/api/runs/{payload['run_id']}/bundle")
        bundle.raise_for_status()
        report_payload = report.json()

        print("Autonomous research loop completed")
        print(payload)
        print(report_payload["title"])
        print(report_payload["figure_path"])
        print(draft.json()["title"])
        print(bundle.json()["artifact_dir"])


if __name__ == "__main__":
    main()
