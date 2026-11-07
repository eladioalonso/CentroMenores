"""Copias de seguridad verificables de la carpeta portable."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import stat
import tempfile
import zipfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from uuid import uuid4

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
        infos = bundle.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise ValueError("El backup contiene rutas duplicadas")
        if any(not _safe_archive_name(name) for name in names):
            raise ValueError("El backup contiene rutas no seguras")
        if bundle.testzip() is not None:
            raise ValueError("El ZIP contiene un miembro dañado")
        if "manifest.json" not in names or "database/centro.db" not in names:
            raise ValueError("El backup está incompleto")
        try:
            manifest = json.loads(bundle.read("manifest.json"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("El manifiesto del backup no es válido") from exc
        if not isinstance(manifest, dict) or manifest.get("format") != 1:
            raise ValueError("Formato de manifiesto no compatible")
        files = manifest.get("files")
        if not isinstance(files, dict) or "database/centro.db" not in files:
            raise ValueError("El manifiesto no contiene la base de datos")
        expected_names = set(files) | {"manifest.json"}
        if set(names) != expected_names:
            raise ValueError("El contenido del ZIP no coincide con el manifiesto")
        for info in infos:
            mode = (info.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise ValueError("El backup contiene enlaces simbólicos")
            if info.flag_bits & 0x1:
                raise ValueError("El backup contiene archivos cifrados no compatibles")
        for name, expected in files.items():
            if (not isinstance(name, str) or not _safe_archive_name(name)
                    or not isinstance(expected, str)):
                raise ValueError(f"Entrada no válida en el manifiesto: {name}")
            digest = hashlib.sha256()
            with bundle.open(name, "r") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != expected:
                raise ValueError(f"Integridad incorrecta en {name}")
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp:
            with bundle.open("database/centro.db", "r") as source:
                shutil.copyfileobj(source, temp, length=1024 * 1024)
            temp_path = Path(temp.name)
        connection = sqlite3.connect(temp_path)
        try:
            result = connection.execute("PRAGMA integrity_check").fetchone()[0]
            if result != "ok":
                raise ValueError("La base de datos del backup no supera integrity_check")
        finally:
            connection.close()
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
    target = paths.backups / f"{kind}-{stamp}-{uuid4().hex[:8]}.zip"
    temporary_archive = paths.backups / f".{target.name}.tmp"
    try:
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
            with zipfile.ZipFile(temporary_archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
                bundle.write(snapshot, "database/centro.db")
                files["database/centro.db"] = _sha256(snapshot)
                for label, root in (("documents", paths.documents), ("images", paths.images)):
                    if root.is_symlink():
                        raise ValueError(f"La carpeta {label} no puede ser un enlace simbólico")
                    if root.exists():
                        for file in sorted(root.rglob("*")):
                            if file.is_symlink():
                                raise ValueError(f"Se ha detectado un enlace simbólico en {label}")
                            if not file.is_file():
                                continue
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
        try:
            verify_backup(temporary_archive)
            os.replace(temporary_archive, target)
        except Exception:
            temporary_archive.unlink(missing_ok=True)
            raise
    
    except Exception:
        temporary_archive.unlink(missing_ok=True)
        raise
    if external_root is not None:
        external_temporary = external_root / f".{target.name}.tmp"
        try:
            external_root.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, external_temporary)
            verify_backup(external_temporary)
            os.replace(external_temporary, external_root / target.name)
        except (OSError, ValueError):
            external_temporary.unlink(missing_ok=True)
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


def restore_backup(paths: DataPaths, archive: Path) -> Path:
    """Restaura un conjunto completo tras validar y conservar el estado actual.

    Conserva los registros de auditoría actuales que no existan en la copia.
    Rechaza copias cuyo esquema no sea compatible con la base instalada.
    """
    manifest = verify_backup(archive)
    ensure_data_directories(paths)
    # La copia previa es obligatoria y queda verificada antes de tocar nada.
    pre_restore = create_backup(paths, kind="pre_operation")
    with tempfile.TemporaryDirectory(prefix="centro-restore-", dir=paths.root) as temp_dir:
        stage = Path(temp_dir)
        with zipfile.ZipFile(archive, "r") as bundle:
            for info in bundle.infolist():
                if not _safe_archive_name(info.filename):
                    raise ValueError("El archivo contiene rutas no seguras")
                if info.is_dir():
                    continue
                target = stage.joinpath(*PurePosixPath(info.filename).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(info) as source, target.open("wb") as destination:
                    shutil.copyfileobj(source, destination)

        staged_db = stage / "database" / "centro.db"
        if not staged_db.is_file():
            raise ValueError("La copia no contiene la base de datos")
        with closing(sqlite3.connect(staged_db)) as restored, closing(sqlite3.connect(paths.database)) as current:
            restored_check = restored.execute("PRAGMA integrity_check").fetchone()[0]
            if restored_check != "ok":
                raise ValueError("La base restaurada no supera integrity_check")
            current_tables = {r[0] for r in current.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            restored_tables = {r[0] for r in restored.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            if "alembic_version" not in current_tables or "alembic_version" not in restored_tables:
                raise ValueError("No se puede verificar la versión del esquema")
            current_version = current.execute("SELECT version_num FROM alembic_version").fetchone()
            restored_version = restored.execute("SELECT version_num FROM alembic_version").fetchone()
            if not current_version or not restored_version or current_version[0] != restored_version[0]:
                raise ValueError("La copia tiene una versión de esquema distinta. Restauración cancelada.")
            if "access_audit" not in current_tables or "access_audit" not in restored_tables:
                raise ValueError("No se puede garantizar la conservación de auditoría")
            current_cols = {r[1] for r in current.execute("PRAGMA table_info(access_audit)")}
            restored_cols = {r[1] for r in restored.execute("PRAGMA table_info(access_audit)")}
            required = {"id", "account_id", "username_snapshot", "event", "occurred_at", "details"}
            if not required.issubset(current_cols) or not required.issubset(restored_cols):
                raise ValueError("La estructura de auditoría no es compatible")
            # Las referencias de cuenta inexistentes se convierten en NULL,
            # conservando usuario, evento, fecha y detalle originales.
            restored.execute("ATTACH DATABASE ? AS current_db", (str(paths.database),))
            restored.execute(
                """INSERT OR IGNORE INTO access_audit
                (id, account_id, username_snapshot, event, occurred_at, details)
                SELECT a.id,
                    CASE WHEN a.account_id IS NOT NULL AND EXISTS
                        (SELECT 1 FROM user_accounts u WHERE u.id=a.account_id)
                    THEN a.account_id ELSE NULL END,
                    a.username_snapshot, a.event, a.occurred_at, a.details
                FROM current_db.access_audit a"""
            )
            restored.commit()
            foreign_errors = restored.execute("PRAGMA foreign_key_check").fetchall()
            if foreign_errors:
                raise ValueError("La base restaurada contiene relaciones inválidas")
            restored.execute("DETACH DATABASE current_db")

        # Prepara directorios completos antes de sustituirlos.
        staged_docs = stage / "documents"
        staged_images = stage / "images"
        staged_docs.mkdir(exist_ok=True)
        staged_images.mkdir(exist_ok=True)
        backup_hold = stage / "previous"
        backup_hold.mkdir()
        operations = [
            (paths.documents, backup_hold / "documents", staged_docs),
            (paths.images, backup_hold / "images", staged_images),
        ]
        moved = []
        installed = []
        try:
            for live, old, new in operations:
                if live.exists():
                    os.replace(live, old)
                    moved.append((live, old))
                os.replace(new, live)
                installed.append(live)
            staged_live_db = stage / "database" / "restore.db"
            os.replace(staged_db, staged_live_db)
            os.replace(staged_live_db, paths.database)
        except Exception as original_error:
            rollback_errors = []
            for live in reversed(installed):
                try:
                    if live.is_dir():
                        shutil.rmtree(live)
                    elif live.exists():
                        live.unlink()
                except OSError as rollback_error:
                    rollback_errors.append(f"{live}: {rollback_error}")
            for live, old in reversed(moved):
                try:
                    if old.exists():
                        os.replace(old, live)
                except OSError as rollback_error:
                    rollback_errors.append(f"{live}: {rollback_error}")
            if rollback_errors:
                raise RuntimeError(
                    "Falló la restauración y también parte de la reversión. "
                    "No vuelvas a iniciar la aplicación; conserva la copia previa "
                    f"{pre_restore.name} y solicita recuperación técnica. "
                    + "; ".join(rollback_errors)
                ) from original_error
            raise
    return pre_restore
