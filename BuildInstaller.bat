@echo off
REM Builds StoppedFlowKinetiX.exe (PyInstaller) and the Windows installer (Inno Setup 6).
REM Run from the project folder, in the Python environment with requirements.txt installed
REM plus PyInstaller (pip install pyinstaller).

cd /d "%~dp0"

REM Version from src\version.py (one place for it)
for /f "delims=" %%v in ('python -c "from src.version import APP_VERSION; print(APP_VERSION)"') do set APPVER=%%v
if "%APPVER%"=="" (
    echo Cannot read the version from src\version.py - is Python on the PATH?
    pause
    exit /b 1
)
echo Building StoppedFlowKinetiX %APPVER%

REM Tests first: an installer is built only from code that gives the notebook's numbers
python -m pytest -q
if errorlevel 1 (
    echo Tests failed - stopping.
    pause
    exit /b 1
)

REM Executable (one folder) - settings in StoppedFlowKinetiX.spec
pyinstaller --noconfirm --clean StoppedFlowKinetiX.spec
if errorlevel 1 (
    echo PyInstaller build failed - stopping.
    pause
    exit /b 1
)

REM Installer
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"
%ISCC% /DMyAppVersion=%APPVER% installer.iss
if errorlevel 1 (
    echo Inno Setup build failed - stopping. build\ and dist\ left in place for debugging.
    pause
    exit /b 1
)

REM Installer built - remove the intermediate output (regenerated on every run)
rd /s /q build
rd /s /q dist

echo.
echo Done. The installer is installer\Setup_for_StoppedFlowKinetiX_ver_%APPVER%.exe
pause
