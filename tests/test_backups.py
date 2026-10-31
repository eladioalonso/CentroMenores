import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

from gestion_centro.paths import data_paths, ensure_data_directories
from gestion_centro.persistence.backups import create_backup, verify_backup, sync_pending_backups


def prepare_paths(tmp_path):
    paths = data_paths(tmp_path)
    ensure_data_directories(paths)
    with sqlite3.connect(paths.database) as connection:
        connection.execute("CREATE TABLE sample (value TEXT)")
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
