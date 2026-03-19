# -*- mode: python ; coding: utf-8 -*-
"""
AHDUNYI Client - Final Clean Build Spec
100% pure UI Automation architecture

NOTE: Analysis, PYZ, EXE, COLLECT, SPECPATH are injected by PyInstaller
automatically - never import them manually in a .spec file.
"""

import os
import sys

# ====================  Path Configuration  ====================
# SPECPATH is injected by PyInstaller - it equals the directory containing
# this .spec file. Never use __file__ inside a spec.
spec_dir = SPECPATH  # noqa: F821
project_root = os.path.dirname(spec_dir)

print("[INFO] spec_dir    : " + spec_dir)
print("[INFO] project_root: " + project_root)
print("[INFO] python      : " + sys.executable)

# ====================  Entry point  ====================
main_script = os.path.join(spec_dir, 'client_launcher.py')
if not os.path.exists(main_script):
    print("[ERROR] Main script not found: " + main_script)
    sys.exit(1)

print("[INFO] main_script : " + main_script)

# ====================  Data files  ====================
example_cfg = os.path.join(spec_dir, 'client_config.example.json')
datas = []
if os.path.exists(example_cfg):
    datas.append((example_cfg, '.'))

# ====================  Hidden imports  ====================
hiddenimports = [
    # System / monitoring
    'psutil',
    'uiautomation',
    # PyQt6
    'PyQt6',
    'PyQt6.QtWidgets',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.sip',
    # Network
    'requests',
    # COM (Windows UI Automation)
    'comtypes',
    'comtypes.client',
    # Misc
    'cachetools',
    # Client UI modules (ensure they are bundled)
    'app.ui.login_window',
    'app.ui.supervisor_dashboard',
    'utils.room_monitor',
    'client_config',
]

# ====================  Excludes  ====================
excludes = [
    'tkinter',
    'test',
    'unittest',
    'pytest',
    'doctest',
    'numpy',
    'pandas',
    'matplotlib',
    'scipy',
    'sklearn',
    'torch',
    'tensorflow',
    'keras',
    'PIL',
    'PIL.Image',
    'opencv',
    'cv2',
    'setuptools',
    'pip',
    'wheel',
    'distutils',
]

# ====================  Analysis  ====================
a = Analysis(
    [main_script],
    pathex=[spec_dir],
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
    optimize=0,
)

# ====================  PYZ  ====================
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# ====================  EXE  ====================
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AHDUNYI_Audit_Client',
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
)

# ====================  COLLECT  ====================
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AHDUNYI_Audit_Client',
)

print("=" * 60)
print("[OK] Spec configuration complete")
print("     output      : AHDUNYI_Audit_Client")
print("     console     : off (GUI app)")
print("     hidden imps : " + str(len(hiddenimports)))
print("     excludes    : " + str(len(excludes)))
print("     arch        : 100% pure UI Automation")
print("=" * 60)
