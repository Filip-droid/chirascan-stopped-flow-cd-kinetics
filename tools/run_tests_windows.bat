@echo off
REM Runs the tests (the analysis is compared with the notebook's reference workbook).
cd /d "%~dp0\.."
python -m pytest -v
pause
