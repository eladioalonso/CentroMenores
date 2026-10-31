from pathlib import Path

import pytest
from sqlalchemy import text

from gestion_centro.persistence.database import build_engine, build_session_factory, session_scope


def test_session_scope_commits_on_success(tmp_path: Path) -> None:
    engine = build_engine(tmp_path / "transactions.db")
    factory = build_session_factory(engine)
    try:
        with session_scope(factory) as session:
            session.execute(text("CREATE TABLE sample (value INTEGER NOT NULL)"))
            session.execute(text("INSERT INTO sample (value) VALUES (7)"))
        with engine.connect() as connection:
            assert connection.execute(text("SELECT value FROM sample")).scalar_one() == 7
    finally:
        engine.dispose()


def test_session_scope_rolls_back_on_error(tmp_path: Path) -> None:
    engine = build_engine(tmp_path / "rollback.db")
    factory = build_session_factory(engine)
    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE sample (value INTEGER NOT NULL)"))
        with pytest.raises(RuntimeError):
            with session_scope(factory) as session:
                session.execute(text("INSERT INTO sample (value) VALUES (9)"))
                raise RuntimeError("fallo simulado")
        with engine.connect() as connection:
            assert connection.execute(text("SELECT COUNT(*) FROM sample")).scalar_one() == 0
    finally:
        engine.dispose()
