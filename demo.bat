@echo off
title AI Outreach System — Demo Day
color 0A

echo.
echo  ================================================================
echo    AI OUTREACH SYSTEM — Demo Launcher
echo    Starting Backend + Frontend...
echo  ================================================================
echo.

:: Kill any existing processes on ports 8000 and 3000
echo [1/4] Clearing ports...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING 2^>nul') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING 2^>nul') do taskkill /F /PID %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3001 ^| findstr LISTENING 2^>nul') do taskkill /F /PID %%a >nul 2>&1
timeout /t 1 /nobreak >nul

:: Start Backend
echo [2/4] Starting Backend (FastAPI on port 8000)...
cd /d "%~dp0"
start "AI Outreach Backend" cmd /k "call .venv\Scripts\activate && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

:: Wait for backend to initialize
echo [3/4] Waiting for backend to boot...
timeout /t 4 /nobreak >nul

:: Start Frontend
echo [4/4] Starting Frontend (Next.js on port 3000)...
cd /d "%~dp0frontend"
start "AI Outreach Frontend" cmd /k "npm run dev"

:: Wait and open browser
timeout /t 5 /nobreak >nul

echo.
echo  ================================================================
echo    READY FOR DEMO!
echo.
echo    Backend:   http://localhost:8000
echo    Frontend:  http://localhost:3000
echo    API Docs:  http://localhost:8000/docs
echo.
echo    Press any key to open the app in your browser...
echo  ================================================================
pause >nul

start http://localhost:3000
