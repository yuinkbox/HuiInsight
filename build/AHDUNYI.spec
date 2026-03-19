# -*- mode: python ; coding: utf-8 -*-
"""
AHDUNYI Terminal PRO - PyInstaller spec.

Packs:
  - src/main.py            (entry point)
  - web_client/dist/**     (compiled Vue frontend)
  - config.json            (optional, if present)

Author : AHDUNYI
Version: 9.0.0
"""

import os
import sys
from pathlib import Path

SPEC_DIR = Path(SPECPATH)      # noqa: F821  injected by PyInstaller
PROJECT  = SPEC_DIR.parent

print("[SPEC] project root: " + str(PROJECT))
print("[SPEC] python      : " + sys.executable)

MAIN = str(PROJECT / "src" / "main.py")
assert os.path.exists(MAIN), "Entry point not found: " + MAIN

# Data files
datas = []
WEB_DIST = PROJECT / "web_client" / "dist"
if WEB_DIST.exists():
    datas.append((str(WEB_DIST), "web_client/dist"))
    print("[SPEC] web_client/dist included")
else:
    print("[WARN] web_client/dist missing - run npm run build first")

CFG = PROJECT / "config.json"
if CFG.exists():
    datas.append((str(CFG), "."))
    print("[SPEC] config.json included")

hiddenimports = [
    "PyQt6", "PyQt6.QtWidgets", "PyQt6.QtCore", "PyQt6.QtGui",
    "PyQt6.QtWebChannel", "PyQt6.QtWebEngineWidgets",
    "PyQt6.QtWebEngineCore", "PyQt6.sip",
    "psutil", "uiautomation", "comtypes", "comtypes.client",
    "requests", "urllib3", "urllib3.util.retry", "cachetools",
    "src.main", "src.config.settings",
    "src.utils.file_helper", "src.utils.network_client",
    "src.app.bridge.web_channel",
    "src.app.core.room_monitor", "src.app.core.behavior_analyzer",
    "src.app.ui.login_window", "src.app.ui.main_window",
]

excludes = [
    "tkinter", "unittest", "test", "pytest", "doctest",
    "numpy", "pandas", "matplotlib", "scipy", "sklearn",
    "torch", "tensorflow", "keras", "PIL", "cv2",
    "setuptools", "pip", "wheel", "distutils",
]

a = Analysis(        # noqa: F821
    [MAIN],
    pathex=[str(PROJECT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)  # noqa: F821

exe = EXE(            # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AHDUNYI_Terminal_PRO",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(       # noqa: F821
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AHDUNYI_Terminal_PRO",
)

print("[SPEC] done - hidden imports: " + str(len(hiddenimports)))
print("[SPEC] done - datas         : " + str(len(datas)))
