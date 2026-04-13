# Start the AI Outreach System backend
# Usage: .\start_backend.ps1

$root = $PSScriptRoot

# Start FastAPI Backend
Write-Host "Starting FastAPI Backend on port 8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$root'; .venv\Scripts\activate; python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload`""

Write-Host ""
Write-Host "Done! Backend started:" -ForegroundColor Green
Write-Host "  - Backend API: http://localhost:8000" -ForegroundColor Yellow
