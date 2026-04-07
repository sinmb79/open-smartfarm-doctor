# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


root = Path(__file__).parent
icon_path = root / "assets" / "open-smartfarm-doctor.ico"
datas = [
    ("models", "models"),
    ("data", "data"),
    ("i18n", "i18n"),
    ("engine\\web\\templates", "engine\\web\\templates"),
]
mosquitto_dir = root / "bin" / "mosquitto"
if mosquitto_dir.exists():
    datas.append(("bin\\mosquitto", "bin\\mosquitto"))


a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
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
    name="open-smartfarm-doctor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path.exists() else None,
)
