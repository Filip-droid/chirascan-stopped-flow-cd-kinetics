@echo off
REM Starts StoppedFlowKinetiX from the source code - with the environment made by
REM setup_env.bat (folder "StoppedFlowKinetiX_env") when it exists, otherwise with "python".
cd /d "%~dp0"
if exist "%~dp0StoppedFlowKinetiX_env\Scripts\python.exe" (
    "%~dp0StoppedFlowKinetiX_env\Scripts\python.exe" main.py %*
) else (
    python main.py %*
)
