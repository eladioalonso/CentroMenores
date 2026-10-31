import sqlite3
from pathlib import Path

from gestion_centro.paths import data_paths, ensure_data_directories
from gestion_centro.persistence.diagnostics import run_diagnostics


def test_diagnostics_report_integrity_and_storage_without_personal_content(tmp_path):
    paths = data_paths(tmp_path / "portable")
    ensure_data_directories(paths)
    with sqlite3.connect(paths.database) as connection:
        connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY)")
        connection.execute("INSERT INTO sample DEFAULT VALUES")
    report = run_diagnostics(paths)
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["Integridad SQLite"]["status"] == "OK"
    assert report["document_file_count"] == 0
    assert report["document_bytes"] == 0
    assert "minors" not in str(report).lower()
    assert report["disk_free_bytes"] > 0
