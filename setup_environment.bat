@echo off
REM ==========================================================================
REM  StoppedFlowKinetiX - Python environment + desktop shortcut
REM
REM  Uses the virtual environment in the folder "venv" next to this file:
REM    - when it exists and works, it is kept: only missing or changed
REM      packages of requirements.txt are installed (a few seconds when
REM      nothing changed) and the desktop shortcut is refreshed;
REM    - when it does not exist or is broken, it is created, all packages
REM      are installed and the tests are run.
REM  The shortcut "StoppedFlowKinetiX (Python)" on the desktop starts the
REM  program with pythonw.exe of that environment (no console window).
REM
REM  Usage:   setup_environment.bat              keep / update the environment
REM           setup_environment.bat fresh        delete it and build it again
REM           setup_environment.bat fresh 3.12   rebuild with a specific Python version
REM ==========================================================================
setlocal
cd /d "%~dp0"
set "APPDIR=%~dp0"
set "VENV=%APPDIR%venv"
set "VPY=%VENV%\Scripts\python.exe"

REM --- arguments: "fresh" and/or a Python version such as 3.12
set "FRESH="
set "PYVER="
for %%a in (%*) do (
    if /i "%%~a"=="fresh"   set "FRESH=1"
    if /i "%%~a"=="/fresh"  set "FRESH=1"
    if /i "%%~a"=="--fresh" set "FRESH=1"
    echo %%~a| findstr /r "^[0-9][0-9]*\.[0-9][0-9]*$" >nul && set "PYVER=%%~a"
)
if defined PYVER set "FRESH=1"

REM --- is there a working environment?
set "HAVE="
if exist "%VPY%" (
    "%VPY%" -c "import sys" >nul 2>nul && set "HAVE=1"
)
if defined HAVE if not defined FRESH goto update

REM ==========================================================================
REM  Build a new environment
REM ==========================================================================
REM Which Python creates the environment, in this order:
REM   1. the py launcher (python.org installations)
REM   2. "python" on PATH (e.g. when started from the Anaconda Prompt)
REM   3. Anaconda / Miniconda in their usual folders
set "PY="
if defined PYVER (
    py -%PYVER% --version >nul 2>nul && set "PY=py -%PYVER%"
    if not defined PY (
        echo Python %PYVER% was not found by the py launcher ^(py -0 lists the installed versions^).
        pause
        exit /b 1
    )
)
if not defined PY (
    py -3 --version >nul 2>nul && set "PY=py -3"
)
if not defined PY (
    python --version >nul 2>nul && set "PY=python"
)
if not defined PY (
    for %%d in ("%USERPROFILE%\anaconda3" "%USERPROFILE%\miniconda3" "%LOCALAPPDATA%\anaconda3" "%LOCALAPPDATA%\miniconda3" "%ProgramData%\anaconda3" "%ProgramData%\miniconda3" "%ProgramData%\Anaconda3" "C:\anaconda3" "C:\miniconda3") do (
        if not defined PY if exist "%%~d\python.exe" (
            set "PY="%%~d\python.exe""
            REM as the Anaconda Prompt does: its DLLs (e.g. for SSL, needed by pip) on PATH for this run
            set "PATH=%%~d;%%~d\Library\mingw-w64\bin;%%~d\Library\usr\bin;%%~d\Library\bin;%%~d\Scripts;%PATH%"
        )
    )
)
if not defined PY (
    echo.
    echo Python was not found.
    echo  - With Anaconda: start "Anaconda Prompt" from the Start menu, go to this folder and run
    echo    setup_environment.bat there.
    echo  - Or install Python 3.10 or newer from https://www.python.org ^(it does not interfere with
    echo    Anaconda^) and run this file again.
    pause
    exit /b 1
)
echo Using: %PY%
%PY% --version
if exist "%VENV%" (
    if defined FRESH (echo Removing the old environment ...) else (echo The environment is broken - building it again ...)
    rd /s /q "%VENV%"
    if exist "%VENV%" (
        echo Cannot remove "%VENV%" - close StoppedFlowKinetiX and any window using it, then try again.
        pause
        exit /b 1
    )
)
echo Creating the environment "%VENV%" ...
%PY% -m venv "%VENV%"
if errorlevel 1 (
    echo Creating the environment failed.
    pause
    exit /b 1
)
"%VPY%" -m pip install --upgrade pip
echo Installing the packages ^(requirements.txt^) ...
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Installing the packages failed - see the messages above.
    echo If it mentions SSL and Python comes from Anaconda, run this file from the "Anaconda Prompt",
    echo or install Python from https://www.python.org and run:  setup_environment.bat fresh
    pause
    exit /b 1
)
echo Running the tests ...
"%VPY%" -m pytest -q
if errorlevel 1 (
    echo.
    echo WARNING: some tests failed - see above. The shortcut is created anyway.
    echo.
)
goto shortcut

REM ==========================================================================
REM  Keep the environment, bring the packages up to date
REM ==========================================================================
:update
echo Using the existing environment "%VENV%"
"%VPY%" --version
REM an environment made from Anaconda's Python: its DLLs on PATH for this run (as the Anaconda Prompt does)
set "VHOME="
for /f "tokens=1,* delims==" %%a in ('findstr /b /i "home" "%VENV%\pyvenv.cfg" 2^>nul') do set "VHOME=%%b"
if defined VHOME for /f "tokens=*" %%c in ("%VHOME%") do set "VHOME=%%c"
if defined VHOME if exist "%VHOME%\Library\bin" set "PATH=%VHOME%;%VHOME%\Library\mingw-w64\bin;%VHOME%\Library\usr\bin;%VHOME%\Library\bin;%VHOME%\Scripts;%PATH%"
echo Checking the packages ^(requirements.txt^) ...
"%VPY%" -m pip install -q --disable-pip-version-check -r requirements.txt
if errorlevel 1 (
    echo Installing the packages failed - see the messages above.
    echo To build the environment from scratch, run:  setup_environment.bat fresh
    pause
    exit /b 1
)
echo The packages are up to date.

REM ==========================================================================
REM  Desktop shortcut (also works when the desktop is in OneDrive)
REM ==========================================================================
:shortcut
echo Creating the desktop shortcut ...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$d=[Environment]::GetFolderPath('Desktop');" ^
  "$s=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $d 'StoppedFlowKinetiX (Python).lnk'));" ^
  "$s.TargetPath='%VENV%\Scripts\pythonw.exe';" ^
  "$q=[char]34; $s.Arguments=$q+'%APPDIR%main.py'+$q;" ^
  "$s.WorkingDirectory='%APPDIR%';" ^
  "$s.IconLocation='%APPDIR%resources\icons\app_icon.ico';" ^
  "$s.Description='StoppedFlowKinetiX - stopped-flow CD kinetics (runs from the source code)';" ^
  "$s.Save()"
if errorlevel 1 (
    echo Creating the shortcut failed. You can start the program with run.bat instead.
) else (
    echo The shortcut "StoppedFlowKinetiX (Python)" is on your desktop.
)

echo.
echo Done. Environment: "%VENV%"
pause
