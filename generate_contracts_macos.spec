# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

project_dir = Path.cwd()
icon_file = project_dir / "app.icns"
bundle_version = (project_dir / "VERSION").read_text(encoding="utf-8").strip()
target_arch = os.environ.get("MACOS_TARGET_ARCH") or None
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
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=target_arch,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='合同批量生成器.app',
    icon=str(icon_file) if icon_file.exists() else None,
    bundle_identifier='com.kylebeta.contract-generator',
    version=bundle_version,
    info_plist={
        'CFBundleName': '合同批量生成器',
        'CFBundleDisplayName': '合同批量生成器',
        'CFBundleShortVersionString': bundle_version,
        'CFBundleVersion': bundle_version,
        'NSHighResolutionCapable': 'True',
    },
)
