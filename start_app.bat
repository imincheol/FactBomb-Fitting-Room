@echo off
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

echo ==========================================
echo   FactBomb Fitting Room - Auto Launcher
echo ==========================================


echo [0/3] Cleaning up previous processes...
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM node.exe /T 2>nul
echo Cleanup done.

:: Ensure logs directory exists
if not exist "logs" mkdir "logs"

:: 1. Start Backend (New Window)
:: 1. Start Backend (Background)
echo [1/3] Launching Backend Server (Background)...
start /B cmd /c "scripts\run_backend.bat nopause > logs\backend_server.log 2>&1"

:: 2. Start Frontend (Background)
echo [2/3] Launching Frontend Server (Background)...
start /B cmd /c "scripts\run_frontend.bat nopause > logs\frontend_server.log 2>&1"

:: 3. Open Browser
echo [3/3] Opening Web Interface...
timeout /t 5 /nobreak >nul
start http://localhost:5173

echo ==========================================
echo   Servers running in background.
echo   Check logs\backend_server.log and logs\frontend_server.log for details.
echo ==========================================
pause
