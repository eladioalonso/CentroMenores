import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

from gestion_centro.paths import data_paths, ensure_data_directories
from gestion_centro.persistence.backups import create_backup, verify_backup, sync_pending_backups, restore_backup


def prepare_paths(tmp_path):
    paths = data_paths(tmp_path)
    ensure_data_directories(paths)
    with sqlite3.connect(paths.database) as connection:
        connection.execute("CREATE TABLE sample (value TEXT)")
        connection.execute("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)")
        connection.execute("INSERT INTO alembic_version VALUES ('test-version')")
        connection.execute("CREATE TABLE user_accounts (id TEXT PRIMARY KEY)")
        connection.execute("""CREATE TABLE access_audit (
            id TEXT PRIMARY KEY, account_id TEXT NULL REFERENCES user_accounts(id),
            username_snapshot TEXT NOT NULL, event TEXT NOT NULL,
            occurred_at TEXT NOT NULL, details TEXT NULL)""")
        connection.execute("INSERT INTO sample VALUES ('fictitious')")
    (paths.documents / "sample.pdf").write_bytes(b"fake document bytes")
    (paths.images / "sample.png").write_bytes(b"fake image bytes")
    return paths


def test_backup_contains_database_and_files_and_verifies(tmp_path):
    paths = prepare_paths(tmp_path / "portable")
    archive = create_backup(paths, kind="manual",
        now=datetime(2026, 5, 1, tzinfo=timezone.utc))
    manifest = verify_backup(archive)
    assert manifest["kind"] == "manual"
    assert "database/centro.db" in manifest["files"]
    assert "documents/sample.pdf" in manifest["files"]
    assert "images/sample.png" in manifest["files"]


def test_backup_marks_external_pending_and_syncs_when_usb_available(tmp_path):
    paths = prepare_paths(tmp_path / "portable")
    archive = create_backup(paths, kind="manual",
        now=datetime(2026, 5, 2, tzinfo=timezone.utc))
    pending = json.loads((paths.backups / "external-pending.json").read_text(encoding="utf-8"))
    assert archive.name in pending
    external = tmp_path / "usb"
    copied = sync_pending_backups(paths, external)
    assert len(copied) == 1
    assert verify_backup(copied[0])["kind"] == "manual"
    assert json.loads((paths.backups / "external-pending.json").read_text(encoding="utf-8")) == []


def test_backup_detects_modified_archive(tmp_path):
    paths = prepare_paths(tmp_path / "portable")
    archive = create_backup(paths, kind="manual",
        now=datetime(2026, 5, 3, tzinfo=timezone.utc))
    import zipfile
    tampered = tmp_path / "tampered.zip"
    with zipfile.ZipFile(archive, "r") as src, zipfile.ZipFile(tampered, "w") as dst:
        for item in src.infolist():
            payload = src.read(item.filename)
            if item.filename == "documents/sample.pdf":
                payload += b"tampered"
            dst.writestr(item, payload)
    import pytest
    with pytest.raises(ValueError, match="Integridad"):
        verify_backup(tampered)


def test_restore_requires_matching_schema_and_preserves_current_audit(tmp_path):
    paths = prepare_paths(tmp_path / "portable")
    archive = create_backup(paths, kind="manual",
        now=datetime(2026, 5, 4, tzinfo=timezone.utc))
    (paths.documents / "sample.pdf").write_bytes(b"changed after backup")
    with sqlite3.connect(paths.database) as connection:
        connection.execute(
            "INSERT INTO access_audit VALUES (?, NULL, ?, ?, ?, ?)",
            ("audit-after-backup", "educador-ficticio", "test_event",
             "2026-05-04T12:00:00+00:00", "registro posterior")
        )
    previous = restore_backup(paths, archive)
    assert previous.is_file()
    assert (paths.documents / "sample.pdf").read_bytes() == b"fake document bytes"
    with sqlite3.connect(paths.database) as connection:
        row = connection.execute(
            "SELECT username_snapshot, event, details FROM access_audit WHERE id=?",
            ("audit-after-backup",)
        ).fetchone()
    assert row == ("educador-ficticio", "test_event", "registro posterior")


def test_restore_refuses_different_schema_without_replacing_live_database(tmp_path):
    paths = prepare_paths(tmp_path / "portable")
    archive = create_backup(paths, kind="manual",
        now=datetime(2026, 5, 5, tzinfo=timezone.utc))
    with sqlite3.connect(paths.database) as connection:
        connection.execute("UPDATE alembic_version SET version_num='newer-version'")
    before = (paths.documents / "sample.pdf").read_bytes()
    import pytest
    with pytest.raises(ValueError, match="versión de esquema"):
        restore_backup(paths, archive)
    assert (paths.documents / "sample.pdf").read_bytes() == before
