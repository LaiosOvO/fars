from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


class DatabaseManager:
    def __init__(self, database_url: str):
        self.database_url = database_url
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        self.engine = create_engine(database_url, future=True, connect_args=connect_args)
        self.session_factory = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, expire_on_commit=False)

    def init_db(self, bootstrap_mode: str = "create_all", alembic_config_path: str = "alembic.ini") -> None:
        if bootstrap_mode == "none":
            return
        if bootstrap_mode == "migrate":
            from fars_kg.migrations import run_alembic_upgrade

            run_alembic_upgrade(self.database_url, config_path=alembic_config_path)
            return
        if bootstrap_mode != "create_all":
            raise ValueError(f"Unsupported database bootstrap mode: {bootstrap_mode}")

        from fars_kg import models  # noqa: F401

        Base.metadata.create_all(self.engine)

    def ping(self) -> bool:
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
