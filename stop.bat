@echo off
title AI Outreach — Shutdown
color 0C

echo.
echo  Shutting down AI Outreach System...
echo.

:: Kill backend (uvicorn on 8000)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING 2^>nul') do (
    echo  Stopping Backend (PID %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

:: Kill frontend (Next.js on 3000/3001)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING 2^>nul') do (
    echo  Stopping Frontend (PID %%a)...
    taskkill /F /PID %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3001 ^| findstr LISTENING 2^>nul') do (
    echo  Stopping Frontend (PID %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo  All servers stopped.
echo.
pause
