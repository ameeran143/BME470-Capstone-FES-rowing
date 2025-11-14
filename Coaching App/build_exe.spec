# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for FES Rowing App
Alternative to build_exe.py - can be used with: pyinstaller build_exe.spec
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect data files
datas = [
    ('assets', 'assets'),
    ('compress.jpg', '.'),
    ('extend.jpg', '.'),
]

# Collect hidden imports
hiddenimports = [
    'wx',
    'wx.grid',
    'matplotlib',
    'matplotlib.backends.backend_wxagg',
    'matplotlib.figure',
    'matplotlib.dates',
    'PIL',
    'PIL.Image',
    'scipy',
    'scipy.signal',
    'numpy',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'test', 'tests'],
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
    name='FES_Rowing_App',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
)

