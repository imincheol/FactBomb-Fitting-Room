@echo off
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%.."

echo ==========================================
echo   Running Code Quality Check (Ruff)...
echo ==========================================

:: Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate
)

:: Run ruff check
echo [1/2] Linting check...
ruff check backend/
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Automatic fixing available. Run with --fix if desired.
)

:: Run ruff format
echo [2/2] Format check...
ruff format --check backend/

echo.
echo ==========================================
echo   Quality Check Complete.
echo ==========================================
pause
