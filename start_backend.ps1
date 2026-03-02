# Start the intelligent outreach backend and Temporal worker safely
echo "Starting FastAPI Backend..."
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$PSScriptRoot'; .\backend\venv\Scripts\activate; uvicorn backend.main:app --port 8000 --reload`""

echo "Starting Temporal Worker..."
Start-Process powershell -ArgumentList "-NoExit -Command `"cd '$PSScriptRoot'; .\backend\venv\Scripts\activate; python -m backend.temporal.worker`""

echo "Done! The backend and worker are opening in new windows."
