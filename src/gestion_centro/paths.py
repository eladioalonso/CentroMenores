"""Resolución de rutas para el despliegue portable."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DataPaths:
    """Rutas persistentes de la aplicación."""

    root: Path
    data: Path
    documents: Path
    images: Path
    backups: Path
    logs: Path
    database: Path


def application_root() -> Path:
    """Devuelve la carpeta raíz portable o la raíz del proyecto en desarrollo."""
    override = os.environ.get("CENTRO_DATOS_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2] / ".centro_datos"


def data_paths(root: Path | None = None) -> DataPaths:
    """Construye las rutas sin crear carpetas ni escribir en disco."""
    base = (root or application_root()).resolve()
    data = base / "data"
    return DataPaths(
        root=base,
        data=data,
        documents=data / "documentos",
        images=data / "imagenes",
        backups=data / "backups",
        logs=base / "logs",
        database=data / "centro.db",
    )


def ensure_data_directories(paths: DataPaths) -> None:
    """Crea únicamente las carpetas operativas necesarias."""
    for directory in (paths.data, paths.documents, paths.images, paths.backups, paths.logs):
        directory.mkdir(parents=True, exist_ok=True)
