@echo off
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%.."

echo ==========================================
echo   Starting Backend Server...
echo ==========================================

:: Check Virtual Environment
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

:: Activate & Install/Update Dependencies
call venv\Scripts\activate
echo [INFO] Checking dependencies...
pip install -r backend\requirements.txt

:: Start Server
echo [INFO] Starting Uvicorn server...
set PYTHONIOENCODING=utf-8
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
if "%1"=="" pause
