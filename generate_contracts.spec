# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_all

project_dir = Path.cwd()
icon_file = project_dir / "app.ico"
version_file = project_dir / "version_info.txt"
flet_datas, flet_binaries, flet_hiddenimports = collect_all("flet")
desktop_datas, desktop_binaries, desktop_hiddenimports = collect_all("flet_desktop")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=flet_binaries + desktop_binaries,
    datas=flet_datas + desktop_datas,
    hiddenimports=flet_hiddenimports + desktop_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='合同批量生成器',
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
