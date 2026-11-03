from sqlalchemy import create_engine, inspect

from gestion_centro.persistence.migrations import upgrade_database


def test_upgrade_creates_versioned_auth_schema(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    upgrade_database(engine)
    inspector = inspect(engine)
    assert not any(
        item.get("name") == "uq_vaccine_review_minor_item"
        for item in inspector.get_unique_constraints("vaccine_dose_reviews")
    )
    columns = {column["name"]: column for column in inspector.get_columns("vaccine_calendar_items")}
    assert columns["dose_label"]["type"].length == 80  # SQLite no aplica límites VARCHAR; el servicio valida 240.
    assert "entry_kind" in columns
    vaccine_record_columns = {column["name"] for column in inspector.get_columns("vaccine_records")}
    assert "calendar_item_id" in vaccine_record_columns
    assert any(\n        "calendar_item_id" in foreign_key["constrained_columns"]\n        and foreign_key["referred_table"] == "vaccine_calendar_items"\n        for foreign_key in inspector.get_foreign_keys("vaccine_records")\n    )
    assert {
        "professionals", "user_accounts", "access_audit", "alembic_version",
        "minors", "stays", "events", "event_stay_links", "diary_days",
        "diary_entries", "diary_entry_stay_links", "incidents",
        "incident_participants", "agenda_items", "agenda_item_stay_links",
        "communications", "communication_contributions", "education_goals",
        "education_updates", "school_placements", "school_records",
        "health_profiles", "medication_plans", "medication_administrations",
        "vaccine_records", "personal_documents", "authorizations", "outings",
        "outing_stays", "outing_authorizations", "vaccine_calendar_editions",
        "vaccine_calendar_items", "vaccine_dose_reviews",
    } <= set(inspector.get_table_names())
    with engine.connect() as connection:
        editions = connection.exec_driver_sql(
            "SELECT jurisdiction, edition_code, status FROM vaccine_calendar_editions"
        ).all()
        items = connection.exec_driver_sql(
            "SELECT vaccine_code, category FROM vaccine_calendar_items"
        ).all()
        accelerated_kinds = connection.exec_driver_sql(
            "SELECT DISTINCT entry_kind FROM vaccine_calendar_items "
            "WHERE vaccine_code LIKE 'ACC-%'"
        ).scalars().all()
        risk_schedule_kinds = connection.exec_driver_sql(
            "SELECT DISTINCT entry_kind FROM vaccine_calendar_items "
            "WHERE vaccine_code IN ('RISK-A-HB', 'RISK-I-TV', 'VPH-AD')"
        ).scalars().all()
        risk_single_kind = connection.exec_driver_sql(
            "SELECT entry_kind FROM vaccine_calendar_items WHERE vaccine_code = 'RISK-A-HIB'"
        ).scalar_one()
    assert ("Melilla", "2026-infantil", "documentary") in editions
    assert ("Melilla", "2026-adulto", "documentary") in editions
    assert ("Melilla", "2025-acelerado", "documentary") in editions
    assert ("SNS", "2026-riesgo-infantil", "documentary") in editions
    assert ("SNS", "2026-riesgo-adultos", "documentary") in editions
    assert len(items) >= 35
    assert any(code == "VRS-MAB" and category == "passive_immunization" for code, category in items)
    assert len([
        code for code, category in items
        if code in {"GRIPE-AD", "NEUMO-VNC20-65", "VRS-AD"}
    ]) == 3
    assert sum(category == "catch_up" for code, category in items) >= 20
    assert sum(category == "risk" for code, category in items) >= 20
    assert accelerated_kinds == ["schedule"]
    assert risk_schedule_kinds == ["schedule"]
    assert risk_single_kind == "dose"
    engine.dispose()


def test_migration_root_uses_pyinstaller_bundle_when_frozen(monkeypatch, tmp_path):
    import sys
    from gestion_centro.persistence.migrations import migration_root

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert migration_root() == tmp_path
