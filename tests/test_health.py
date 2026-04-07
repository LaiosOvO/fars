from fastapi.testclient import TestClient

from fars.main import create_app


def test_healthcheck_returns_service_metadata() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "FARS Paper Knowledge Layer"
    assert data["environment"] == "development"
    assert data["version"] == "0.1.0"
    assert data["debug"] is False
