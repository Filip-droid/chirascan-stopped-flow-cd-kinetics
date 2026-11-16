@echo off
REM "StoppedFlowKinetiX_env Terminal": a command prompt in this folder with the project's own
REM environment active (made by setup_env.bat), e.g. for
REM     python main.py
REM     python -m pytest -q
REM     BuildInstaller.bat
REM With a command after it, it runs that command first and then stays open,
REM e.g.  "StoppedFlowKinetiX_env Terminal.bat" python -m pytest -q
REM (the shortcuts "Run tests" and "Build installer" do exactly that).
cd /d "%~dp0"
if not exist "%~dp0StoppedFlowKinetiX_env\Scripts\activate.bat" (
    echo StoppedFlowKinetiX_env does not exist yet - run setup_env.bat first.
    pause
    exit /b 1
)
call "%~dp0StoppedFlowKinetiX_env\Scripts\activate.bat"
title StoppedFlowKinetiX_env Terminal
if "%~1"=="" goto prompt
title StoppedFlowKinetiX_env - %*
echo ^> %*
call %*
echo.
:prompt
cmd /k
