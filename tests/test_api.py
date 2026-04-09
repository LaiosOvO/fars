from pathlib import Path
import json
from datetime import datetime
import threading

from fastapi.testclient import TestClient

from fars_kg.api.app import create_app
from fars_kg.config import Settings
from fars_kg.connectors.openalex import OpenAlexClientProtocol, OpenAlexWork
from fars_kg.parsers.base import ParseResult, ParsedCitation, ParsedSection, ParserProtocol
from fars_kg.worktree import GitWorktreeManager
import subprocess


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


class MultiVersionOpenAlexClient:
    def search_topic(self, topic: str, limit: int = 10) -> list[OpenAlexWork]:
        return [
            OpenAlexWork(
                openalex_id="https://openalex.org/W1",
                title="Source Paper",
                doi="10.1000/source",
                publication_year=2024,
                venue="TestConf",
                abstract="Source abstract",
                source_url="https://example.com/source-v1",
                pdf_url="https://example.com/source-v1.pdf",
                citation_count=5,
            ),
            OpenAlexWork(
                openalex_id="https://openalex.org/W1",
                title="Source Paper",
                doi="10.1000/source",
                publication_year=2024,
                venue="TestConf",
                abstract="Source abstract",
                source_url="https://example.com/source-v2",
                pdf_url="https://example.com/source-v2.pdf",
                citation_count=5,
            ),
            OpenAlexWork(
                openalex_id="https://openalex.org/W2",
                title="Target Paper A",
                doi="10.1000/target-a",
                publication_year=2023,
                venue="TestConf",
                abstract="Target A abstract",
                source_url="https://example.com/target-a",
                pdf_url="https://example.com/target-a.pdf",
                citation_count=7,
            ),
            OpenAlexWork(
                openalex_id="https://openalex.org/W3",
                title="Target Paper B",
                doi="10.1000/target-b",
                publication_year=2023,
                venue="TestConf",
                abstract="Target B abstract",
                source_url="https://example.com/target-b",
                pdf_url="https://example.com/target-b.pdf",
                citation_count=6,
            ),
        ][:limit]


class MultiVersionParser:
    provider_name = "multi"

    def parse_version(self, version: object) -> ParseResult:
        source_url = getattr(version, "source_url", "") or ""
        if source_url.endswith("source-v1"):
            target_openalex_id = "https://openalex.org/W2"
            target_label = "Target Paper A"
        else:
            target_openalex_id = "https://openalex.org/W3"
            target_label = "Target Paper B"
        context = f"We compare against {target_label}."
        return ParseResult(
            sections=[
                ParsedSection(
                    section_type="body",
                    heading="Introduction",
                    paragraphs=[context],
                )
            ],
            citations=[
                ParsedCitation(
                    raw_reference=f"{target_label} citation",
                    target_openalex_id=target_openalex_id,
                    resolution_confidence=0.9,
                    contexts=[context],
                )
            ],
        )


class FlakyOnceParser:
    provider_name = "flaky-once"

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._failed = False

    def parse_version(self, version: object) -> ParseResult:
        with self._lock:
            if not self._failed:
                self._failed = True
                raise RuntimeError("database is locked")
        return FakeParser().parse_version(version)


def build_client(
    tmp_path: Path,
    *,
    settings: Settings | None = None,
    openalex_client: OpenAlexClientProtocol | None = None,
    default_parser: ParserProtocol | None = None,
) -> TestClient:
    settings = settings or Settings(database_url=f"sqlite+pysqlite:///{tmp_path / 'test.db'}")
    repo_root = tmp_path / "repo"
    repo_root.mkdir(exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True)
    (repo_root / "README.md").write_text("# repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
    manager = GitWorktreeManager(str(repo_root), str(tmp_path / "worktrees"))
    app = create_app(
        settings=settings,
        openalex_client=openalex_client or FakeOpenAlexClient(),
        default_parser=default_parser or FakeParser(),
        worktree_manager=manager,
    )
    return TestClient(app)


def test_health_endpoint(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["X-Request-ID"]
    assert response.headers["X-Process-Time-Ms"]
    assert response.json()["version"] == "0.1.0"
    assert response.json()["environment"] == "development"

    readiness = client.get("/api/health/readiness")
    assert readiness.status_code == 200
    readiness_payload = readiness.json()
    assert readiness_payload["status"] == "ready"
    assert readiness_payload["database_status"] == "ok"
    assert readiness_payload["database_bootstrap_mode"] == "create_all"
    assert readiness_payload["request_logging_enabled"] is True
    assert readiness_payload["paper_count"] == 0
    assert readiness_payload["run_count"] == 0

    info = client.get("/api/system/info")
    assert info.status_code == 200
    info_payload = info.json()
    assert info_payload["version"] == "0.1.0"
    assert info_payload["environment"] == "development"
    assert info_payload["database_bootstrap_mode"] == "create_all"
    assert info_payload["parser_provider"] == "noop"
    assert info_payload["artifacts_root"] == ".artifacts"
    assert info_payload["request_id_header"] == "X-Request-ID"
    assert info_payload["request_logging_enabled"] is True


def test_console_ui_routes(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    root = client.get("/", follow_redirects=False)
    assert root.status_code in {307, 308}
    assert root.headers["location"] == "/fars"

    fars = client.get("/fars")
    assert fars.status_code == 200
    assert "text/html" in fars.headers["content-type"]
    fars_body = fars.text
    assert "FARS: Fully Automated Research System" in fars_body
    assert "FARS DEPLOYMENTS" in fars_body
    assert "RESEARCH RUNS" in fars_body
    assert 'href="https://analemma.ai/#blog"' in fars_body
    assert 'href="https://analemma.ai/about/"' in fars_body
    assert "margin-bottom: 34px;" in fars_body
    assert "margin: 24px auto 34px;" in fars_body
    assert "letter-spacing: 0.06em;" in fars_body
    assert "X / Follow" in fars_body
    assert "YouTube Channel" in fars_body
    assert "Toggle menu" in fars_body
    assert "mobile-sheet" in fars_body
    assert "toggleMenu" in fars_body
    assert 'role="dialog"' in fars_body
    assert 'aria-modal="true"' in fars_body
    assert 'id="mobile-sheet-title"' in fars_body
    assert '<line x1="4" x2="20" y1="6" y2="6"></line>' in fars_body
    assert ".nav-links a.secondary::after" in fars_body
    assert ".mobile-sheet-nav a.external::after" in fars_body
    assert ".social a:hover" in fars_body
    assert ".nav-links a.secondary:hover" in fars_body
    assert ".mobile-sheet-nav a:hover" in fars_body
    assert ".social a:focus-visible" in fars_body
    assert ".footer a:focus-visible" in fars_body
    assert "@media (prefers-reduced-motion: reduce)" in fars_body
    assert ".card:hover" in fars_body
    assert 'document.body.style.overflow = open ? "hidden" : ""' in fars_body
    assert "main.inert = open" in fars_body
    assert 'event.key !== "Tab"' in fars_body
    assert "toggle.focus();" in fars_body
    assert 'event.key === "Escape"' in fars_body
    assert 'viewBox="0 0 24 24"' in fars_body
    assert "mini-pill" in fars_body
    assert "letter-spacing: 0.04em;" in fars_body
    assert 'class="spinner"' in fars_body
    assert "Visible deployments:" in fars_body
    assert "Visible runs:" in fars_body
    assert "Visible events:" in fars_body
    assert 'id="deployments-count"' in fars_body
    assert 'id="runs-count"' in fars_body
    assert 'id="events-count"' in fars_body
    assert "public progress tracking" in fars_body
    assert "Full details remain in the operator console." in fars_body
    assert ".hero-image:hover" in fars_body
    assert ".footer a:hover" in fars_body
    assert "action-bar" not in fars_body
    assert "last-updated" in fars_body
    assert "Terms of Service" in fars_body
    assert "Join Us" in fars_body
    assert '.footer a::after' in fars_body
    assert "Public live view for autonomous research progress." in fars_body
    assert "PAPER INSPECTION" not in fars_body
    assert "LATEST RUN EVENTS" in fars_body
    assert "/fars/events?limit=16" in fars_body
    assert "Open advanced operator console" not in fars_body
    assert 'id="k-ready"' not in fars_body
    assert "fars-live.analemma.ai/images/fars/live-completed-card.jpg" not in fars_body
    assert "FARS live deployment completed card" in fars_body

    console = client.get("/console")
    assert console.status_code == 200
    assert "text/html" in console.headers["content-type"]
    body = console.text
    assert "FARS Research Console" in body
    assert "research-loops/run" in body
    assert "const API = \"/api\"" in body
    assert "Graph Viewer" in body
    assert "Paper Explorer" in body
    assert "paper-search" in body
    assert "Run Reconciliation" in body
    assert "reconcile-submit" in body
    assert "Logs" in body


def test_console_operator_token_gate_and_login(tmp_path: Path) -> None:
    settings = Settings(
        database_url=f"sqlite+pysqlite:///{tmp_path / 'secure.db'}",
        operator_token="secret-token",
    )
    client = build_client(tmp_path, settings=settings)

    fars = client.get("/fars")
    assert fars.status_code == 200

    locked = client.get("/console")
    assert locked.status_code == 401
    assert "Operator Login" in locked.text

    public_data = client.get("/fars/data")
    assert public_data.status_code == 200
    payload = public_data.json()
    assert payload["generated_at"]
    assert payload["counts"]["deployments"] >= 0
    assert payload["counts"]["research_runs"] >= 0
    if payload["research_runs"]:
        assert "branch_name" not in payload["research_runs"][0]
        assert "summary" not in payload["research_runs"][0]
        assert "has_artifact" not in payload["research_runs"][0]
    if payload["deployments"]:
        assert "exists" not in payload["deployments"][0]

    public_events = client.get("/fars/events")
    assert public_events.status_code == 200
    events_payload = public_events.json()
    assert events_payload["generated_at"]
    assert isinstance(events_payload["events"], list)
    if events_payload["events"]:
        event = events_payload["events"][0]
        assert "run_id" in event
        assert "event_type" in event
        assert "status" in event
        assert "source" in event
        assert "time_created" in event
        assert "message" not in event
        assert "payload_json" not in event

    denied = client.post(
        "/api/research-loops/batch-run",
        json={
            "topics": ["transformers"],
            "limit": 2,
            "iterations": 1,
            "use_worktree": False,
            "max_concurrency": 1,
        },
    )
    assert denied.status_code == 401

    denied_runs = client.get("/api/runs")
    assert denied_runs.status_code == 401

    denied_batches = client.get("/api/research-loops/batches")
    assert denied_batches.status_code == 401

    assert client.get("/api/health/").status_code == 200
    assert client.get("/api/health/readiness/").status_code == 200
    assert client.get("/api/system/info/").status_code == 200

    login = client.post("/console/login", data={"token": "secret-token"}, follow_redirects=False)
    assert login.status_code == 303
    assert login.headers["location"] == "/console"

    unlocked = client.get("/console")
    assert unlocked.status_code == 200
    assert "FARS Research Console" in unlocked.text

    allowed = client.post(
        "/api/research-loops/batch-run",
        json={
            "topics": ["transformers"],
            "limit": 2,
            "iterations": 1,
            "use_worktree": False,
            "max_concurrency": 1,
        },
    )
    assert allowed.status_code == 200


def test_readiness_returns_503_when_schema_is_missing(tmp_path: Path) -> None:
    settings = Settings(
        database_url=f"sqlite+pysqlite:///{tmp_path / 'missing_schema.db'}",
        database_bootstrap_mode="none",
    )
    client = build_client(tmp_path, settings=settings)
    readiness = client.get("/api/health/readiness")
    assert readiness.status_code == 503
    payload = readiness.json()
    assert payload["status"] == "not_ready"
    assert payload["database_status"] == "error"
    assert payload["database_bootstrap_mode"] == "none"
    assert payload["paper_count"] == 0
    assert payload["run_count"] == 0


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
    assert detail.json()["result_stats"]["result_count"] == 0

    search = client.get("/api/papers/search", params={"q": "source"})
    assert search.status_code == 200
    assert any(item["canonical_title"] == "Source Paper" for item in search.json())


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
    assert parse_payload["chunks_created"] == 3
    assert parse_payload["citations_created"] == 1
    assert parse_payload["edges_created"] == 1

    neighbors = client.get(f"/api/graph/papers/{source_paper_id}/neighbors")
    assert neighbors.status_code == 200
    neighbor_payload = neighbors.json()
    assert len(neighbor_payload) == 1
    assert neighbor_payload[0]["title"] == "Target Paper"
    assert neighbor_payload[0]["edge_type"] == "cites"

    mermaid = client.get(f"/api/graph/papers/{source_paper_id}/mermaid")
    assert mermaid.status_code == 200
    mermaid_payload = mermaid.json()
    assert "graph LR" in mermaid_payload["mermaid"]
    assert "Source Paper" in mermaid_payload["mermaid"]
    assert "Target Paper" in mermaid_payload["mermaid"]

    sections = client.get(f"/api/papers/{source_paper_id}/sections")
    assert sections.status_code == 200
    assert sections.json()[0]["heading"] == "Introduction"

    citations = client.get(f"/api/papers/{source_paper_id}/citations")
    assert citations.status_code == 200
    citations_payload = citations.json()
    assert citations_payload[0]["target_paper_title"] == "Target Paper"
    assert citations_payload[0]["contexts"][0]["context_text"] == "We compare against Target Paper."
    assert citations_payload[0]["contexts"][0]["context_type"] == "comparison"

    explanations = client.get(f"/api/graph/papers/{source_paper_id}/explanations")
    assert explanations.status_code == 200
    explanation_payload = explanations.json()
    assert explanation_payload["paper_id"] == source_paper_id
    assert explanation_payload["explanations"][0]["target_paper_title"] == "Target Paper"
    assert "cites" in explanation_payload["explanations"][0]["edge_types"]
    assert "comparison" in explanation_payload["explanations"][0]["context_types"]


def test_reparse_does_not_duplicate_citation_edges(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    ingest = client.post("/api/topics/ingest", json={"topic": "transformers", "limit": 2})
    payload = ingest.json()
    source_paper_id = payload["paper_ids"][0]
    source_version_id = payload["version_ids"][0]

    first_parse = client.post(f"/api/paper-versions/{source_version_id}/parse")
    assert first_parse.status_code == 200
    assert first_parse.json()["edges_created"] == 1

    second_parse = client.post(f"/api/paper-versions/{source_version_id}/parse")
    assert second_parse.status_code == 200
    assert second_parse.json()["edges_created"] == 1

    neighbors = client.get(f"/api/graph/papers/{source_paper_id}/neighbors")
    assert neighbors.status_code == 200
    cites_neighbors = [item for item in neighbors.json() if item["edge_type"] == "cites"]
    assert len(cites_neighbors) == 1

    citations = client.get(f"/api/papers/{source_paper_id}/citations")
    assert citations.status_code == 200
    assert len(citations.json()) == 1


def test_infer_semantic_edges_uses_all_versions(tmp_path: Path) -> None:
    client = build_client(
        tmp_path,
        openalex_client=MultiVersionOpenAlexClient(),
        default_parser=MultiVersionParser(),
    )
    ingest = client.post("/api/topics/ingest", json={"topic": "transformers", "limit": 4})
    assert ingest.status_code == 200
    payload = ingest.json()

    source_paper_id = payload["paper_ids"][0]
    source_version_ids = payload["version_ids"][:2]
    assert payload["paper_ids"][0] == payload["paper_ids"][1]

    for version_id in source_version_ids:
        parse = client.post(f"/api/paper-versions/{version_id}/parse")
        assert parse.status_code == 200
        assert parse.json()["citations_created"] == 1

    infer = client.post(f"/api/graph/papers/{source_paper_id}/infer-semantic-edges")
    assert infer.status_code == 200
    infer_payload = infer.json()
    assert infer_payload["edges_created"] == 2

    evidence = client.get(f"/api/papers/{source_paper_id}/evidence-pack")
    assert evidence.status_code == 200
    compares_targets = sorted(
        item["title"]
        for item in evidence.json()["neighbors"]
        if item["edge_type"] == "compares"
    )
    assert compares_targets == ["Target Paper A", "Target Paper B"]


def test_semantic_enrichment_and_evidence_pack(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    ingest = client.post("/api/topics/ingest", json={"topic": "transformers", "limit": 2})
    payload = ingest.json()
    source_paper_id = payload["paper_ids"][0]
    source_version_id = payload["version_ids"][0]

    parse = client.post(f"/api/paper-versions/{source_version_id}/parse")
    assert parse.status_code == 200

    enrich = client.post(
        f"/api/papers/{source_paper_id}/semantic-enrichment",
        json={"methods": ["Transformer"], "datasets": ["WMT14"], "metrics": ["BLEU"]},
    )
    assert enrich.status_code == 200
    enrich_payload = enrich.json()
    assert enrich_payload["methods_attached"] == 1
    assert enrich_payload["datasets_attached"] == 1
    assert enrich_payload["metrics_attached"] == 1

    evidence = client.get(f"/api/papers/{source_paper_id}/evidence-pack")
    assert evidence.status_code == 200
    evidence_payload = evidence.json()
    assert evidence_payload["paper_id"] == source_paper_id
    assert evidence_payload["canonical_title"] == "Source Paper"
    assert evidence_payload["methods"][0]["name"] == "Transformer"
    assert evidence_payload["datasets"][0]["name"] == "WMT14"
    assert evidence_payload["metrics"][0]["name"] == "BLEU"
    assert len(evidence_payload["neighbors"]) == 1


def test_auto_semantic_enrichment_from_parsed_text(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    ingest = client.post("/api/topics/ingest", json={"topic": "transformers", "limit": 2})
    payload = ingest.json()
    source_paper_id = payload["paper_ids"][0]
    source_version_id = payload["version_ids"][0]

    parse = client.post(f"/api/paper-versions/{source_version_id}/parse")
    assert parse.status_code == 200

    enrich = client.post(f"/api/papers/{source_paper_id}/semantic-enrichment/auto")
    assert enrich.status_code == 200
    enrich_payload = enrich.json()
    assert enrich_payload["methods_attached"] >= 1
    assert enrich_payload["datasets_attached"] >= 1
    assert enrich_payload["metrics_attached"] >= 1
    assert "Transformer" in enrich_payload["extracted_methods"]
    assert "WMT14" in enrich_payload["extracted_datasets"]
    assert "BLEU" in enrich_payload["extracted_metrics"]


def test_semantic_edge_inference_from_citation_context(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    ingest = client.post("/api/topics/ingest", json={"topic": "transformers", "limit": 2})
    payload = ingest.json()
    source_paper_id = payload["paper_ids"][0]
    source_version_id = payload["version_ids"][0]

    parse = client.post(f"/api/paper-versions/{source_version_id}/parse")
    assert parse.status_code == 200

    infer = client.post(f"/api/graph/papers/{source_paper_id}/infer-semantic-edges")
    assert infer.status_code == 200
    infer_payload = infer.json()
    assert infer_payload["paper_id"] == source_paper_id
    assert infer_payload["edges_created"] == 1

    evidence = client.get(f"/api/papers/{source_paper_id}/evidence-pack")
    assert evidence.status_code == 200
    edge_types = {neighbor["edge_type"] for neighbor in evidence.json()["neighbors"]}
    assert "compares" in edge_types


def test_snapshot_and_run_workflow_contract(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    ingest = client.post("/api/topics/ingest", json={"topic": "transformers", "limit": 2})
    payload = ingest.json()
    source_paper_id = payload["paper_ids"][0]
    source_version_id = payload["version_ids"][0]

    parse = client.post(f"/api/paper-versions/{source_version_id}/parse")
    assert parse.status_code == 200

    enrich = client.post(
        f"/api/papers/{source_paper_id}/semantic-enrichment",
        json={"methods": ["Transformer"], "datasets": ["WMT14"], "metrics": ["BLEU"]},
    )
    assert enrich.status_code == 200

    snapshot = client.post(f"/api/papers/{source_paper_id}/snapshots", json={"topic": "machine translation"})
    assert snapshot.status_code == 200
    snapshot_payload = snapshot.json()
    assert snapshot_payload["paper_id"] == source_paper_id
    assert snapshot_payload["topic"] == "machine translation"

    run = client.post("/api/runs", json={"snapshot_id": snapshot_payload["id"], "branch_name": "exp-branch-1"})
    assert run.status_code == 200
    run_payload = run.json()
    assert run_payload["status"] == "created"
    assert run_payload["branch_name"] == "exp-branch-1"

    manifest = client.get(f"/api/runs/{run_payload['id']}/execution-manifest")
    assert manifest.status_code == 200
    manifest_payload = manifest.json()
    assert manifest_payload["knowledge_mode"] == "shared_snapshot"
    assert manifest_payload["execution_mode"] == "isolated_worktree"

    worktree = client.post(f"/api/runs/{run_payload['id']}/worktree")
    assert worktree.status_code == 200
    worktree_payload = worktree.json()
    assert worktree_payload["branch_name"] == "exp-branch-1"
    assert Path(worktree_payload["worktree_path"]).exists()

    writeback = client.post(
        f"/api/runs/{run_payload['id']}/result",
        json={
            "status": "completed",
            "result_summary": "Semantic enrichment baseline run completed",
            "result_payload_json": '{\"f1\": 0.91}',
        },
    )
    assert writeback.status_code == 200
    writeback_payload = writeback.json()
    assert writeback_payload["status"] == "completed"
    assert writeback_payload["result_summary"] == "Semantic enrichment baseline run completed"

    experiment = client.post(
        f"/api/runs/{run_payload['id']}/experiment-results",
        json={
            "paper_id": source_paper_id,
            "method_name": "Transformer",
            "dataset_name": "WMT14",
            "metric_name": "BLEU",
            "value": "28.4",
            "notes": "baseline run",
        },
    )
    assert experiment.status_code == 200
    experiment_payload = experiment.json()
    assert experiment_payload["metric_name"] == "BLEU"
    assert experiment_payload["value"] == "28.4"

    results = client.get(f"/api/papers/{source_paper_id}/results")
    assert results.status_code == 200
    results_payload = results.json()
    assert len(results_payload) == 1
    assert results_payload[0]["method_name"] == "Transformer"
    assert results_payload[0]["source"] == "manual"

    detail = client.get(f"/api/papers/{source_paper_id}")
    assert detail.status_code == 200
    detail_payload = detail.json()
    assert detail_payload["result_stats"]["result_count"] == 1
    assert detail_payload["result_stats"]["metric_names"] == ["BLEU"]

    auto_result = client.post(
        f"/api/runs/{run_payload['id']}/experiment-results/auto",
        json={"paper_id": source_paper_id},
    )
    assert auto_result.status_code == 200
    auto_payload = auto_result.json()
    assert auto_payload["created_count"] >= 1
    assert auto_payload["results"][0]["metric_name"] == "BLEU"
    assert auto_payload["results"][0]["source"] == "auto_extract"


def test_topic_landscape_aggregates_entities_and_edges(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    ingest = client.post("/api/topics/ingest", json={"topic": "transformers", "limit": 2})
    payload = ingest.json()
    source_paper_id = payload["paper_ids"][0]
    source_version_id = payload["version_ids"][0]

    parse = client.post(f"/api/paper-versions/{source_version_id}/parse")
    assert parse.status_code == 200

    enrich = client.post(f"/api/papers/{source_paper_id}/semantic-enrichment/auto")
    assert enrich.status_code == 200

    infer = client.post(f"/api/graph/papers/{source_paper_id}/infer-semantic-edges")
    assert infer.status_code == 200

    snapshot = client.post(f"/api/papers/{source_paper_id}/snapshots", json={"topic": "paper"})
    assert snapshot.status_code == 200
    run = client.post("/api/runs", json={"snapshot_id": snapshot.json()["id"], "branch_name": "landscape-run"})
    assert run.status_code == 200
    result = client.post(
        f"/api/runs/{run.json()['id']}/experiment-results",
        json={
            "paper_id": source_paper_id,
            "method_name": "Transformer",
            "dataset_name": "WMT14",
            "metric_name": "BLEU",
            "value": "28.4",
        },
    )
    assert result.status_code == 200

    auto_result = client.post(
        f"/api/runs/{run.json()['id']}/experiment-results/auto",
        json={"paper_id": source_paper_id},
    )
    assert auto_result.status_code == 200

    landscape = client.get("/api/topics/landscape", params={"q": "paper"})
    assert landscape.status_code == 200
    payload = landscape.json()
    assert payload["paper_count"] >= 2
    assert "Transformer" in payload["methods"]
    assert "WMT14" in payload["datasets"]
    assert "BLEU" in payload["metrics"]
    assert "cites" in payload["edge_type_counts"]
    assert payload["result_count"] >= 1
    assert payload["papers_with_results"] >= 1
    assert payload["top_result_papers"][0]["canonical_title"] == "Source Paper"


def test_autonomous_research_loop_without_worktree(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    response = client.post(
        "/api/research-loops/run",
        json={"topic": "transformers", "limit": 2, "iterations": 3, "use_worktree": False},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["topic"] == "transformers"
    assert payload["requested_iterations"] == 3
    assert len(payload["paper_ids"]) == 2
    assert payload["parsed_versions"] == 2
    assert payload["enriched_papers"] == 2
    assert payload["result_count"] >= 1
    assert payload["executed_result_count"] >= 1
    assert payload["hypothesis_count"] >= 1
    assert payload["experiment_plan_count"] >= 1
    assert payload["experiment_task_count"] >= 3
    assert payload["iteration_count"] == 3
    assert payload["used_worktree"] is False
    assert "Autonomous loop completed" in payload["summary"]

    hypotheses = client.get(f"/api/runs/{payload['run_id']}/hypotheses")
    assert hypotheses.status_code == 200
    assert len(hypotheses.json()) >= 1

    plans = client.get(f"/api/runs/{payload['run_id']}/experiment-plans")
    assert plans.status_code == 200
    assert len(plans.json()) >= 1

    tasks = client.get(f"/api/runs/{payload['run_id']}/experiment-tasks")
    assert tasks.status_code == 200
    tasks_payload = tasks.json()
    assert len(tasks_payload) >= 3
    task_types = {task["task_type"] for task in tasks_payload}
    assert {"benchmark", "ablation", "comparison"}.issubset(task_types)

    iterations = client.get(f"/api/runs/{payload['run_id']}/iterations")
    assert iterations.status_code == 200
    assert len(iterations.json()) >= 1
    assert iterations.json()[0]["decision"] in {"keep", "discard"}

    report = client.post(f"/api/runs/{payload['run_id']}/report")
    assert report.status_code == 200
    report_payload = report.json()
    assert "Autonomous Research Report" in report_payload["title"]
    assert "## Hypotheses" in report_payload["markdown"]
    assert "## Experiment Plans" in report_payload["markdown"]
    assert "## Experiment Results" in report_payload["markdown"]
    assert report_payload["figure_path"].endswith(".svg")
    assert Path(report_payload["figure_path"]).exists()
    assert ".svg" in report_payload["markdown"]

    draft = client.get(f"/api/runs/{payload['run_id']}/paper-draft")
    assert draft.status_code == 200
    draft_payload = draft.json()
    required_sections = [
        "## Abstract",
        "## Introduction",
        "## Related Work",
        "## Hypotheses",
        "## Method",
        "## Experiment Setup",
        "## Results",
        "## Discussion",
        "## Conclusion",
        "## References",
    ]
    for section in required_sections:
        assert section in draft_payload["markdown"]
    assert draft_payload["figure_path"].endswith(".svg")
    assert Path(draft_payload["figure_path"]).exists()

    bundle = client.get(f"/api/runs/{payload['run_id']}/bundle")
    assert bundle.status_code == 200
    bundle_payload = bundle.json()
    assert Path(bundle_payload["artifact_dir"]).exists()
    assert Path(bundle_payload["report_path"]).exists()
    assert Path(bundle_payload["paper_draft_path"]).exists()
    assert Path(bundle_payload["summary_path"]).exists()
    assert Path(bundle_payload["iterations_path"]).exists()
    assert Path(bundle_payload["figure_path"]).exists()
    assert Path(bundle_payload["hypotheses_path"]).exists()
    assert Path(bundle_payload["experiment_plans_path"]).exists()
    assert Path(bundle_payload["experiment_tasks_path"]).exists()
    assert Path(bundle_payload["experiment_results_path"]).exists()
    assert Path(bundle_payload["events_path"]).exists()
    assert Path(bundle_payload["manifest_path"]).exists()
    assert Path(bundle_payload["zip_path"]).exists()
    assert "Autonomous Research Report" in Path(bundle_payload["report_path"]).read_text(encoding="utf-8")
    assert "## Abstract" in Path(bundle_payload["paper_draft_path"]).read_text(encoding="utf-8")
    manifest_payload = json.loads(Path(bundle_payload["manifest_path"]).read_text(encoding="utf-8"))
    assert manifest_payload["run_id"] == payload["run_id"]
    assert manifest_payload["files"]["zip_path"]["path"].endswith("bundle.zip")
    assert manifest_payload["files"]["zip_path"]["exists"] is True
    assert manifest_payload["files"]["zip_path"]["sha256"]
    assert manifest_payload["files"]["events_path"]["exists"] is True

    events = client.get(f"/api/runs/{payload['run_id']}/events")
    assert events.status_code == 200
    events_payload = events.json()
    assert events_payload
    event_ids = [item["id"] for item in events_payload]
    assert event_ids == sorted(event_ids)
    event_times = [datetime.fromisoformat(item["time_created"]) for item in events_payload]
    assert event_times == sorted(event_times)
    event_types = {item["event_type"] for item in events_payload}
    assert "run.created" in event_types
    assert "research_loop.started" in event_types
    assert "research_loop.completed" in event_types
    assert "artifact_bundle.generated" in event_types
    for item in events_payload:
        assert item["run_id"] == payload["run_id"]
        if item["payload_json"] is not None:
            parsed_payload = json.loads(item["payload_json"])
            assert isinstance(parsed_payload, (dict, list))

    bundle_download = client.get(f"/api/runs/{payload['run_id']}/bundle/download")
    assert bundle_download.status_code == 200
    assert bundle_download.headers["content-type"].startswith("application/zip")

    manifest_api = client.get(f"/api/runs/{payload['run_id']}/bundle/manifest")
    assert manifest_api.status_code == 200
    manifest_api_payload = manifest_api.json()
    assert manifest_api_payload["run_id"] == payload["run_id"]
    assert manifest_api_payload["files"]["report_path"]["exists"] is True

    report_download = client.get(f"/api/runs/{payload['run_id']}/report/download")
    assert report_download.status_code == 200
    assert report_download.headers["content-type"].startswith("text/markdown")

    draft_download = client.get(f"/api/runs/{payload['run_id']}/paper-draft/download")
    assert draft_download.status_code == 200
    assert draft_download.headers["content-type"].startswith("text/markdown")

    figure_download = client.get(f"/api/runs/{payload['run_id']}/figure/download")
    assert figure_download.status_code == 200
    assert figure_download.headers["content-type"].startswith("image/svg+xml")

    run_detail = client.get(f"/api/runs/{payload['run_id']}")
    assert run_detail.status_code == 200
    assert run_detail.json()["status"] == "completed"

    run_status = client.get(f"/api/runs/{payload['run_id']}/status")
    assert run_status.status_code == 200
    assert run_status.json()["status"] == "completed"

    runs = client.get("/api/runs")
    assert runs.status_code == 200
    assert len(runs.json()) >= 1

    continued = client.post(f"/api/research-loops/{payload['run_id']}/continue", json={"iterations": 2})
    assert continued.status_code == 200
    continued_payload = continued.json()
    assert continued_payload["run_id"] == payload["run_id"]
    assert continued_payload["iteration_count"] == 5


def test_batch_research_loop_orchestration_and_reconciliation(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    response = client.post(
        "/api/research-loops/batch-run",
        json={
            "topics": ["transformers", "machine translation"],
            "limit": 2,
            "iterations": 2,
            "use_worktree": False,
            "max_concurrency": 1,
            "branch_prefix": "batch-test",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["requested_topics"] == ["transformers", "machine translation"]
    assert payload["requested_iterations"] == 2
    assert payload["requested_concurrency"] == 1
    assert payload["completed_count"] == 2
    assert payload["failed_count"] == 0
    assert len(payload["items"]) == 2

    for item in payload["items"]:
        assert item["status"] == "completed"
        assert item["run_id"] is not None
        assert item["lead_paper_id"] is not None
        assert item["lead_paper_title"]
        assert item["artifact_dir"]
        assert Path(item["artifact_dir"]).exists()
        assert item["summary"]
        assert item["result_count"] >= 1
        assert item["error"] is None

    reconciliation = payload["reconciliation"]
    assert reconciliation["successful_run_count"] == 2
    assert reconciliation["failed_run_count"] == 0
    assert reconciliation["total_result_count"] >= 2
    metric_names = {item["metric_name"] for item in reconciliation["best_metrics"]}
    assert "BLEU" in metric_names

    artifact = payload["artifact"]
    assert artifact["kind"] == "batch-run"
    assert artifact["batch_id"]
    assert Path(artifact["artifact_dir"]).exists()
    assert Path(artifact["summary_path"]).exists()
    assert Path(artifact["items_path"]).exists()
    assert Path(artifact["reconciliation_path"]).exists()
    assert Path(artifact["manifest_path"]).exists()
    assert Path(artifact["zip_path"]).exists()

    manifest = client.get(f"/api/research-loops/batches/{artifact['batch_id']}/manifest")
    assert manifest.status_code == 200
    manifest_payload = manifest.json()
    assert manifest_payload["batch_id"] == artifact["batch_id"]
    assert manifest_payload["kind"] == "batch-run"
    assert manifest_payload["files"]["zip_path"]["exists"] is True

    bundle_download = client.get(f"/api/research-loops/batches/{artifact['batch_id']}/download")
    assert bundle_download.status_code == 200
    assert bundle_download.headers["content-type"].startswith("application/zip")

    summary_download = client.get(f"/api/research-loops/batches/{artifact['batch_id']}/summary/download")
    assert summary_download.status_code == 200
    assert summary_download.headers["content-type"].startswith("application/json")

    items_download = client.get(f"/api/research-loops/batches/{artifact['batch_id']}/items/download")
    assert items_download.status_code == 200
    assert items_download.headers["content-type"].startswith("application/json")
    assert isinstance(json.loads(items_download.text), list)

    reconciliation_download = client.get(f"/api/research-loops/batches/{artifact['batch_id']}/reconciliation/download")
    assert reconciliation_download.status_code == 200
    assert reconciliation_download.headers["content-type"].startswith("application/json")
    assert isinstance(json.loads(reconciliation_download.text), dict)


def test_batch_research_loop_retries_transient_parallel_failures(tmp_path: Path) -> None:
    client = build_client(tmp_path, default_parser=FlakyOnceParser())
    response = client.post(
        "/api/research-loops/batch-run",
        json={
            "topics": ["transformers", "machine translation"],
            "limit": 2,
            "iterations": 1,
            "use_worktree": False,
            "max_concurrency": 2,
            "branch_prefix": "batch-retry",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["requested_concurrency"] == 2
    assert payload["completed_count"] == 2
    assert payload["failed_count"] == 0
    assert all(item["status"] == "completed" for item in payload["items"])


def test_batch_research_loop_serializes_worktree_mode(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    response = client.post(
        "/api/research-loops/batch-run",
        json={
            "topics": ["transformers", "machine translation"],
            "limit": 2,
            "iterations": 1,
            "use_worktree": True,
            "max_concurrency": 4,
            "branch_prefix": "batch-worktree",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["requested_concurrency"] == 1
    assert payload["completed_count"] == 2
    for item in payload["items"]:
        run = client.get(f"/api/runs/{item['run_id']}")
        assert run.status_code == 200
        run_payload = run.json()
        assert run_payload["worktree_path"] is not None
        assert Path(run_payload["worktree_path"]).exists()


def test_batch_research_loop_sanitizes_branch_prefix(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    response = client.post(
        "/api/research-loops/batch-run",
        json={
            "topics": ["transformers"],
            "limit": 2,
            "iterations": 1,
            "use_worktree": False,
            "max_concurrency": 1,
            "branch_prefix": "Bad Prefix/$%^",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    run_id = payload["items"][0]["run_id"]
    run = client.get(f"/api/runs/{run_id}")
    assert run.status_code == 200
    branch_name = run.json()["branch_name"]
    assert branch_name.startswith("bad-prefix-")
    assert "/" not in branch_name
    assert " " not in branch_name


def test_reconcile_runs_endpoint(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    batch = client.post(
        "/api/research-loops/batch-run",
        json={
            "topics": ["transformers", "machine translation"],
            "limit": 2,
            "iterations": 1,
            "use_worktree": False,
            "max_concurrency": 1,
        },
    )
    assert batch.status_code == 200
    run_ids = [item["run_id"] for item in batch.json()["items"]]
    assert all(run_ids)

    reconcile = client.post(
        "/api/research-loops/reconcile",
        json={"run_ids": [run_ids[0], run_ids[1], 999999]},
    )
    assert reconcile.status_code == 200
    payload = reconcile.json()
    assert payload["requested_run_ids"] == [run_ids[0], run_ids[1], 999999]
    assert payload["missing_run_ids"] == [999999]
    assert payload["found_count"] == 2
    assert len(payload["items"]) == 2
    assert payload["reconciliation"]["successful_run_count"] == 2
    assert payload["reconciliation"]["failed_run_count"] == 0
    assert payload["reconciliation"]["total_result_count"] >= 2
    assert payload["artifact"]["kind"] == "reconcile"
    assert Path(payload["artifact"]["manifest_path"]).exists()


def test_batch_index_listing_and_kind_filter(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    batch = client.post(
        "/api/research-loops/batch-run",
        json={
            "topics": ["transformers"],
            "limit": 2,
            "iterations": 1,
            "use_worktree": False,
            "max_concurrency": 1,
        },
    )
    assert batch.status_code == 200
    batch_id = batch.json()["artifact"]["batch_id"]
    run_id = batch.json()["items"][0]["run_id"]
    assert run_id is not None

    reconcile = client.post(
        "/api/research-loops/reconcile",
        json={"run_ids": [run_id]},
    )
    assert reconcile.status_code == 200
    reconcile_batch_id = reconcile.json()["artifact"]["batch_id"]

    index_all = client.get("/api/research-loops/batches", params={"limit": 10})
    assert index_all.status_code == 200
    index_payload = index_all.json()
    batch_ids = {item["batch_id"] for item in index_payload}
    assert batch_id in batch_ids
    assert reconcile_batch_id in batch_ids
    assert all("exists" in item for item in index_payload)

    index_batch_run = client.get("/api/research-loops/batches", params={"kind": "batch-run", "limit": 10})
    assert index_batch_run.status_code == 200
    payload_batch_run = index_batch_run.json()
    assert payload_batch_run
    assert all(item["kind"] == "batch-run" for item in payload_batch_run)


def test_batch_manifest_endpoints_return_404_for_unknown_batch(tmp_path: Path) -> None:
    client = build_client(tmp_path)
    manifest = client.get("/api/research-loops/batches/nonexistent123/manifest")
    assert manifest.status_code == 404
    bundle = client.get("/api/research-loops/batches/nonexistent123/download")
    assert bundle.status_code == 404
    summary = client.get("/api/research-loops/batches/nonexistent123/summary/download")
    assert summary.status_code == 404
    items = client.get("/api/research-loops/batches/nonexistent123/items/download")
    assert items.status_code == 404
    reconciliation = client.get("/api/research-loops/batches/nonexistent123/reconciliation/download")
    assert reconciliation.status_code == 404
