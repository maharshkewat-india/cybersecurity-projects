@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    py -m venv .venv
    if errorlevel 1 (
        echo Failed to create the virtual environment. Install Python and try again.
        exit /b 1
    )
)

"%~dp0.venv\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo Failed to install project dependencies.
    exit /b 1
)

echo.| "%~dp0.venv\Scripts\python.exe" -m streamlit run "%~dp0app.py"

endlocal