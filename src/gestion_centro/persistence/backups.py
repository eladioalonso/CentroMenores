"""Copias de seguridad verificables de la carpeta portable."""
from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from gestion_centro.paths import DataPaths, ensure_data_directories


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_archive_name(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts and "\\" not in name


def verify_backup(archive: Path) -> dict:
    """Comprueba estructura, hashes y la integridad SQLite sin extraer el backup."""
    if not archive.is_file():
        raise FileNotFoundError(archive)
    with zipfile.ZipFile(archive, "r") as bundle:
        names = bundle.namelist()
        if any(not _safe_archive_name(name) for name in names):
            raise ValueError("El backup contiene rutas no seguras")
        if "manifest.json" not in names or "database/centro.db" not in names:
            raise ValueError("El backup está incompleto")
        manifest = json.loads(bundle.read("manifest.json"))
        for name, expected in manifest["files"].items():
            if name not in names or hashlib.sha256(bundle.read(name)).hexdigest() != expected:
                raise ValueError(f"Integridad incorrecta en {name}")
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp:
            temp.write(bundle.read("database/centro.db"))
            temp_path = Path(temp.name)
        try:
            with sqlite3.connect(temp_path) as connection:
                result = connection.execute("PRAGMA integrity_check").fetchone()[0]
                if result != "ok":
                    raise ValueError("La base de datos del backup no supera integrity_check")
        finally:
            temp_path.unlink(missing_ok=True)
        return manifest


def create_backup(paths: DataPaths, *, kind: str = "manual",
                  external_root: Path | None = None,
                  now: datetime | None = None, keep_daily: int = 30) -> Path:
    """Crea snapshot SQLite coherente y empaqueta documentos e imágenes."""
    if kind not in {"manual", "daily", "pre_operation"}:
        raise ValueError("Tipo de backup no válido")
    ensure_data_directories(paths)
    if not paths.database.is_file():
        raise FileNotFoundError("No existe la base de datos")
    moment = now or datetime.now(timezone.utc)
    stamp = moment.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = paths.backups / f"{kind}-{stamp}.zip"
    with tempfile.TemporaryDirectory(prefix="centro-backup-") as temp_dir:
        snapshot = Path(temp_dir) / "centro.db"
        source = sqlite3.connect(paths.database)
        destination = sqlite3.connect(snapshot)
        try:
            source.backup(destination)
            check = destination.execute("PRAGMA integrity_check").fetchone()[0]
            if check != "ok":
                raise ValueError("La base de datos no supera integrity_check")
        finally:
            destination.close()
            source.close()
        files: dict[str, str] = {}
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
            bundle.write(snapshot, "database/centro.db")
            files["database/centro.db"] = _sha256(snapshot)
            for label, root in (("documents", paths.documents), ("images", paths.images)):
                if root.exists():
                    for file in sorted(p for p in root.rglob("*") if p.is_file()):
                        name = f"{label}/{file.relative_to(root).as_posix()}"
                        if not _safe_archive_name(name):
                            raise ValueError("Ruta de archivo no segura")
                        bundle.write(file, name)
                        files[name] = _sha256(file)
            manifest = {
                "format": 1, "kind": kind, "created_at": moment.astimezone(timezone.utc).isoformat(),
                "files": files,
            }
            bundle.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    verify_backup(target)
    if external_root is not None:
        try:
            external_root.mkdir(parents=True, exist_ok=True)
            external_target = external_root / target.name
            shutil.copy2(target, external_target)
            verify_backup(external_target)
        except OSError:
            _mark_pending(paths, target)
    else:
        _mark_pending(paths, target)
    if kind == "daily":
        daily = sorted(paths.backups.glob("daily-*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in daily[keep_daily:]:
            old.unlink(missing_ok=True)
    return target


def _mark_pending(paths: DataPaths, archive: Path) -> None:
    pending = paths.backups / "external-pending.json"
    entries = []
    if pending.exists():
        try:
            entries = json.loads(pending.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            entries = []
    if archive.name not in entries:
        entries.append(archive.name)
    pending.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def sync_pending_backups(paths: DataPaths, external_root: Path) -> list[Path]:
    """Copia al USB las copias pendientes y verifica cada destino."""
    pending = paths.backups / "external-pending.json"
    if not pending.exists():
        return []
    entries = json.loads(pending.read_text(encoding="utf-8"))
    external_root.mkdir(parents=True, exist_ok=True)
    completed = []
    remaining = []
    for name in entries:
        if Path(name).name != name:
            raise ValueError("Nombre de backup pendiente no válido")
        source = paths.backups / name
        if not source.is_file():
            remaining.append(name)
            continue
        target = external_root / name
        shutil.copy2(source, target)
        verify_backup(target)
        completed.append(target)
    pending.write_text(json.dumps(remaining, ensure_ascii=False, indent=2), encoding="utf-8")
    return completed
