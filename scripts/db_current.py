from __future__ import annotations

from pathlib import Path

from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from fars_kg.config import get_settings


def main() -> None:
    settings = get_settings()
    config_path = Path(settings.alembic_config_path).resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Alembic config not found: {config_path}")

    engine = create_engine(settings.database_url)
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        print(context.get_current_revision() or "none")


if __name__ == "__main__":
    main()
