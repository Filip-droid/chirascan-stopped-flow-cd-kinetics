# -*- mode: python ; coding: utf-8 -*-
# PyInstaller specification of StoppedFlowKinetiX.
# Windows: used by BuildInstaller.bat (folder dist/StoppedFlowKinetiX, then the Inno Setup installer).
# macOS: used by .github/workflows/build-macos.yml (dist/StoppedFlowKinetiX.app, then a .dmg).
# PyInstaller builds for the system it runs on; a Mac app must be built on a Mac.
import sys

sys.path.insert(0, SPECPATH)
from src.version import APP_NAME, APP_VERSION  # noqa: E402

MAC = sys.platform == 'darwin'

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
    upx=not MAC,                       # UPX damages macOS binaries
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['resources/icons/app_icon.icns' if MAC else 'resources/icons/app_icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=not MAC,
    upx_exclude=[],
    name='StoppedFlowKinetiX',
)

if MAC:
    app = BUNDLE(
        coll,
        name='StoppedFlowKinetiX.app',
        icon='resources/icons/app_icon.icns',
        bundle_identifier='cz.ibp.stoppedflowkinetix',
        version=APP_VERSION,
        info_plist={
            'CFBundleName': APP_NAME,
            'CFBundleDisplayName': APP_NAME,
            'CFBundleShortVersionString': APP_VERSION,
            'CFBundleVersion': APP_VERSION,
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': True,   # light look also in dark mode (the program's own colours)
            'LSMinimumSystemVersion': '11.0',
            'NSHumanReadableCopyright': 'Institute of Biophysics of the Czech Academy of Sciences, MIT License',
        },
    )
