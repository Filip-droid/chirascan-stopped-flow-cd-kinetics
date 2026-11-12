@echo off
REM ==========================================================================
REM  StoppedFlowKinetiX - fresh Python environment + desktop shortcut
REM
REM  Creates a new virtual environment in the folder "venv" next to this file
REM  (an existing one is deleted first), installs requirements.txt into it,
REM  runs the tests and puts the shortcut "StoppedFlowKinetiX (Python)" on the
REM  desktop. The shortcut starts the program with pythonw.exe of that
REM  environment (no console window).
REM
REM  Usage:   setup_environment.bat          (newest Python found by "py")
REM           setup_environment.bat 3.12     (a specific installed version)
REM ==========================================================================
setlocal
cd /d "%~dp0"
set "APPDIR=%~dp0"
set "VENV=%APPDIR%venv"

REM --- which Python creates the environment
set "PY="
if not "%~1"=="" (
    set "PY=py -%~1"
) else (
    where py >nul 2>nul && set "PY=py -3"
)
if "%PY%"=="" set "PY=python"
echo Using: %PY%
%PY% --version
if errorlevel 1 (
    echo.
    echo Python was not found. Install Python 3.10 or newer from https://www.python.org
    echo ^(tick "Add python.exe to PATH" / keep the "py launcher"^) and run this file again.
    pause
    exit /b 1
)

REM --- fresh environment
if exist "%VENV%" (
    echo Removing the old environment "%VENV%" ...
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

echo Installing the packages ^(requirements.txt^) ...
"%VENV%\Scripts\python.exe" -m pip install --upgrade pip
"%VENV%\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Installing the packages failed - see the messages above.
    pause
    exit /b 1
)

REM --- check that the analysis gives the notebook's numbers
echo Running the tests ...
"%VENV%\Scripts\python.exe" -m pytest -q
if errorlevel 1 (
    echo.
    echo WARNING: some tests failed - see above. The shortcut is created anyway.
    echo.
)

REM --- desktop shortcut (also works when the desktop is in OneDrive)
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
