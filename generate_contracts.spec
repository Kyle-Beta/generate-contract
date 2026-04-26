# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files

project_dir = Path.cwd()
icon_file = project_dir / "app.ico"
version_file = project_dir / "version_info.txt"
desktop_datas = collect_data_files("flet_desktop")
flet_datas, flet_binaries, flet_hiddenimports = collect_all("flet")
docx_datas = collect_data_files("docx")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=flet_binaries,
    datas=desktop_datas + flet_datas + docx_datas,
    hiddenimports=flet_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="contract-generator",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_file) if icon_file.exists() else None,
    version=str(version_file) if version_file.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="contract-generator",
)
