@echo off
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%.."

echo ==========================================
echo   Running Tests & Coverage...
echo ==========================================

:: Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate
)

:: Run pytest
pytest
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Tests Failed!
    exit /b %ERRORLEVEL%
)

echo.
echo ==========================================
echo   Tests Passed!
echo   See 'htmlcov/index.html' for coverage details.
echo ==========================================
pause
