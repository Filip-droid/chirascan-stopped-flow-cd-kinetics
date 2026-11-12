@echo off
REM Starts StoppedFlowKinetiX from the source code - with the environment made by
REM setup_environment.bat (folder "venv") when it exists, otherwise with "python".
cd /d "%~dp0"
if exist "%~dp0venv\Scripts\python.exe" (
    "%~dp0venv\Scripts\python.exe" main.py %*
) else (
    python main.py %*
)
