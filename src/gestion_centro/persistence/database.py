"""Configuración de SQLite y sesiones SQLAlchemy."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker


def build_engine(database_path: Path, *, busy_timeout_ms: int = 5_000) -> Engine:
    """Crea un motor SQLite con las garantías de durabilidad acordadas."""
    if busy_timeout_ms < 0:
        raise ValueError("busy_timeout_ms no puede ser negativo")

    database_path = database_path.resolve()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{database_path.as_posix()}",
        connect_args={"timeout": busy_timeout_ms / 1_000},
        future=True,
    )

    @event.listens_for(engine, "connect")
    def configure_sqlite(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute(f"PRAGMA busy_timeout={int(busy_timeout_ms)}")
            cursor.execute("PRAGMA synchronous=FULL")
            cursor.execute("PRAGMA journal_mode=DELETE")
        finally:
            cursor.close()

    return engine


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Devuelve una fábrica de sesiones sin confirmación implícita."""
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    """Contexto transaccional: confirma o revierte y siempre cierra la sesión."""
    session = factory()
    try:
        with session.begin():
            yield session
    finally:
        session.close()
