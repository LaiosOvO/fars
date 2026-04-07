from fastapi.testclient import TestClient

from fars.main import create_app


def test_search_endpoint_returns_matching_papers() -> None:
    client = TestClient(create_app())

    response = client.get("/papers/search", params={"q": "bert"})

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    assert any("BERT" in item["canonical_title"] for item in data)


def test_get_paper_detail_returns_seed_paper() -> None:
    client = TestClient(create_app())

    response = client.get("/papers/paper-bert")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "paper-bert"
    assert data["identifiers"]["openalex_id"] == "W2"


def test_topic_ingest_returns_bounded_results() -> None:
    client = TestClient(create_app())

    response = client.post("/papers/ingest/topic", json={"query": "transformer", "limit": 2})

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "transformer"
    assert data["count"] <= 2


def test_graph_neighbors_returns_edges_for_seed_paper() -> None:
    client = TestClient(create_app())

    response = client.get("/graph/papers/paper-roberta/neighbors")

    assert response.status_code == 200
    data = response.json()
    assert data["paper_id"] == "paper-roberta"
    assert len(data["neighbors"]) == 2
    assert any(edge["edge_type"] == "extends" for edge in data["neighbors"])
