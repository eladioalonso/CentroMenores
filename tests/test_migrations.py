from datetime import date, datetime, timezone
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

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
    minor_columns = {column["name"] for column in inspector.get_columns("minors")}
    assert "internal_code" in minor_columns  # clave técnica heredada, no visible en la interfaz
    assert "nif_nie" in minor_columns
    minor_indexes = {item["name"]: item for item in inspector.get_indexes("minors")}
    assert minor_indexes["uq_minors_nif_nie"]["unique"] == 1
    user_account_columns = {column["name"] for column in inspector.get_columns("user_accounts")}
    assert "health_access" in user_account_columns
    with engine.connect() as connection:
        health_default = connection.exec_driver_sql(
            "SELECT dflt_value FROM pragma_table_info('user_accounts') WHERE name='health_access'"
        ).scalar_one()
    assert health_default in ("0", "false", "FALSE")
    health_profile_columns = {column["name"] for column in inspector.get_columns("health_profiles")}
    assert {
        "cip", "health_center", "physician", "nurse",
        "health_card_expires_on", "clinical_history",
    } <= health_profile_columns
    health_version_columns = {
        column["name"]: column for column in inspector.get_columns("health_profile_versions")
    }
    assert health_version_columns["changed_by_account_id"]["nullable"] is True
    vaccine_record_columns = {column["name"] for column in inspector.get_columns("vaccine_records")}
    assert {
        "calendar_item_id", "manufacturer", "product_name", "batch_number",
        "administration_center", "administering_professional", "source_document_id",
    } <= vaccine_record_columns
    with engine.connect() as connection:
        triggers = {
            row[0] for row in connection.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='trigger'"
            ).all()
        }
    assert {
        "trg_vaccine_record_calendar_insert",
        "trg_vaccine_record_calendar_update",
        "trg_vaccine_calendar_item_delete",
    } <= triggers
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
        "vaccine_calendar_items", "vaccine_dose_reviews", "incident_reports",
        "incident_report_versions", "incident_report_entries", "vaccine_record_versions",
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



def test_legacy_incidents_are_migrated_into_diary_with_minor_links(tmp_path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'legacy.db').as_posix()}")
    root = Path(__file__).resolve().parents[1]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "0031_incident_report_version_metadata")

    now = datetime(2026, 6, 1, 12, tzinfo=timezone.utc)
    with engine.begin() as connection:
        connection.execute(text(
            "INSERT INTO professionals (id, display_name, active, created_at) "
            "VALUES ('professional-1', 'Educador histórico', 1, :now)"
        ), {"now": now})
        connection.execute(text(
            "INSERT INTO user_accounts (id, professional_id, username, password_hash, role, "
            "active, health_access, failed_attempts, created_at, updated_at) "
            "VALUES ('account-1', 'professional-1', 'historical', 'hash', 'educator', "
            "1, 0, 0, :now, :now)"
        ), {"now": now})
        connection.execute(text(
            "INSERT INTO minors (id, internal_code, given_names, family_names, active, "
            "cip, health_center, physician, nurse, health_card_expires_on, clinical_history, "
            "created_at, updated_at) VALUES ('minor-1', 'legacy-code', 'Caso', 'Histórico', "
            "1, 'CIP-LEGACY', 'Centro antiguo', 'Facultativo antiguo', 'Enfermería antigua', "
            "'2027-01-01', 'Antecedente histórico', :now, :now)"
        ), {"now": now})
        connection.execute(text(
            "INSERT INTO stays (id, minor_id, sequence_number, started_on, status, created_at) "
            "VALUES ('stay-1', 'minor-1', 1, '2026-01-01', 'active', :now)"
        ), {"now": now})
        connection.execute(text(
            "INSERT INTO health_profiles (id, minor_id, stay_id, allergies, relevant_conditions, "
            "emergency_instructions, updated_by_account_id, updated_by_name_snapshot, updated_at) "
            "VALUES ('profile-1', 'minor-1', 'stay-1', 'Alergia ficticia al polen', "
            "'Antecedente respiratorio ficticio', 'Instrucción de emergencia ficticia', "
            "'account-1', 'Educador histórico', :now)"
        ), {"now": now})
        connection.execute(text(
            "INSERT INTO diary_days (id, diary_date, created_at) "
            "VALUES ('day-1', '2026-06-01', :now)"
        ), {"now": now})
        connection.execute(text(
            "INSERT INTO incidents (id, diary_day_id, title, description, incident_type, "
            "severity, happened_at, recorded_at, status, author_account_id, "
            "author_name_snapshot) VALUES ('incident-1', 'day-1', 'Hecho histórico', "
            "'Descripción conservada', 'behavior', 'high', :now, :now, 'open', "
            "'account-1', 'Educador histórico')"
        ), {"now": now})
        connection.execute(text(
            "INSERT INTO diary_entries (id, diary_day_id, shift, category, content, "
            "happened_at, recorded_at, author_account_id, author_name_snapshot) "
            "VALUES ('entry-existing', 'day-1', 'morning', 'observation', "
            "'Hecho duplicado · ya anotado', :now, :now, 'account-1', 'Educador histórico')"
        ), {"now": now})
        connection.execute(text(
            "INSERT INTO incidents (id, diary_day_id, title, description, incident_type, "
            "severity, happened_at, recorded_at, status, author_account_id, "
            "author_name_snapshot) VALUES ('incident-duplicate', 'day-1', 'Hecho duplicado', "
            "'ya anotado', 'behavior', 'low', :now, :now, 'open', "
            "'account-1', 'Educador histórico')"
        ), {"now": now})
        connection.execute(text(
            "INSERT INTO incident_participants (id, incident_id, stay_id, role, "
            "minor_code_snapshot, minor_name_snapshot) VALUES ('participant-1', "
            "'incident-1', 'stay-1', 'affected', 'X1234567A', 'Caso Histórico')"
        ))

    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    with engine.connect() as connection:
        entry = connection.execute(text(
            "SELECT shift, category, content, author_name_snapshot "
            "FROM diary_entries WHERE content LIKE '%Hecho histórico%'"
        )).mappings().one()
        link = connection.execute(text(
            "SELECT stay_id, minor_code_snapshot, minor_name_snapshot "
            "FROM diary_entry_stay_links WHERE entry_id = ("
            "SELECT id FROM diary_entries WHERE content LIKE '%Hecho histórico%')"
        )).mappings().one()
        health = connection.execute(text(
            "SELECT cip, health_center, physician, nurse, health_card_expires_on, clinical_history "
            "FROM health_profiles WHERE minor_id='minor-1'"
        )).mappings().one()
        profile = connection.execute(text(
            "SELECT id, allergies, relevant_conditions, emergency_instructions "
            "FROM health_profiles WHERE minor_id='minor-1'"
        )).mappings().one()
        health_version_detail = connection.execute(text(
            "SELECT old_values, new_values FROM health_profile_versions "
            "WHERE minor_id='minor-1' ORDER BY changed_at DESC, id DESC LIMIT 1"
        )).mappings().one()
        health_version = connection.execute(text(
            "SELECT changed_by_account_id, changed_by_name_snapshot, new_values "
            "FROM health_profile_versions WHERE minor_id='minor-1'"
        )).mappings().one()
        diary_count = connection.execute(text(
            "SELECT COUNT(*) FROM diary_entries WHERE diary_day_id='day-1'"
        )).scalar_one()
    assert entry["shift"] == "unspecified"
    assert entry["category"] == "negative"
    assert "Descripción conservada" in entry["content"]
    assert entry["author_name_snapshot"] == "Educador histórico"
    assert dict(link) == {
        "stay_id": "stay-1",
        "minor_code_snapshot": "X1234567A",
        "minor_name_snapshot": "Caso Histórico",
    }
    assert health["cip"] == "CIP-LEGACY"
    assert health["health_center"] == "Centro antiguo"
    assert health["physician"] == "Facultativo antiguo"
    assert health["nurse"] == "Enfermería antigua"
    assert health["health_card_expires_on"] == "2027-01-01"
    assert health["clinical_history"] == "Antecedente histórico"
    assert dict(profile) == {
        "id": "profile-1",
        "allergies": "Alergia ficticia al polen",
        "relevant_conditions": "Antecedente respiratorio ficticio",
        "emergency_instructions": "Instrucción de emergencia ficticia",
    }
    assert "Alergia ficticia al polen" in health_version_detail["old_values"]
    assert "CIP-LEGACY" in health_version_detail["new_values"]
    assert health_version["changed_by_account_id"] is None
    assert health_version["changed_by_name_snapshot"] == "Migración histórica"
    assert "CIP-LEGACY" in health_version["new_values"]
    assert diary_count == 2
    engine.dispose()
