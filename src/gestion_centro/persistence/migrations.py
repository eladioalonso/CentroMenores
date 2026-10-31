"""Inicialización versionada del esquema local mediante Alembic."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Engine


def upgrade_database(engine: Engine) -> None:
    project_root = Path(__file__).resolve().parents[3]
    ini_path = project_root / "alembic.ini"
    migrations_path = project_root / "migrations"
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
