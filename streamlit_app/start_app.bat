@echo off
echo Starting Cline Web IDE...

REM Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH.
    pause
    exit /b 1
)

REM Set up environment if needed
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    python -m pip install --upgrade pip
    
    echo Installing dependencies without Rust requirements...
    python install_dependencies.py
) else (
    call venv\Scripts\activate
)

REM Run the application with no authentication for easier local use
python run.py --no-auth

pause
