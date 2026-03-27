# =============================================================================
# NTS Local Startup — No Docker Required (PowerShell)
# =============================================================================
# Usage: .\start-local.ps1
#
# Starts the backend (FastAPI/uvicorn) and frontend (Vite dev server).
# Press Ctrl+C to stop both.
# =============================================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  NTS - Local (Dockerless) Startup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# --- Check prerequisites ---
$missing = @()

if (-not (Get-Command nmap -ErrorAction SilentlyContinue)) {
    $missing += "  - nmap: https://nmap.org/download"
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    $missing += "  - Python 3.11+: https://python.org"
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    $missing += "  - Node.js 18+: https://nodejs.org"
}

if ($missing.Count -gt 0) {
    Write-Host "ERROR: Missing prerequisites:" -ForegroundColor Red
    $missing | ForEach-Object { Write-Host $_ -ForegroundColor Red }
    exit 1
}

$nodeVersion = node --version
Write-Host "Prerequisites OK: python, node $nodeVersion" -ForegroundColor Green
Write-Host ""

# --- Environment file ---
if (-not (Test-Path .env)) {
    Write-Host "No .env found - copying .env.dockerless as starting point..." -ForegroundColor Yellow
    Copy-Item .env.dockerless .env
    Write-Host ""
    Write-Host "  IMPORTANT: Edit .env to set:" -ForegroundColor Yellow
    Write-Host "    SCAN_DEFAULT_RANGE  - your network subnet (e.g., 192.168.1.0/24)" -ForegroundColor Yellow
    Write-Host "    NEO4J_PASSWORD      - must match your Neo4j Desktop password" -ForegroundColor Yellow
    Write-Host ""
}

# --- Backend setup ---
Write-Host "Setting up backend..."
Set-Location backend

if (-not (Test-Path .venv)) {
    Write-Host "  Creating Python virtual environment..."
    python -m venv .venv
}

# Activate venv
& .venv\Scripts\Activate.ps1

Write-Host "  Installing Python dependencies..."
pip install -q -r requirements.txt

if (-not (Test-Path data)) {
    New-Item -ItemType Directory -Path data | Out-Null
}

Write-Host "  Starting backend on http://127.0.0.1:8000 ..."
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:ScriptDir\backend
    & $using:ScriptDir\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
}

# --- Frontend setup ---
Set-Location ..\frontend

if (-not (Test-Path node_modules)) {
    Write-Host "  Installing frontend dependencies..."
    npm install
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  NTS is running!" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Frontend:   http://localhost:3000" -ForegroundColor Green
Write-Host "  Backend:    http://127.0.0.1:8000/api" -ForegroundColor Green
Write-Host "  API Docs:   http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "  Neo4j:      http://localhost:7474" -ForegroundColor Green
Write-Host ""
Write-Host "  Press Ctrl+C to stop." -ForegroundColor Yellow
Write-Host ""

try {
    npm run dev
}
finally {
    Write-Host "Shutting down..."
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -ErrorAction SilentlyContinue
}
