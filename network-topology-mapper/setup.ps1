<#
.SYNOPSIS
    NTS One-Click Setup for Windows.

.DESCRIPTION
    Installs missing tools, detects your network, configures .env, and launches NTS.

.EXAMPLE
    .\setup.ps1              # Full setup + launch
    .\setup.ps1 -SkipInstall # Skip winget installs
    .\setup.ps1 -RunOnly     # Skip all setup, just launch
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
    param([int]$Port)
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect("localhost", $Port)
        $tcp.Close()
        return $true
    } catch {
        return $false
    }
}

# ===========================================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   NTS -- Network Topology Scanner Setup" -ForegroundColor Cyan
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
        Write-Host '         Make sure to check "Add Python to PATH" during install.' -ForegroundColor Yellow
        Read-Host "Press Enter after installing Python then re-run this script"
        exit 1
    }

    # --- Node.js ---
    if (Get-Command node -ErrorAction SilentlyContinue) {
        $nodeVer = node --version
        Write-OK "Node.js: $nodeVer"
    } else {
        Write-Err "Node.js not found. Install from https://nodejs.org (LTS recommended)"
        Read-Host "Press Enter after installing Node.js then re-run this script"
        exit 1
    }

    # --- nmap ---
    if (Get-Command nmap -ErrorAction SilentlyContinue) {
        Write-OK "nmap: installed"
    } else {
        Write-Warn "nmap not found -- installing via winget..."
        try {
            winget install --id Insecure.Nmap --accept-package-agreements --accept-source-agreements
            $nmapPath = "C:\Program Files (x86)\Nmap"
            if (Test-Path $nmapPath) {
                $env:PATH += ";$nmapPath"
            }
            Write-OK "nmap installed. You may need to restart your terminal for PATH to update."
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
        $hasNeo4jCmd = [bool](Get-Command neo4j -ErrorAction SilentlyContinue)
        $hasNeo4jLocal = Test-Path "$env:LOCALAPPDATA\Neo4j Desktop"
        $hasNeo4jProgs = Test-Path "$env:LOCALAPPDATA\Programs\Neo4j Desktop"
        $neo4jInstalled = $hasNeo4jCmd -or $hasNeo4jLocal -or $hasNeo4jProgs

        if (-not $neo4jInstalled) {
            Write-Warn "Neo4j Desktop not found -- installing via winget..."
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
        Write-Host '   NEO4J SETUP (one-time -- takes 2 minutes):' -ForegroundColor Yellow
        Write-Host "   ============================================================" -ForegroundColor Yellow
        Write-Host "   1. Open Neo4j Desktop" -ForegroundColor White
        Write-Host '   2. Click "New" then "Create project"' -ForegroundColor White
        Write-Host '   3. Click "Add" then "Local DBMS"' -ForegroundColor White
        Write-Host "   4. Set the password to: changeme" -ForegroundColor White
        Write-Host '      (or whatever you want -- you will enter it below)' -ForegroundColor DarkGray
        Write-Host '   5. Click "Create"' -ForegroundColor White
        Write-Host '   6. Click "Start" on the DBMS' -ForegroundColor White
        Write-Host '   7. Wait until it says "Started" with a green dot' -ForegroundColor White
        Write-Host "   ============================================================" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter once Neo4j is running"

        if (-not (Test-PortOpen -Port 7687)) {
            Write-Err "Neo4j is not responding on port 7687. Make sure the DBMS is started."
            $cont = Read-Host "Continue anyway? (y/n)"
            if ($cont -ne "y") { exit 1 }
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

    $adapters = Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object {
            $_.IPAddress -ne "127.0.0.1" -and
            -not $_.IPAddress.StartsWith("169.254") -and
            $_.PrefixOrigin -ne "WellKnown"
        } |
        Sort-Object -Property { if ($_.InterfaceAlias -match "Wi-Fi|Ethernet") { 0 } else { 1 } }

    $detectedSubnet = $null
    $detectedIP = $null

    foreach ($adapter in $adapters) {
        $ip = $adapter.IPAddress
        $prefix = $adapter.PrefixLength
        $iface = $adapter.InterfaceAlias

        # Skip VPN/tunnel ranges
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
        Write-OK "Found: $iface -- $ip (subnet: $detectedSubnet)"
        break
    }

    if (-not $detectedSubnet) {
        $detectedSubnet = "192.168.1.0/24"
        Write-Warn "Could not auto-detect subnet. Using default: $detectedSubnet"
    }

    Write-Host ""
    $userSubnet = Read-Host "   Scan this subnet? [$detectedSubnet] (Enter to accept or type a different one)"
    if ($userSubnet) { $detectedSubnet = $userSubnet }

    Write-OK "Will scan: $detectedSubnet"
}

# ===========================================================================
# STEP 3: Configure .env
# ===========================================================================
if (-not $RunOnly) {
    Write-Step "Configuring environment..."

    $skipEnvWrite = $false
    if (Test-Path .env) {
        $overwrite = Read-Host "   .env already exists. Overwrite? (y/n) [n]"
        if ($overwrite -ne "y") {
            Write-OK "Keeping existing .env"
            $skipEnvWrite = $true
            # Read subnet from existing .env
            $envMatch = Select-String -Path .env -Pattern "^SCAN_DEFAULT_RANGE=(.+)"
            if ($envMatch) {
                $detectedSubnet = $envMatch.Matches[0].Groups[1].Value.Trim()
            }
        } else {
            Remove-Item .env
        }
    }

    if (-not $skipEnvWrite -and -not (Test-Path .env)) {
        $neo4jPass = Read-Host "   Neo4j password? [changeme] (Enter for default)"
        if (-not $neo4jPass) { $neo4jPass = "changeme" }

        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
        $envLines = @(
            "# Auto-generated by setup.ps1 on $timestamp"
            ""
            "NEO4J_URI=bolt://localhost:7687"
            "NEO4J_USER=neo4j"
            "NEO4J_PASSWORD=$neo4jPass"
            ""
            "REDIS_URL=redis://localhost:6379/0"
            "SQLITE_PATH=./data/mapper.db"
            ""
            "SCAN_DEFAULT_RANGE=$detectedSubnet"
            "SCAN_RATE_LIMIT=500"
            "SCAN_PASSIVE_INTERFACE="
            ""
            "ENABLE_ACTIVE_SCAN=true"
            "ENABLE_PASSIVE_SCAN=false"
            "ENABLE_SNMP_SCAN=true"
            ""
            "SNMP_COMMUNITY=public"
            "SNMP_VERSION=2c"
            ""
            "SSH_USERNAME="
            "SSH_PASSWORD="
            ""
            "ANTHROPIC_API_KEY="
            ""
            "APP_HOST=127.0.0.1"
            "APP_PORT=8000"
            "LOG_LEVEL=INFO"
            "AGENT_MODE=alert"
            "WS_HEARTBEAT_INTERVAL=30"
            "SCAN_INTERVAL_MINUTES=0"
        )
        $envLines -join "`n" | Out-File -FilePath .env -Encoding UTF8 -NoNewline
        Write-OK ".env created -- subnet: $detectedSubnet"
    }
}

# ===========================================================================
# STEP 4: Backend setup
# ===========================================================================
if (-not $RunOnly) {
    Write-Step "Setting up backend..."

    Set-Location "$ScriptDir\backend"

    if (-not (Test-Path .venv)) {
        Write-Host "   Creating Python virtual environment..."
        python -m venv .venv
    }

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
    Set-Location "$ScriptDir\frontend"

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
    Write-Host "   The app will start with mock data. To get real scan results" -ForegroundColor Yellow
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
    Set-Location "$using:ScriptDir\backend"
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
    $jobState = (Get-Job $backendJob.Id).State
    if ($jobState -eq "Failed") {
        Write-Err "Backend failed to start:"
        Receive-Job $backendJob
        exit 1
    }
}

# Read subnet from .env for the scan hint
Set-Location $ScriptDir
$scanRange = "192.168.1.0/24"
if (Test-Path .env) {
    $m = Select-String -Path .env -Pattern "^SCAN_DEFAULT_RANGE=(.+)"
    if ($m) { $scanRange = $m.Matches[0].Groups[1].Value.Trim() }
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
Write-Host "   Open a second terminal and run:" -ForegroundColor White
Write-Host ""
$scanCmd = 'Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/scans -ContentType "application/json" -Body ''{"type":"active","target":"' + $scanRange + '","intensity":"normal"}'''
Write-Host "   $scanCmd" -ForegroundColor DarkCyan
Write-Host ""
Write-Host "   Or just click Scan in the sidebar!" -ForegroundColor White
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
    Write-Host "Done." -ForegroundColor Cyan
}
