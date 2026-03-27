<#
.SYNOPSIS
    NTS One-Click Setup — installs everything, detects your network, and launches the app.

.DESCRIPTION
    Hand this script to a groupmate. They run it once and they're scanning.

    What it does:
      1. Installs missing tools (nmap, Neo4j Desktop) via winget
      2. Auto-detects your network subnet
      3. Configures .env
      4. Sets up Python venv + Node dependencies
      5. Starts Neo4j, backend, and frontend
      6. Opens the browser

.EXAMPLE
    .\setup.ps1              # Full setup + launch
    .\setup.ps1 -SkipInstall # Skip winget installs (if you already have everything)
    .\setup.ps1 -RunOnly     # Skip all setup, just launch (for subsequent runs)
#>

param(
    [switch]$SkipInstall,
    [switch]$RunOnly
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# --- Helpers ---
function Write-Step  { param($msg) Write-Host "`n>> $msg" -ForegroundColor Cyan }
function Write-OK    { param($msg) Write-Host "   [OK] $msg" -ForegroundColor Green }
function Write-Warn  { param($msg) Write-Host "   [!!] $msg" -ForegroundColor Yellow }
function Write-Err   { param($msg) Write-Host "   [ERROR] $msg" -ForegroundColor Red }

function Test-PortOpen {
    param([string]$Host = "localhost", [int]$Port)
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect($Host, $Port)
        $tcp.Close()
        return $true
    } catch {
        return $false
    }
}

# ===========================================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   NTS — Network Topology Scanner Setup" -ForegroundColor Cyan
Write-Host "   One script. Real network scanning. No Docker." -ForegroundColor DarkCyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ===========================================================================
# STEP 1: Install missing tools
# ===========================================================================
if (-not $RunOnly -and -not $SkipInstall) {
    Write-Step "Checking prerequisites..."

    # --- Python ---
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $pyVer = python --version 2>&1
        Write-OK "Python: $pyVer"
    } else {
        Write-Err "Python not found. Install Python 3.11+ from https://python.org"
        Write-Host "         Make sure to check 'Add Python to PATH' during install." -ForegroundColor Yellow
        Read-Host "Press Enter after installing Python, then re-run this script"
        exit 1
    }

    # --- Node.js ---
    if (Get-Command node -ErrorAction SilentlyContinue) {
        $nodeVer = node --version
        Write-OK "Node.js: $nodeVer"
    } else {
        Write-Err "Node.js not found. Install from https://nodejs.org (LTS recommended)"
        Read-Host "Press Enter after installing Node.js, then re-run this script"
        exit 1
    }

    # --- nmap ---
    if (Get-Command nmap -ErrorAction SilentlyContinue) {
        Write-OK "nmap: installed"
    } else {
        Write-Warn "nmap not found — installing via winget..."
        try {
            winget install --id Insecure.Nmap --accept-package-agreements --accept-source-agreements
            # nmap installer adds to PATH but current session doesn't see it yet
            $nmapPath = "C:\Program Files (x86)\Nmap"
            if (Test-Path $nmapPath) {
                $env:PATH += ";$nmapPath"
            }
            Write-OK "nmap installed! You may need to restart your terminal for PATH to update."
        } catch {
            Write-Err "Could not install nmap automatically."
            Write-Host "         Download manually: https://nmap.org/download" -ForegroundColor Yellow
        }
    }

    # --- Neo4j Desktop ---
    $neo4jRunning = Test-PortOpen -Port 7687
    if ($neo4jRunning) {
        Write-OK "Neo4j: running on port 7687"
    } else {
        # Check if Neo4j Desktop is installed
        $neo4jInstalled = (Get-Command neo4j -ErrorAction SilentlyContinue) -or
                          (Test-Path "$env:LOCALAPPDATA\Neo4j Desktop") -or
                          (Test-Path "$env:LOCALAPPDATA\Programs\Neo4j Desktop")

        if (-not $neo4jInstalled) {
            Write-Warn "Neo4j Desktop not found — installing via winget..."
            try {
                winget install --id Neo4j.Neo4jDesktop --accept-package-agreements --accept-source-agreements
                Write-OK "Neo4j Desktop installed!"
            } catch {
                Write-Err "Could not install Neo4j Desktop automatically."
                Write-Host "         Download manually: https://neo4j.com/download/" -ForegroundColor Yellow
            }
        }

        Write-Host ""
        Write-Host "   ============================================================" -ForegroundColor Yellow
        Write-Host "   NEO4J SETUP (one-time, takes 2 minutes):" -ForegroundColor Yellow
        Write-Host "   ============================================================" -ForegroundColor Yellow
        Write-Host "   1. Open Neo4j Desktop" -ForegroundColor White
        Write-Host "   2. Click 'New' > 'Create project'" -ForegroundColor White
        Write-Host "   3. Click 'Add' > 'Local DBMS'" -ForegroundColor White
        Write-Host "   4. Set the password to: changeme" -ForegroundColor White
        Write-Host "      (or whatever you want — you'll enter it below)" -ForegroundColor DarkGray
        Write-Host "   5. Click 'Create'" -ForegroundColor White
        Write-Host "   6. Click 'Start' on the DBMS" -ForegroundColor White
        Write-Host "   7. Wait until it says 'Started' with a green dot" -ForegroundColor White
        Write-Host "   ============================================================" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter once Neo4j is running"

        # Verify
        if (-not (Test-PortOpen -Port 7687)) {
            Write-Err "Neo4j is not responding on port 7687. Make sure the DBMS is started."
            $continue = Read-Host "Continue anyway? (y/n)"
            if ($continue -ne "y") { exit 1 }
        } else {
            Write-OK "Neo4j is running!"
        }
    }
}

# ===========================================================================
# STEP 2: Auto-detect network subnet
# ===========================================================================
if (-not $RunOnly) {
    Write-Step "Detecting your network..."

    # Get active network adapters with real IPs (skip loopback, APIPA, VPN tunnels)
    $adapters = Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object {
            $_.IPAddress -ne "127.0.0.1" -and
            -not $_.IPAddress.StartsWith("169.254") -and
            $_.PrefixOrigin -ne "WellKnown"
        } |
        Sort-Object -Property { $_.InterfaceAlias -match "Wi-Fi|Ethernet" } -Descending

    $detectedSubnet = $null
    $detectedIP = $null

    foreach ($adapter in $adapters) {
        $ip = $adapter.IPAddress
        $prefix = $adapter.PrefixLength
        $iface = $adapter.InterfaceAlias

        # Skip VPN-looking ranges (10.x with /32 or weird masks, 100.x Tailscale)
        if ($ip.StartsWith("100.") -and $prefix -ge 30) { continue }
        if ($prefix -ge 30) { continue }

        # Calculate network address
        $ipBytes = [System.Net.IPAddress]::Parse($ip).GetAddressBytes()
        $maskInt = [uint32]([math]::Pow(2, 32) - [math]::Pow(2, 32 - $prefix))
        $maskBytes = [BitConverter]::GetBytes($maskInt)
        [Array]::Reverse($maskBytes)

        $networkBytes = @()
        for ($i = 0; $i -lt 4; $i++) {
            $networkBytes += ($ipBytes[$i] -band $maskBytes[$i])
        }
        $networkAddr = ($networkBytes -join ".")

        $detectedSubnet = "$networkAddr/$prefix"
        $detectedIP = $ip
        Write-OK "Found: $iface — $ip (subnet: $detectedSubnet)"
        break
    }

    if (-not $detectedSubnet) {
        $detectedSubnet = "192.168.1.0/24"
        Write-Warn "Could not auto-detect subnet. Using default: $detectedSubnet"
    }

    # Let user confirm or override
    Write-Host ""
    $userSubnet = Read-Host "   Scan this subnet? [$detectedSubnet] (press Enter to accept, or type a different one)"
    if ($userSubnet) { $detectedSubnet = $userSubnet }

    Write-OK "Will scan: $detectedSubnet"
}

# ===========================================================================
# STEP 3: Configure .env
# ===========================================================================
if (-not $RunOnly) {
    Write-Step "Configuring environment..."

    if (Test-Path .env) {
        $overwrite = Read-Host "   .env already exists. Overwrite? (y/n) [n]"
        if ($overwrite -ne "y") {
            Write-OK "Keeping existing .env"
            # Still read the subnet from existing .env for display later
            $detectedSubnet = (Select-String -Path .env -Pattern "^SCAN_DEFAULT_RANGE=(.+)" |
                ForEach-Object { $_.Matches[0].Groups[1].Value }) ?? $detectedSubnet
        } else {
            Remove-Item .env
        }
    }

    if (-not (Test-Path .env)) {
        # Ask for Neo4j password
        $neo4jPass = Read-Host "   Neo4j password? [changeme] (press Enter for default)"
        if (-not $neo4jPass) { $neo4jPass = "changeme" }

        # Generate .env from template
        $envContent = @"
# =============================================================================
# NTS — Auto-generated by setup.ps1 on $(Get-Date -Format "yyyy-MM-dd HH:mm")
# =============================================================================

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=$neo4jPass

# Redis (optional — app works without it)
REDIS_URL=redis://localhost:6379/0

# SQLite
SQLITE_PATH=./data/mapper.db

# Network scanning
SCAN_DEFAULT_RANGE=$detectedSubnet
SCAN_RATE_LIMIT=500
SCAN_PASSIVE_INTERFACE=

# Scan phases
ENABLE_ACTIVE_SCAN=true
ENABLE_PASSIVE_SCAN=false
ENABLE_SNMP_SCAN=true

# SNMP
SNMP_COMMUNITY=public
SNMP_VERSION=2c

# SSH (leave blank unless you have managed network gear)
SSH_USERNAME=
SSH_PASSWORD=

# Claude API (optional)
ANTHROPIC_API_KEY=

# App
APP_HOST=127.0.0.1
APP_PORT=8000
LOG_LEVEL=INFO
AGENT_MODE=alert
WS_HEARTBEAT_INTERVAL=30
SCAN_INTERVAL_MINUTES=0
"@
        $envContent | Out-File -FilePath .env -Encoding UTF8 -NoNewline
        Write-OK ".env created (subnet: $detectedSubnet, neo4j pass: $neo4jPass)"
    }
}

# ===========================================================================
# STEP 4: Backend setup
# ===========================================================================
if (-not $RunOnly) {
    Write-Step "Setting up backend..."

    Set-Location backend

    if (-not (Test-Path .venv)) {
        Write-Host "   Creating Python virtual environment..."
        python -m venv .venv
    }

    # Activate venv
    & .venv\Scripts\Activate.ps1

    Write-Host "   Installing Python packages (this may take a minute)..."
    pip install -q -r requirements.txt 2>&1 | Out-Null

    if (-not (Test-Path data)) {
        New-Item -ItemType Directory -Path data | Out-Null
    }

    Write-OK "Backend ready"
    Set-Location $ScriptDir

    # --- Frontend setup ---
    Write-Step "Setting up frontend..."
    Set-Location frontend

    if (-not (Test-Path node_modules)) {
        Write-Host "   Installing Node packages (this may take a minute)..."
        npm install 2>&1 | Out-Null
    }

    Write-OK "Frontend ready"
    Set-Location $ScriptDir
}

# ===========================================================================
# STEP 5: Launch everything
# ===========================================================================
Write-Step "Launching NTS..."

# Check Neo4j one more time
if (Test-PortOpen -Port 7687) {
    Write-OK "Neo4j: running"
} else {
    Write-Warn "Neo4j is not running on port 7687!"
    Write-Host "   The app will start with mock data. To get real scan results," -ForegroundColor Yellow
    Write-Host "   open Neo4j Desktop and start your DBMS." -ForegroundColor Yellow
    Write-Host ""
}

# Start backend
Set-Location "$ScriptDir\backend"

if (-not (Test-Path .venv\Scripts\Activate.ps1)) {
    Write-Err "Backend venv not found. Run setup.ps1 without -RunOnly first."
    exit 1
}

& .venv\Scripts\Activate.ps1

Write-Host "   Starting backend..."
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:ScriptDir\backend
    & "$using:ScriptDir\backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 2>&1
}

# Wait for backend to be ready
Write-Host "   Waiting for backend..." -NoNewline
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    if (Test-PortOpen -Port 8000) {
        $ready = $true
        break
    }
    Write-Host "." -NoNewline
}
Write-Host ""

if ($ready) {
    Write-OK "Backend running on http://127.0.0.1:8000"
} else {
    Write-Warn "Backend may still be starting up..."
    # Check if the job failed
    $jobState = (Get-Job $backendJob.Id).State
    if ($jobState -eq "Failed") {
        Write-Err "Backend failed to start. Check the error:"
        Receive-Job $backendJob
        exit 1
    }
}

# Read subnet from .env for the scan hint
Set-Location $ScriptDir
$scanRange = "192.168.1.0/24"
if (Test-Path .env) {
    $match = Select-String -Path .env -Pattern "^SCAN_DEFAULT_RANGE=(.+)"
    if ($match) { $scanRange = $match.Matches[0].Groups[1].Value.Trim() }
}

# Open browser
Write-Host "   Opening browser..."
Start-Process "http://localhost:3000"

# Print instructions
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "   NTS is running!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "   Frontend:   http://localhost:3000" -ForegroundColor White
Write-Host "   Backend:    http://127.0.0.1:8000/api" -ForegroundColor White
Write-Host "   API Docs:   http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "   TO SCAN YOUR NETWORK:" -ForegroundColor Yellow
Write-Host "   Click 'Scan' in the sidebar, or run this in another terminal:" -ForegroundColor White
Write-Host ""
Write-Host "   curl -X POST http://127.0.0.1:8000/api/scans ``" -ForegroundColor DarkCyan
Write-Host "     -H 'Content-Type: application/json' ``" -ForegroundColor DarkCyan
Write-Host "     -d '{""type"":""active"",""target"":""$scanRange"",""intensity"":""normal""}'" -ForegroundColor DarkCyan
Write-Host ""
Write-Host "   Or in PowerShell:" -ForegroundColor White
Write-Host ""
Write-Host "   Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/scans ``" -ForegroundColor DarkCyan
Write-Host "     -ContentType 'application/json' ``" -ForegroundColor DarkCyan
Write-Host "     -Body '{""type"":""active"",""target"":""$scanRange"",""intensity"":""normal""}'" -ForegroundColor DarkCyan
Write-Host ""
Write-Host "   Press Ctrl+C to stop everything." -ForegroundColor Yellow
Write-Host ""

# Start frontend in foreground
Set-Location "$ScriptDir\frontend"
try {
    npm run dev
}
finally {
    Write-Host "`nShutting down..."
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -ErrorAction SilentlyContinue
    Set-Location $ScriptDir
    Write-Host "Done. See you next scan." -ForegroundColor Cyan
}
