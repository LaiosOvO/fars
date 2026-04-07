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
                    paragraphs=["First paragraph.", "Second paragraph."],
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
    settings = Settings(database_url=f"sqlite+pysqlite:///{tmp_path / 'test.db'}")
    app = create_app(settings=settings, openalex_client=FakeOpenAlexClient(), default_parser=FakeParser())
    return TestClient(app)


def test_health_endpoint(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ingest_and_read_paper(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    ingest = client.post("/api/topics/ingest", json={"topic": "transformers", "limit": 2})
    assert ingest.status_code == 200
    payload = ingest.json()
    assert payload["papers_created"] == 2
    assert len(payload["paper_ids"]) == 2

    detail = client.get(f"/api/papers/{payload['paper_ids'][0]}")
    assert detail.status_code == 200
    assert detail.json()["canonical_title"] == "Source Paper"
    assert len(detail.json()["versions"]) == 1


def test_parse_version_creates_graph_edge(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    ingest = client.post("/api/topics/ingest", json={"topic": "transformers", "limit": 2})
    payload = ingest.json()
    source_paper_id = payload["paper_ids"][0]
    source_version_id = payload["version_ids"][0]

    parse = client.post(f"/api/paper-versions/{source_version_id}/parse")
    assert parse.status_code == 200
    parse_payload = parse.json()
    assert parse_payload["sections_created"] == 1
    assert parse_payload["chunks_created"] == 2
    assert parse_payload["citations_created"] == 1
    assert parse_payload["edges_created"] == 1

    neighbors = client.get(f"/api/graph/papers/{source_paper_id}/neighbors")
    assert neighbors.status_code == 200
    neighbor_payload = neighbors.json()
    assert len(neighbor_payload) == 1
    assert neighbor_payload[0]["title"] == "Target Paper"
    assert neighbor_payload[0]["edge_type"] == "cites"
