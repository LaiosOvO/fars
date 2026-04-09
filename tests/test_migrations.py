from pathlib import Path

import pytest
from sqlalchemy import inspect

from fars_kg.db import DatabaseManager


ROOT = Path(__file__).resolve().parents[1]


def test_database_manager_can_bootstrap_via_alembic(tmp_path: Path) -> None:
    db_path = tmp_path / "migrated.db"
    manager = DatabaseManager(f"sqlite+pysqlite:///{db_path}")
    manager.init_db("migrate", str(ROOT / "alembic.ini"))

    inspector = inspect(manager.engine)
    table_names = set(inspector.get_table_names())
    assert "paper" in table_names
    assert "research_run" in table_names
    assert "research_run_event" in table_names


def test_database_manager_bootstrap_none_skips_schema_creation(tmp_path: Path) -> None:
    db_path = tmp_path / "no_bootstrap.db"
    manager = DatabaseManager(f"sqlite+pysqlite:///{db_path}")
    manager.init_db("none")

    inspector = inspect(manager.engine)
    assert inspector.get_table_names() == []


def test_database_manager_rejects_unsupported_bootstrap_mode(tmp_path: Path) -> None:
    db_path = tmp_path / "unsupported.db"
    manager = DatabaseManager(f"sqlite+pysqlite:///{db_path}")
    with pytest.raises(ValueError, match="Unsupported database bootstrap mode"):
        manager.init_db("invalid-mode")
