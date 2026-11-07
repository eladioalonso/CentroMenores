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

def test_diagnostics_counts_corrupt_archives_instead_of_aborting(tmp_path):
    paths = data_paths(tmp_path / "portable")
    ensure_data_directories(paths)
    with sqlite3.connect(paths.database) as connection:
        connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY)")
    (paths.backups / "broken.zip").write_bytes(b"not a zip archive")
    report = run_diagnostics(paths)
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["Copias verificables"]["status"] == "AVISO"
    assert "1 no válidas" in checks["Copias verificables"]["detail"]


def test_diagnostics_reports_malformed_pending_queue(tmp_path):
    paths = data_paths(tmp_path / "portable")
    ensure_data_directories(paths)
    with sqlite3.connect(paths.database) as connection:
        connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY)")
    (paths.backups / "external-pending.json").write_text(
        '{"not": "a list"}', encoding="utf-8")
    report = run_diagnostics(paths)
    checks = {item["name"]: item for item in report["checks"]}
    assert checks["Copia externa pendiente"]["status"] == "AVISO"
    assert "No se pudo leer" in checks["Copia externa pendiente"]["detail"]

