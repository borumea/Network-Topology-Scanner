# Installation Guide

> **Recommended:** Use Demo Mode for development — no manual installation required. Run `./demo.sh up` from `network-topology-mapper/`. This guide covers manual setup for local bare-metal development.

---

## Prerequisites

### All Platforms
- Python 3.11+
- Node.js 18+
- nmap (for active scanning)

Optional:
- Redis 7 (for WebSocket pub/sub — app falls back to in-memory if unavailable)

### Linux Additional Requirements

**Ubuntu/Debian:**
```bash
# Core dependencies
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip nmap

# For Scapy packet capture
sudo apt install -y libpcap-dev python3-dev build-essential

# Optional: Redis
sudo apt install -y redis-server
sudo systemctl enable --now redis-server
```

**Fedora/RHEL:**
```bash
sudo dnf install -y python3.11 nmap libpcap-devel gcc python3-devel redis
```

**Arch Linux:**
```bash
sudo pacman -S python nmap libpcap redis
```

### Network Scanning Privileges (Linux)

Network scanning requires elevated privileges. Choose one option:

**Option A: Linux Capabilities (Recommended)**
```bash
# Grant capabilities to nmap and python
sudo setcap cap_net_raw,cap_net_admin=eip $(which nmap)
sudo setcap cap_net_raw,cap_net_admin=eip $(which python3.11)
```

**Option B: Run as Root (Not Recommended)**
```bash
sudo uvicorn app.main:app --reload --port 8000
```

**Option C: Use Unprivileged Mode**
No setup required — NTS auto-detects and falls back to TCP connect scans. Slower but works without elevated privileges.

### Install Redis (Optional)

**macOS:**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt install redis-server
sudo systemctl start redis && sudo systemctl enable redis
```

**Verify:**
```bash
redis-cli ping   # Should return: PONG
```

---

## Configure the Backend

```bash
cd network-topology-mapper/backend
cp ../.env.example ../.env
```

Edit `.env`:
```bash
REDIS_URL=redis://localhost:6379/0
SQLITE_PATH=./data/mapper.db
SCAN_DEFAULT_RANGE=192.168.1.0/24
```

---

## Start the Backend

```bash
cd network-topology-mapper/backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at http://localhost:8000

On startup, look for:
```
[INFO] TopologyDB connected to data/mapper.db
[INFO] Connected to Redis at localhost:6379
[INFO] SQLite initialized at data/mapper.db
```

---

## Verify

```bash
curl http://localhost:8000/api/health
# {"status": "ok"}

curl http://localhost:8000/api/topology/stats
# {"total_devices": 0, ...}
```

---

## Troubleshooting

**Redis connection refused:**
- macOS: `brew services start redis`
- Linux: `sudo systemctl start redis`
- Verify: `redis-cli ping`
- The app works without Redis (in-memory fallback), but WebSocket pub/sub won't function across multiple workers.

**Permission denied on nmap:**
- macOS (Homebrew): nmap runs with required capabilities by default
- Linux: `sudo setcap cap_net_raw,cap_net_admin=eip $(which nmap)`
