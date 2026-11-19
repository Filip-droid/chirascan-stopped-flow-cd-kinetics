@echo off
rem ===========================================================================
rem  Runs all tests on this Windows computer (double-click it, or run it from
rem  any folder); the analysis is compared with the notebook's reference
rem  workbook. Result: tools\logs\tests_windows.txt (the last line: passed /
rem  failed), shown at the end here too; tools\logs\tests_finished.txt is
rem  written when it is done.
rem  Python: %%SFK_PYTHON%% if set, else the project's own environment
rem  StoppedFlowKinetiX_env (setup_env.bat) - the same as the desktop shortcut
rem  "Run tests" - else "python".
rem ===========================================================================
cd /d "%~dp0.."
set "PY=python"
if exist "%CD%\StoppedFlowKinetiX_env\Scripts\python.exe" set "PY=%CD%\StoppedFlowKinetiX_env\Scripts\python.exe"
if defined SFK_PYTHON set "PY=%SFK_PYTHON%"
if not exist tools\logs mkdir tools\logs
if exist tools\logs\tests_finished.txt del tools\logs\tests_finished.txt
echo Python used: %PY%> tools\logs\tests_windows.txt
"%PY%" --version >> tools\logs\tests_windows.txt 2>&1
type tools\logs\tests_windows.txt
echo Running all tests (about a minute) - the result goes to tools\logs\tests_windows.txt ...
"%PY%" -m pytest -v -p no:cacheprovider >> tools\logs\tests_windows.txt 2>&1
echo finished %DATE% %TIME% > tools\logs\tests_finished.txt
echo.
echo The end of the result:
powershell -NoProfile -Command "Get-Content -Tail 15 'tools\logs\tests_windows.txt'"
pause
