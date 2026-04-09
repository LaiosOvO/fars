from __future__ import annotations

from fars_kg.config import get_settings
from fars_kg.migrations import run_alembic_upgrade


def main() -> None:
    settings = get_settings()
    run_alembic_upgrade(settings.database_url, config_path=settings.alembic_config_path)
    print("database upgraded")


if __name__ == "__main__":
    main()

