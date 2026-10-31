from sqlalchemy import create_engine, inspect

from gestion_centro.persistence.migrations import upgrade_database


def test_upgrade_creates_versioned_auth_schema(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    upgrade_database(engine)
    inspector = inspect(engine)
    assert {"professionals", "user_accounts", "access_audit", "alembic_version", "minors", "stays", "events", "event_stay_links", "diary_days", "diary_entries", "diary_entry_stay_links", "incidents", "incident_participants", "agenda_items", "agenda_item_stay_links"} <= set(inspector.get_table_names())
    engine.dispose()


def test_migration_root_uses_pyinstaller_bundle_when_frozen(monkeypatch, tmp_path):
    import sys
    from gestion_centro.persistence.migrations import migration_root

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert migration_root() == tmp_path
