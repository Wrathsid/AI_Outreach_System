# ================================================================
#  AI Outreach System — Demo Launcher (PowerShell)
#  Double-click or run: .\demo.ps1
# ================================================================

$Host.UI.RawUI.WindowTitle = "AI Outreach System - Demo Day"
Write-Host ""
Write-Host "  ================================================================" -ForegroundColor Cyan
Write-Host "    AI OUTREACH SYSTEM — Demo Launcher" -ForegroundColor White
Write-Host "    Starting Backend + Frontend..." -ForegroundColor Gray
Write-Host "  ================================================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Kill stale processes on demo ports
Write-Host "[1/4] Clearing ports 8000, 3000, 3001..." -ForegroundColor Yellow
@(8000, 3000, 3001) | ForEach-Object {
    $port = $_
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | ForEach-Object {
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}
Start-Sleep -Seconds 1

# 2. Start Backend
Write-Host "[2/4] Starting Backend (FastAPI)..." -ForegroundColor Green
$backendCmd = "cd '$projectRoot'; & '$projectRoot\.venv\Scripts\activate.ps1'; python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

# 3. Wait for backend
Write-Host "[3/4] Waiting for backend to boot (4s)..." -ForegroundColor Gray
Start-Sleep -Seconds 4

# 4. Start Frontend
Write-Host "[4/4] Starting Frontend (Next.js)..." -ForegroundColor Green
$frontendCmd = "cd '$projectRoot\frontend'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Start-Sleep -Seconds 5

Write-Host ""
Write-Host "  ================================================================" -ForegroundColor Cyan
Write-Host "    READY FOR DEMO!" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "    Backend:   http://localhost:8000" -ForegroundColor Green
Write-Host "    Frontend:  http://localhost:3000" -ForegroundColor Green
Write-Host "    API Docs:  http://localhost:8000/docs" -ForegroundColor DarkGray
Write-Host "" -ForegroundColor White
Write-Host "  ================================================================" -ForegroundColor Cyan
Write-Host ""

# Open browser
Start-Process "http://localhost:3000"

Write-Host "Browser opened! You're live." -ForegroundColor Green
Write-Host "Press any key to exit this launcher..." -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
