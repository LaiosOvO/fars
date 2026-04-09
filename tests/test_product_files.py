from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_production_artifacts_exist() -> None:
    assert (ROOT / "Dockerfile").exists()
    assert (ROOT / "docker-compose.yml").exists()
    assert (ROOT / ".env.example").exists()
    assert (ROOT / "Makefile").exists()
    assert (ROOT / "alembic.ini").exists()
    assert (ROOT / "alembic" / "env.py").exists()
    assert (ROOT / "alembic" / "versions" / "20260408_0001_initial_schema.py").exists()
    assert (ROOT / "scripts" / "db_upgrade.py").exists()
    assert (ROOT / "scripts" / "db_current.py").exists()
    assert (ROOT / "scripts" / "run_batch_research_loop.py").exists()


def test_env_example_contains_core_settings() -> None:
    content = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "FARS_DATABASE_URL" in content
    assert "FARS_DATABASE_BOOTSTRAP_MODE" in content
    assert "FARS_ALEMBIC_CONFIG_PATH" in content
    assert "FARS_ARTIFACTS_ROOT" in content
    assert "FARS_PARSER_PROVIDER" in content
    assert "FARS_ENABLE_REQUEST_LOGGING" in content
    assert "FARS_REQUEST_ID_HEADER" in content
    assert "FARS_OPERATOR_TOKEN" in content


def test_dockerfile_starts_api() -> None:
    content = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "uvicorn" in content
    assert "fars_kg.api.app:app" in content
    assert "COPY alembic.ini" in content
    assert "COPY alembic " in content


def test_makefile_has_core_targets() -> None:
    content = (ROOT / "Makefile").read_text(encoding="utf-8")
    for target in (
        "install:",
        "test:",
        "run:",
        "loop:",
        "batch-loop:",
        "loop-continue:",
        "openapi:",
        "smoke:",
        "db-upgrade:",
        "db-current:",
    ):
        assert target in content


def test_docker_compose_defaults_to_migration_bootstrap() -> None:
    content = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "FARS_DATABASE_BOOTSTRAP_MODE" in content
    assert "migrate" in content
    assert "FARS_ALEMBIC_CONFIG_PATH" in content
