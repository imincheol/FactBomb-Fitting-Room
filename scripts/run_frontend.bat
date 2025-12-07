@echo off
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%..\frontend"

echo ==========================================
echo   Starting Frontend Server...
echo ==========================================

if not exist "node_modules" (
    echo [INFO] Installing frontend dependencies...
    call npm install
)

echo [INFO] Starting Vite server...
npm run dev
if "%1"=="" pause
