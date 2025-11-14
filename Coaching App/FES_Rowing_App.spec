# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('compress.jpg', '.'), ('extend.jpg', '.')],
    hiddenimports=['wx', 'wx.grid', 'matplotlib', 'matplotlib.backends.backend_wxagg', 'matplotlib.figure', 'matplotlib.dates', 'PIL', 'PIL.Image', 'scipy', 'scipy.signal', 'numpy'],
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
app = BUNDLE(
    exe,
    name='FES_Rowing_App.app',
    icon=None,
    bundle_identifier=None,
)
