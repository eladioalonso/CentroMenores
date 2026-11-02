"""Inicialización versionada del esquema local mediante Alembic."""

import logging.config  # noqa: F401 - fuerza su inclusión en el ejecutable PyInstaller
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Engine


def migration_root() -> Path:
    # En PyInstaller --onedir, los recursos se incluyen en _internal (sys._MEIPASS).
    if getattr(sys, "frozen", False):
        bundle_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        return bundle_root
    return Path(__file__).resolve().parents[3]


def upgrade_database(engine: Engine) -> None:
    resource_root = migration_root()
    ini_path = resource_root / "alembic.ini"
    migrations_path = resource_root / "migrations"
    if not ini_path.is_file() or not migrations_path.is_dir():
        raise RuntimeError(
            "No se encuentran los archivos de migración. La distribución portable "
            "debe incluir alembic.ini y la carpeta migrations."
        )
    config = Config(str(ini_path))
    config.set_main_option("script_location", str(migrations_path).replace("%", "%%"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
