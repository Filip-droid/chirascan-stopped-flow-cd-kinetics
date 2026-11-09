@echo off
REM Removes the Python cache folders of the project.
cd /d "%~dp0"
for /d /r . %%d in (__pycache__ .pytest_cache) do @if exist "%%d" rd /s /q "%%d"
echo Done.
