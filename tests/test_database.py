from pathlib import Path

from sqlalchemy import text

from gestion_centro.persistence.database import build_engine


def test_sqlite_pragmas_are_applied_per_connection(tmp_path: Path) -> None:
    engine = build_engine(tmp_path / "test.db")
    try:
        with engine.connect() as connection:
            assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
            assert connection.execute(text("PRAGMA synchronous")).scalar_one() == 2
            assert connection.execute(text("PRAGMA journal_mode")).scalar_one().lower() == "delete"
            assert connection.execute(text("PRAGMA busy_timeout")).scalar_one() == 5_000
    finally:
        engine.dispose()
