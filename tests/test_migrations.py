from sqlalchemy import create_engine, inspect

from gestion_centro.persistence.migrations import upgrade_database


def test_upgrade_creates_versioned_auth_schema(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    upgrade_database(engine)
    inspector = inspect(engine)
    assert {"professionals", "user_accounts", "access_audit", "alembic_version"} <= set(inspector.get_table_names())
    engine.dispose()
