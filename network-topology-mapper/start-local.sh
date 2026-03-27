#!/usr/bin/env bash
# =============================================================================
# NTS Local Startup — No Docker Required
# =============================================================================
# Usage: ./start-local.sh
#
# Starts the backend (FastAPI/uvicorn) and frontend (Vite dev server).
# Press Ctrl+C to stop both.
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "  NTS — Local (Dockerless) Startup"
echo "============================================"
echo ""

# --- Check prerequisites ---
MISSING=""

if ! command -v nmap &>/dev/null; then
    MISSING="$MISSING  - nmap: https://nmap.org/download\n"
fi

# Find Python (try python, python3)
PYTHON=""
if command -v python &>/dev/null; then
    PYTHON="python"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
else
    MISSING="$MISSING  - Python 3.11+: https://python.org\n"
fi

if ! command -v node &>/dev/null; then
    MISSING="$MISSING  - Node.js 18+: https://nodejs.org\n"
fi

if [ -n "$MISSING" ]; then
    echo "ERROR: Missing prerequisites:"
    echo -e "$MISSING"
    exit 1
fi

echo "Prerequisites OK: nmap, $PYTHON, node $(node --version)"
echo ""

# --- Environment file ---
if [ ! -f .env ]; then
    echo "No .env found — copying .env.dockerless as starting point..."
    cp .env.dockerless .env
    echo ""
    echo "  IMPORTANT: Edit .env to set:"
    echo "    SCAN_DEFAULT_RANGE  — your network subnet (e.g., 192.168.1.0/24)"
    echo "    NEO4J_PASSWORD      — must match your Neo4j Desktop password"
    echo ""
fi

# --- Backend setup ---
echo "Setting up backend..."
cd backend

if [ ! -d .venv ]; then
    echo "  Creating Python virtual environment..."
    $PYTHON -m venv .venv
fi

# Activate venv (handle Windows Git Bash vs Unix)
if [ -f .venv/Scripts/activate ]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

echo "  Installing Python dependencies..."
pip install -q -r requirements.txt

mkdir -p data

echo "  Starting backend on http://127.0.0.1:8000 ..."
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# --- Frontend setup ---
cd ../frontend

if [ ! -d node_modules ]; then
    echo "  Installing frontend dependencies..."
    npm install
fi

echo ""
echo "============================================"
echo "  NTS is running!"
echo "============================================"
echo ""
echo "  Frontend:   http://localhost:3000"
echo "  Backend:    http://127.0.0.1:8000/api"
echo "  API Docs:   http://127.0.0.1:8000/docs"
echo "  Neo4j:      http://localhost:7474"
echo ""
echo "  Press Ctrl+C to stop."
echo ""

cleanup() {
    echo ""
    echo "Shutting down..."
    kill $BACKEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM

npm run dev
