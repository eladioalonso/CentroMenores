from pathlib import Path

from gestion_centro.paths import data_paths, ensure_data_directories


def test_data_paths_are_inside_portable_root(tmp_path: Path) -> None:
    paths = data_paths(tmp_path)
    assert paths.database == tmp_path / "data" / "centro.db"
    assert paths.documents == tmp_path / "data" / "documentos"
    assert paths.images == tmp_path / "data" / "imagenes"
    assert paths.backups == tmp_path / "data" / "backups"
    assert paths.logs == tmp_path / "logs"


def test_directory_creation_is_explicit(tmp_path: Path) -> None:
    paths = data_paths(tmp_path)
    assert not paths.data.exists()
    ensure_data_directories(paths)
    assert paths.data.is_dir()
    assert paths.documents.is_dir()
    assert paths.images.is_dir()
    assert paths.backups.is_dir()
    assert paths.logs.is_dir()
