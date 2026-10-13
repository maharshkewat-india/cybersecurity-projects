@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -3.10 -m venv .venv 2>nul
    if errorlevel 1 py -3 -m venv .venv
    if errorlevel 1 (
        echo.
        echo Python 3.10 or newer is required. Install Python, then run this file again.
        pause
        exit /b 1
    )
)

if not exist ".venv\.dependencies-installed" (
    echo Installing required packages...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Dependency installation failed. Check your internet connection and try again.
        pause
        exit /b 1
    )
    type nul > ".venv\.dependencies-installed"
)

if not exist "config.json" copy /y "config.json.example" "config.json" >nul

echo Starting Wi-Fi Security Analyzer...
".venv\Scripts\python.exe" "GUI_Module.py"

if errorlevel 1 (
    echo.
    echo The application exited with an error.
    pause
)
endlocal
