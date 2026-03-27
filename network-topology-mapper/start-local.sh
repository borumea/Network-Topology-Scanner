#!/usr/bin/env bash
# =============================================================================
# NTS One-Click Setup — installs deps, detects network, launches everything.
# =============================================================================
# Usage:
#   ./start-local.sh           # Full setup + launch
#   ./start-local.sh --run     # Skip setup, just launch (for subsequent runs)
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

RUN_ONLY=false
if [ "$1" = "--run" ]; then RUN_ONLY=true; fi

step()  { echo -e "\n\033[36m>> $1\033[0m"; }
ok()    { echo -e "   \033[32m[OK]\033[0m $1"; }
warn()  { echo -e "   \033[33m[!!]\033[0m $1"; }
err()   { echo -e "   \033[31m[ERROR]\033[0m $1"; }

port_open() { (echo >/dev/tcp/localhost/$1) 2>/dev/null; }

echo ""
echo "============================================================"
echo "   NTS — Network Topology Scanner Setup"
echo "   One script. Real network scanning. No Docker."
echo "============================================================"
echo ""

# ===========================================================================
# STEP 1: Check / install prerequisites
# ===========================================================================
if [ "$RUN_ONLY" = false ]; then
    step "Checking prerequisites..."

    # Python
    PYTHON=""
    if command -v python3 &>/dev/null; then
        PYTHON="python3"
    elif command -v python &>/dev/null; then
        PYTHON="python"
    fi
    if [ -n "$PYTHON" ]; then
        ok "Python: $($PYTHON --version 2>&1)"
    else
        err "Python 3.11+ not found. Install from https://python.org"
        exit 1
    fi

    # Node
    if command -v node &>/dev/null; then
        ok "Node.js: $(node --version)"
    else
        err "Node.js not found. Install from https://nodejs.org"
        exit 1
    fi

    # nmap
    if command -v nmap &>/dev/null; then
        ok "nmap: installed"
    else
        warn "nmap not found — attempting install..."
        if command -v brew &>/dev/null; then
            brew install nmap && ok "nmap installed via Homebrew"
        elif command -v apt-get &>/dev/null; then
            sudo apt-get install -y nmap && ok "nmap installed via apt"
        elif command -v pacman &>/dev/null; then
            sudo pacman -S --noconfirm nmap && ok "nmap installed via pacman"
        else
            err "Could not auto-install nmap. Install manually:"
            echo "     https://nmap.org/download"
            exit 1
        fi
    fi

    # Neo4j
    if port_open 7687 2>/dev/null; then
        ok "Neo4j: running on port 7687"
    else
        echo ""
        warn "Neo4j is not running on port 7687."
        echo ""
        echo "   Options:"
        echo "   1. Install Neo4j Desktop: https://neo4j.com/download/"
        echo "      Create a local DBMS, set password to 'changeme', click Start."
        echo ""
        echo "   2. Or use Homebrew (macOS):  brew install neo4j && neo4j start"
        echo "   3. Or use Docker (just Neo4j): docker run -d -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/changeme neo4j:5-community"
        echo ""
        read -p "   Press Enter once Neo4j is running (or Enter to continue without it): "

        if port_open 7687 2>/dev/null; then
            ok "Neo4j is running!"
        else
            warn "Neo4j not detected. App will start with mock data (scans won't persist)."
        fi
    fi

    # ===========================================================================
    # STEP 2: Auto-detect network
    # ===========================================================================
    step "Detecting your network..."

    DETECTED_SUBNET=""
    if command -v ip &>/dev/null; then
        # Linux: use ip route
        DETECTED_SUBNET=$(ip route show default 2>/dev/null | awk '{print $3}' | head -1)
        if [ -n "$DETECTED_SUBNET" ]; then
            # Get the subnet of the default route interface
            DEF_IFACE=$(ip route show default 2>/dev/null | awk '{print $5}' | head -1)
            DETECTED_SUBNET=$(ip -4 addr show "$DEF_IFACE" 2>/dev/null | grep -oP 'inet \K[\d./]+' | head -1)
            # Convert host IP/prefix to network/prefix
            if [ -n "$DETECTED_SUBNET" ]; then
                ok "Found: $DEF_IFACE — $DETECTED_SUBNET"
            fi
        fi
    elif command -v ifconfig &>/dev/null; then
        # macOS: use ifconfig
        DEF_IFACE=$(route -n get default 2>/dev/null | grep interface | awk '{print $2}')
        if [ -n "$DEF_IFACE" ]; then
            IP_ADDR=$(ifconfig "$DEF_IFACE" 2>/dev/null | grep 'inet ' | awk '{print $2}')
            NETMASK=$(ifconfig "$DEF_IFACE" 2>/dev/null | grep 'inet ' | awk '{print $4}')
            if [ -n "$IP_ADDR" ]; then
                # Rough CIDR: assume /24 for most home networks
                NETWORK=$(echo "$IP_ADDR" | sed 's/\.[0-9]*$/.0/')
                DETECTED_SUBNET="${NETWORK}/24"
                ok "Found: $DEF_IFACE — $IP_ADDR (subnet: $DETECTED_SUBNET)"
            fi
        fi
    fi

    if [ -z "$DETECTED_SUBNET" ]; then
        DETECTED_SUBNET="192.168.1.0/24"
        warn "Could not auto-detect. Using default: $DETECTED_SUBNET"
    fi

    echo ""
    read -p "   Scan this subnet? [$DETECTED_SUBNET] (Enter to accept, or type a different one): " USER_SUBNET
    if [ -n "$USER_SUBNET" ]; then DETECTED_SUBNET="$USER_SUBNET"; fi
    ok "Will scan: $DETECTED_SUBNET"

    # ===========================================================================
    # STEP 3: Configure .env
    # ===========================================================================
    step "Configuring environment..."

    if [ -f .env ]; then
        read -p "   .env already exists. Overwrite? (y/n) [n]: " OVERWRITE
        if [ "$OVERWRITE" != "y" ]; then
            ok "Keeping existing .env"
        else
            rm .env
        fi
    fi

    if [ ! -f .env ]; then
        read -p "   Neo4j password? [changeme]: " NEO4J_PASS
        NEO4J_PASS="${NEO4J_PASS:-changeme}"

        cat > .env << ENVEOF
# Auto-generated by start-local.sh on $(date "+%Y-%m-%d %H:%M")

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=$NEO4J_PASS
REDIS_URL=redis://localhost:6379/0
SQLITE_PATH=./data/mapper.db
SCAN_DEFAULT_RANGE=$DETECTED_SUBNET
SCAN_RATE_LIMIT=500
SCAN_PASSIVE_INTERFACE=
ENABLE_ACTIVE_SCAN=true
ENABLE_PASSIVE_SCAN=false
ENABLE_SNMP_SCAN=true
SNMP_COMMUNITY=public
SNMP_VERSION=2c
SSH_USERNAME=
SSH_PASSWORD=
ANTHROPIC_API_KEY=
APP_HOST=127.0.0.1
APP_PORT=8000
LOG_LEVEL=INFO
AGENT_MODE=alert
WS_HEARTBEAT_INTERVAL=30
SCAN_INTERVAL_MINUTES=0
ENVEOF
        ok ".env created (subnet: $DETECTED_SUBNET)"
    fi

    # ===========================================================================
    # STEP 4: Install dependencies
    # ===========================================================================
    step "Setting up backend..."
    cd backend

    if [ ! -d .venv ]; then
        $PYTHON -m venv .venv
    fi

    if [ -f .venv/Scripts/activate ]; then
        source .venv/Scripts/activate
    else
        source .venv/bin/activate
    fi

    echo "   Installing Python packages..."
    pip install -q -r requirements.txt
    mkdir -p data
    ok "Backend ready"

    cd "$SCRIPT_DIR"

    step "Setting up frontend..."
    cd frontend
    if [ ! -d node_modules ]; then
        echo "   Installing Node packages..."
        npm install --silent 2>&1
    fi
    ok "Frontend ready"
    cd "$SCRIPT_DIR"
fi

# ===========================================================================
# STEP 5: Launch
# ===========================================================================
step "Launching NTS..."

# Activate venv
cd backend
if [ -f .venv/Scripts/activate ]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

# Neo4j check
if port_open 7687 2>/dev/null; then
    ok "Neo4j: running"
else
    warn "Neo4j not running — app will use mock data"
fi

echo "   Starting backend..."
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Wait for backend
printf "   Waiting for backend"
for i in $(seq 1 30); do
    sleep 1
    if port_open 8000 2>/dev/null; then break; fi
    printf "."
done
echo ""
if port_open 8000 2>/dev/null; then
    ok "Backend running on http://127.0.0.1:8000"
else
    warn "Backend may still be starting..."
fi

cd "$SCRIPT_DIR"

# Read subnet from .env
SCAN_RANGE=$(grep "^SCAN_DEFAULT_RANGE=" .env 2>/dev/null | cut -d= -f2)
SCAN_RANGE="${SCAN_RANGE:-192.168.1.0/24}"

# Open browser (best-effort)
if command -v open &>/dev/null; then
    open "http://localhost:3000" 2>/dev/null &
elif command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:3000" 2>/dev/null &
elif command -v start &>/dev/null; then
    start "http://localhost:3000" 2>/dev/null &
fi

echo ""
echo "============================================================"
echo "   NTS is running!"
echo "============================================================"
echo ""
echo "   Frontend:   http://localhost:3000"
echo "   Backend:    http://127.0.0.1:8000/api"
echo "   API Docs:   http://127.0.0.1:8000/docs"
echo ""
echo "   TO SCAN YOUR NETWORK:"
echo "   Click 'Scan' in the sidebar, or run in another terminal:"
echo ""
echo "   curl -X POST http://127.0.0.1:8000/api/scans \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"type\":\"active\",\"target\":\"$SCAN_RANGE\",\"intensity\":\"normal\"}'"
echo ""
echo "   Press Ctrl+C to stop."
echo ""

cleanup() {
    echo ""
    echo "Shutting down..."
    kill $BACKEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    echo "Done. See you next scan."
    exit 0
}
trap cleanup SIGINT SIGTERM

cd "$SCRIPT_DIR/frontend"
npm run dev
