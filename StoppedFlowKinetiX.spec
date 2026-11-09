# -*- mode: python ; coding: utf-8 -*-
# PyInstaller specification of StoppedFlowKinetiX (used by BuildInstaller.bat).

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('resources', 'resources'), ('example', 'example')],
    # help pages and controllers are imported normally, but list the
    # matplotlib Qt backend explicitly (it is chosen by name at run time)
    hiddenimports=['matplotlib.backends.backend_qt5agg', 'xlsxwriter'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'PyQt6', 'PySide2', 'PySide6', 'IPython', 'jupyter', 'notebook', 'pytest'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='StoppedFlowKinetiX',
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
    icon=['resources/icons/app_icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='StoppedFlowKinetiX',
)
