from fastapi.testclient import TestClient

from fars import CANONICAL_PACKAGE, CANONICAL_RUNTIME, COMPAT_ROLE
from fars.main import create_app


def test_namespace_contract_marks_fars_kg_as_canonical() -> None:
    assert CANONICAL_PACKAGE == "fars_kg"
    assert CANONICAL_RUNTIME == "fars_kg.api.app:app"
    assert COMPAT_ROLE == "demo-compat-surface"


def test_compat_health_exposes_canonical_runtime() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["canonical_runtime"] == "fars_kg.api.app:app"
