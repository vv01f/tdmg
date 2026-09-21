@echo off
setlocal

where python >nul 2>&1
if errorlevel 1 (
    echo Error: Python was not found.
    echo Please install Python 3.13 or newer and make sure it is in PATH.
    exit /b 1
)

python --version

python -m pip --version
if errorlevel 1 (
    echo Error: pip was not found.
    exit /b 1
)

echo Installing tdmg...
python -m pip install .

if errorlevel 1 (
    echo Error: Installation failed.
    exit /b 1
)

echo Installation successful.
endlocal
