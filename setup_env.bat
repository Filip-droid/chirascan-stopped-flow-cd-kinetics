@echo off
REM ==========================================================================
REM  StoppedFlowKinetiX - setup_env.bat: Python environment + desktop shortcuts
REM
REM  The project's own environment is the folder "StoppedFlowKinetiX_env" next
REM  to this file (naming: <Project>_env; ignored by git):
REM    - when it exists and works, it is kept: only missing or changed packages
REM      are installed (a few seconds when nothing changed) and the desktop
REM      shortcuts are refreshed;
REM    - when it does not exist or is broken, it is created, all packages are
REM      installed and the tests are run.
REM  Packages: requirements-lock.txt (the exact versions of every library) when
REM  it was made with the same Python version (major.minor) as the
REM  environment's; otherwise requirements-dev.txt (requirements.txt +
REM  PyInstaller), e.g. for another Python or Anaconda. The first run with no
REM  lock file writes requirements-lock.txt - commit it.
REM  Desktop folder "StoppedFlowKinetiX (Python)" with four shortcuts:
REM    "StoppedFlowKinetiX"              starts the program (pythonw.exe, no console)
REM    "StoppedFlowKinetiX_env Terminal" command prompt here, environment active
REM    "Run tests"                       that terminal, running  python -m pytest -q
REM    "Build installer"                 that terminal, running  BuildInstaller.bat
REM  Another computer: get the project with git, double-click this file (an
REM  environment cannot be copied - it contains fixed paths).
REM
REM  Usage:   setup_env.bat              keep / update the environment
REM           setup_env.bat fresh        delete it and build it again
REM           setup_env.bat fresh 3.12   rebuild with a specific Python version
REM ==========================================================================
setlocal
cd /d "%~dp0"
set "APPDIR=%~dp0"
set "ENV_NAME=StoppedFlowKinetiX_env"
set "APP_NAME=StoppedFlowKinetiX"
set "VENV=%APPDIR%%ENV_NAME%"
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
    echo    setup_env.bat there.
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
%PY% -m venv "%VENV%" --prompt %ENV_NAME%
if errorlevel 1 (
    echo Creating the environment failed.
    pause
    exit /b 1
)
"%VPY%" -m pip install --upgrade pip
set "PIPQ="
call :install
if errorlevel 1 (
    echo Installing the packages failed - see the messages above.
    echo If it mentions SSL and Python comes from Anaconda, run this file from the "Anaconda Prompt",
    echo or install Python from https://www.python.org and run:  setup_env.bat fresh
    pause
    exit /b 1
)
echo Running the tests ...
"%VPY%" -m pytest -q
if errorlevel 1 (
    echo.
    echo WARNING: some tests failed - see above. The shortcuts are created anyway.
    echo.
)
if exist "%APPDIR%venv\Scripts\python.exe" (
    echo.
    echo Note: the folder "venv" ^(the environment of earlier versions of this script^) is no
    echo longer used - you can delete it.
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
set "PIPQ=-q --disable-pip-version-check"
call :install
if errorlevel 1 (
    echo Installing the packages failed - see the messages above.
    echo To build the environment from scratch, run:  setup_env.bat fresh
    pause
    exit /b 1
)
echo The packages are up to date.

REM ==========================================================================
REM  Desktop shortcuts (also works when the desktop is in OneDrive)
REM ==========================================================================
:shortcut
REM --- first start made fast: load the libraries once now (Windows Defender checks
REM     every new file the first time it is loaded; matplotlib builds its font list)
echo.
echo Preparing for a fast first start - takes a few minutes only the first time ...
"%VPY%" -c "import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot, matplotlib.font_manager; import numpy, scipy.optimize, scipy.signal, pandas, PyQt5.QtWidgets, xlsxwriter, openpyxl" 2>nul
if errorlevel 1 echo (not every library could be loaded now - that is fine, it happens at the first start instead)
"%VPY%" -m compileall -q src >nul
echo Ready.

echo Creating the desktop folder "%APP_NAME% (Python)" with four shortcuts ...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$d=[Environment]::GetFolderPath('Desktop'); $f=Join-Path $d '%APP_NAME% (Python)';" ^
  "New-Item -ItemType Directory -Force -Path $f | Out-Null;" ^
  "foreach ($old in @('%ENV_NAME% Terminal.lnk', '%APP_NAME% (Python).lnk')) { Remove-Item -LiteralPath (Join-Path $d $old) -ErrorAction SilentlyContinue };" ^
  "$w=New-Object -ComObject WScript.Shell; $q=[char]34; $p='%~dp0'; $term=$p+'%ENV_NAME% Terminal.bat';" ^
  "function L($n, $t, $a, $i, $c) { $s=$w.CreateShortcut((Join-Path $f ($n+'.lnk'))); $s.TargetPath=$t; $s.Arguments=$a; $s.WorkingDirectory=$p; $s.IconLocation=$i; $s.Description=$c; $s.Save() };" ^
  "L '%APP_NAME%' ($p+'%ENV_NAME%\Scripts\pythonw.exe') ($q+$p+'main.py'+$q) ($p+'resources\icons\app_icon.ico') 'Starts %APP_NAME% from the source code';" ^
  "L '%ENV_NAME% Terminal' $term '' ($p+'resources\icons\app_icon.ico') 'Command prompt in the project folder, environment active';" ^
  "L 'Run tests' $term 'python -m pytest -q' ($env:SystemRoot+'\System32\cmd.exe') 'Runs the tests (python -m pytest -q)';" ^
  "L 'Build installer' $term 'BuildInstaller.bat' ($p+'installer_assets\setupicon.ico') 'Builds the installer (BuildInstaller.bat)'"
if errorlevel 1 (
    echo Creating the shortcuts failed - use "%ENV_NAME% Terminal.bat" in this folder instead.
) else (
    echo On the desktop, folder "%APP_NAME% (Python)":
    echo     "%APP_NAME%"               starts the program
    echo     "%ENV_NAME% Terminal"      command prompt here, environment active
    echo     "Run tests"                python -m pytest -q
    echo     "Build installer"          BuildInstaller.bat
)

echo.
echo Done. Environment: "%VENV%"
pause
exit /b 0

REM ==========================================================================
REM  :install - the packages: requirements-lock.txt when it was made with the
REM  same Python version (major.minor) as the environment's, otherwise
REM  requirements-dev.txt; with no lock file, write one.
REM ==========================================================================
:install
set "ENVPY="
"%VPY%" -c "import sys; print('.'.join(map(str, sys.version_info[:2])))" > "%TEMP%\sfk_env_python.txt" 2>nul
set /p ENVPY=<"%TEMP%\sfk_env_python.txt"
del "%TEMP%\sfk_env_python.txt" >nul 2>nul
set "LOCKPY="
if exist requirements-lock.txt for /f "usebackq tokens=5" %%v in (`findstr /b /c:"# made with Python" requirements-lock.txt`) do set "LOCKPY=%%v"
if defined LOCKPY if "%LOCKPY%"=="%ENVPY%" goto install_lock
if defined LOCKPY (
    echo requirements-lock.txt was made with Python %LOCKPY%, this environment has Python %ENVPY%:
    echo installing requirements-dev.txt instead ^(newest versions allowed by requirements.txt^).
) else (
    echo Installing the packages ^(requirements-dev.txt^) ...
)
"%VPY%" -m pip install %PIPQ% -r requirements-dev.txt
if errorlevel 1 exit /b 1
if exist requirements-lock.txt exit /b 0
(echo # made with Python %ENVPY% by setup_env.bat - the exact versions of %ENV_NAME%; used when the Python version matches)> requirements-lock.txt
"%VPY%" -m pip freeze >> requirements-lock.txt
echo Wrote requirements-lock.txt ^(Python %ENVPY%^) - commit it, so that other computers get the same versions.
exit /b 0

:install_lock
echo Installing the exact versions of requirements-lock.txt ^(made with Python %LOCKPY%^) ...
"%VPY%" -m pip install %PIPQ% -r requirements-lock.txt
if errorlevel 1 exit /b 1
exit /b 0
