from __future__ import annotations

from pathlib import Path


def run_alembic_upgrade(database_url: str, *, revision: str = "head", config_path: str = "alembic.ini") -> None:
    from alembic import command
    from alembic.config import Config

    resolved_config_path = Path(config_path).resolve()
    config = Config(str(resolved_config_path))
    config.set_main_option("script_location", str((resolved_config_path.parent / "alembic").resolve()))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, revision)

