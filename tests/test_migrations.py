from sqlalchemy import create_engine, inspect

from gestion_centro.persistence.migrations import upgrade_database


def test_upgrade_creates_versioned_auth_schema(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    upgrade_database(engine)
    inspector = inspect(engine)
    assert {"professionals", "user_accounts", "access_audit", "alembic_version", "minors", "stays", "events", "event_stay_links", "diary_days", "diary_entries", "diary_entry_stay_links", "incidents", "incident_participants", "agenda_items", "agenda_item_stay_links", "communications", "communication_contributions", "education_goals", "education_updates", "school_placements", "school_records", "health_profiles", "medication_plans", "medication_administrations", "vaccine_records", "personal_documents", "authorizations", "outings", "outing_stays", "outing_authorizations", "vaccine_calendar_editions", "vaccine_calendar_items", "vaccine_dose_reviews"} <= set(inspector.get_table_names())
    with engine.connect() as connection:
        editions = connection.exec_driver_sql("SELECT jurisdiction, edition_code, status FROM vaccine_calendar_editions").all()
        items = connection.exec_driver_sql("SELECT vaccine_code, category FROM vaccine_calendar_items").all()
    assert ("Melilla", "2026-infantil", "documentary") in editions
    assert len(items) >= 35
    assert any(code == "VRS-MAB" and category == "passive_immunization" for code, category in items)
    engine.dispose()


def test_migration_root_uses_pyinstaller_bundle_when_frozen(monkeypatch, tmp_path):
    import sys
    from gestion_centro.persistence.migrations import migration_root

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert migration_root() == tmp_path
