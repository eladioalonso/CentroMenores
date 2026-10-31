"""Diagnóstico técnico local sin extraer ni mostrar contenido personal."""
from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from gestion_centro.persistence.backups import verify_backup


def run_diagnostics(paths) -> dict:
    checks: list[dict[str, str]] = []
    for label, folder in (
        ("Raíz portable", paths.root), ("Base de datos", paths.database.parent),
        ("Documentos", paths.documents), ("Imágenes", paths.images),
        ("Copias", paths.backups), ("Registros", paths.logs),
    ):
        checks.append({
            "name": label,
            "status": "OK" if folder.exists() and folder.is_dir() else "ERROR",
            "detail": "Carpeta disponible" if folder.exists() and folder.is_dir() else "Carpeta ausente",
        })

    if paths.database.is_file():
        try:
            with sqlite3.connect(paths.database) as connection:
                integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
                foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
            checks.append({
                "name": "Integridad SQLite",
                "status": "OK" if integrity == "ok" and not foreign_keys else "ERROR",
                "detail": "Integridad correcta y sin relaciones huérfanas" if integrity == "ok" and not foreign_keys
                          else f"integrity_check={integrity}; relaciones con errores={len(foreign_keys)}",
            })
        except sqlite3.Error as exc:
            checks.append({"name": "Integridad SQLite", "status": "ERROR", "detail": str(exc)})
    else:
        checks.append({"name": "Integridad SQLite", "status": "ERROR", "detail": "Base de datos ausente"})

    archives = sorted(paths.backups.glob("*.zip"), key=lambda item: item.stat().st_mtime, reverse=True)
    valid = 0
    invalid = 0
    for archive in archives:
        try:
            verify_backup(archive)
            valid += 1
        except (OSError, ValueError, KeyError):
            invalid += 1
    checks.append({
        "name": "Copias verificables",
        "status": "OK" if archives and invalid == 0 else ("AVISO" if invalid or not archives else "OK"),
        "detail": f"{valid} válidas; {invalid} no válidas; {len(archives)} en total",
    })

    pending_file = paths.backups / "external-pending.json"
    pending = 0
    if pending_file.exists():
        try:
            import json
            pending = len(json.loads(pending_file.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pending = -1
    checks.append({
        "name": "Copia externa pendiente",
        "status": "AVISO" if pending else "OK",
        "detail": "No hay copias pendientes" if pending == 0 else
                  ("No se pudo leer la cola de copias" if pending < 0 else f"{pending} copias pendientes de USB"),
    })

    usage = shutil.disk_usage(paths.root)
    total_files = 0
    total_bytes = 0
    largest_bytes = 0
    for root in (paths.documents, paths.images):
        if root.exists():
            for item in root.rglob("*"):
                if item.is_file():
                    try:
                        size = item.stat().st_size
                    except OSError:
                        continue
                    total_files += 1
                    total_bytes += size
                    largest_bytes = max(largest_bytes, size)
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "disk_total_bytes": usage.total,
        "disk_free_bytes": usage.free,
        "document_file_count": total_files,
        "document_bytes": total_bytes,
        "largest_attachment_bytes": largest_bytes,
        "backup_count": len(archives),
        "valid_backup_count": valid,
        "invalid_backup_count": invalid,
        "pending_external_count": pending,
    }
