# Installation Guide

> **Recommended:** Use Demo Mode for development — no manual installation required. Run `./demo.sh up` from `network-topology-mapper/`. This guide covers manual setup for local bare-metal development.

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- nmap (for active scanning)

Optional:
- Redis 7 (for WebSocket pub/sub — app falls back to in-memory if unavailable)

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
