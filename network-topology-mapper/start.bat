@echo off
echo Starting Network Topology Mapper...

echo Starting Backend API (Port 8000)...
start cmd /k "cd backend && .\.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000"

echo Starting Frontend Dev Server (Port 3000)...
start cmd /k "cd frontend && npm run dev"

echo All services are starting! You can close this window.
