@echo off
echo ========================================
echo Starting Network Topology Mapper Backend
echo ========================================
echo.

cd /d "%~dp0backend"

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting backend server on port 5000...
echo Press Ctrl+C to stop
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

pause
