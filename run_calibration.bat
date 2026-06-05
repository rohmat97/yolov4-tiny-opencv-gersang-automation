@echo off
setlocal enabledelayedexpansion

echo ==============================================================
echo              GERSANG CALIBRATION INITIALIZER
echo ==============================================================

:: Find a working Python command
set "PYTHON_CMD="
py -V >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_CMD=py"
    goto :found
)

python -V >nul 2>&1
if !errorlevel! equ 0 (
    set "PYTHON_CMD=python"
    goto :found
)

:found
if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python was not found or is not functioning correctly on this system.
    echo Please download and install Python 3.x from: https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Make sure to check the box:
    echo            "[x] Add python.exe to PATH"
    echo            during the installation process.
    echo ==============================================================
    pause
    exit /b 1
)

:: Get the absolute path of the Python executable
set "PYTHON_EXE="
for /f "delims=" %%i in ('where.exe %PYTHON_CMD% 2^>nul') do (
    set "PYTHON_EXE=%%i"
    goto :resolved
)

:resolved
if "%PYTHON_EXE%"=="" (
    echo [ERROR] Failed to resolve the absolute path of %PYTHON_CMD%.
    pause
    exit /b 1
)

echo Python found: %PYTHON_EXE%
echo Checking/Installing required dependencies...
"%PYTHON_EXE%" -m pip install -r "%~dp0requirements.txt"
if !errorlevel! neq 0 (
    echo [WARNING] Failed to verify or install some dependencies.
    echo The script will proceed but might fail if modules are missing.
    echo.
)

echo.
echo Requesting Administrator privileges to run the calibration script...
powershell -Command "Start-Process cmd -ArgumentList '/k \"\"%PYTHON_EXE%\" \"%~dp0auto_login.py\" --calibrate\"' -WorkingDirectory '%~dp0' -Verb RunAs"
if !errorlevel! neq 0 (
    echo [ERROR] Failed to launch with Administrator privileges.
    pause
    exit /b 1
)
