# Start the AI Outreach System backend and Temporal worker
# Usage: .\start_backend.ps1

$root = $PSScriptRoot

# Start FastAPI Backend
Write-Host "Starting FastAPI Backend on port 8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$root'; .\backend\venv\Scripts\activate; python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload`""

# Start Temporal Worker (optional — requires Docker containers running)
Write-Host "Starting Temporal Worker..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$root'; .\backend\venv\Scripts\activate; python -m backend.temporal.worker`""

Write-Host ""
Write-Host "Done! Two new windows opened:" -ForegroundColor Green
Write-Host "  - Backend API:     http://localhost:8000" -ForegroundColor Yellow
Write-Host "  - Temporal Worker: listening on task queues" -ForegroundColor Yellow
Write-Host ""
Write-Host "Make sure Docker is running for Temporal:" -ForegroundColor DarkGray
Write-Host "  docker-compose up -d" -ForegroundColor DarkGray
