# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH)
datas = [
    (str(ROOT / "alembic.ini"), "."),
    (str(ROOT / "migrations"), "migrations"),
]
hiddenimports = collect_submodules("alembic")

a = Analysis(
    [str(ROOT / "src" / "gestion_centro" / "__main__.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True,
    name="GestionCentro", debug=False, bootloader_ignore_signals=False,
    strip=False, upx=False, console=False,
)
coll = COLLECT(
    exe, a.binaries, a.datas, strip=False, upx=False,
    name="GestionCentro",
)
